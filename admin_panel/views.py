import os
import datetime
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from groq import Groq
from .models import MenuDiario, Plato, MenuPlato
from authentication.models import Restaurante
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from django.conf import settings
from dotenv import load_dotenv
import re
from decimal import Decimal
from datetime import datetime


load_dotenv()

# Configuración de Azure Document Intelligence
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
AZURE_KEY = os.getenv("AZURE_KEY")

# Configuración de Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

#Configuración de Azure Blob Storage
AZURE_CONNECTION_STRING = os.getenv("AZURE_CONNECTION_STRING")
AZURE_CONTAINER_NAME = os.getenv("AZURE_CONTAINER_NAME") 

# Extraer texto de PDF usando Azure Document Intelligence
def extract_text_from_pdf(url):
    # Inicializar el cliente de Azure
    document_intelligence_client = DocumentIntelligenceClient(
        endpoint=AZURE_ENDPOINT, credential=AzureKeyCredential(AZURE_KEY)
    )

    # Enviar la solicitud para analizar el documento
    poller = document_intelligence_client.begin_analyze_document(
        "prebuilt-read", AnalyzeDocumentRequest(url_source=url)
    )

    # Obtener el resultado
    result = poller.result()

    return result.content  # Devolver el texto extraído

# Llamada a la API de Groq para procesar el texto y estructurarlo en JSON
def process_text_with_groq(text):
    client = Groq(api_key=GROQ_API_KEY)
    
    prompt = f'''
    You are an AI assistant that extracts structured data from text.
    You will act with the following conditions:
    The date of today is: {datetime.today().strftime('%Y-%m-%d')}, and the weekday is: {datetime.now().strftime('%A')} The dates must be in the format yyyy-mm-dd. 
    If there is a weekday date, you must adjust the date to the nearest day from today (for example, is there is "Lunes" or "Monday", the date must be 2025-03-3).
    If in the same text appears more than one menu, you must asign 'fecha_final' to a day before the next inital date menu, with the objetive to have it coordinated in the timelap.
    If there is only 1 menu, you must asign 'fecha_final' to a week after the starting date of the menu.
    If there is no specified date, asign the 'fecha_inicio' for the date of today and 'fecha_final' to a week after today.
    The info of 'tipo' must be only one of this three possibilities: <"primero"|"segundo"|"postre">
    All the info of 'platos' must be a food dish, if it is not, let the field empty
    All the info that comes you is in spanish
    ###
    Your task is to read a given text containing daily menus and output a JSON structure following this format:
    {{"menus": [{{"precio": <menu price>, "fecha_inicio": <initial_date>, "fecha_final": <final_date>, "platos": [{{"nombre": <dish name>, "descripcion": <dish description, if available>, "tipo": <"primero"|"segundo"|"postre">}}]}}]}}
    
    Now process the following text:
    \"\"\"{text}\"\"\"
    '''

    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama3-8b-8192",
    )

    json_match = re.search(r'{.*}', response.choices[0].message.content, re.DOTALL)

    if json_match:
        # Convertir la cadena JSON a un diccionario
        json_data = json.loads(json_match.group(0))
        # Mostrar los datos JSON
        return json_data
    else:
        print("No se encontró JSON en la respuesta.")
        return None

# Endpoint para subir PDF y procesarlo
@csrf_exempt
def upload_pdf(request):
    if request.method == "POST":
        pdf_file = request.FILES.get("file")
        if not pdf_file:
            return JsonResponse({"error": "No file uploaded"}, status=400)

        # Subir el archivo a Azure Blob Storage
        blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
        container_client = blob_service_client.get_container_client(AZURE_CONTAINER_NAME)

        # Nombre único para el archivo en Azure Blob
        blob_name = f"uploads/{pdf_file.name}"
        blob_client = container_client.get_blob_client(blob_name)

        # Subir el archivo
        blob_client.upload_blob(pdf_file, overwrite=True)

        # Obtener la URL del archivo subido
        file_url = blob_client.url

        # Extraer texto del PDF desde la URL de Azure Blob Storage
        text = extract_text_from_pdf(file_url)

        # Procesar con Groq
        structured_data = process_text_with_groq(text)

        restaurante= Restaurante.objects.get(id=4)

        # Guardar en la base de datos
        for menu_data in structured_data["menus"]:
            print(menu_data)
            menu = MenuDiario.objects.create(
                fecha_inicio=convertir_fecha(menu_data.get("fecha_inicio")),
                fecha_final=convertir_fecha(menu_data.get("fecha_final")),
                precio=convertir_precio(menu_data.get("precio", "0")),
                id_restaurante = restaurante
            )
            for plato_data in menu_data.get("platos", []):
                plato = Plato.objects.create(
                    nombre=plato_data.get("nombre"),
                    descripcion=plato_data.get("descripcion"),
                    precio = 0,
                    tipo=plato_data.get("tipo"),
                )
                
                MenuPlato.objects.create(
                    id_plato = plato,
                    id_menu = menu
                )

        return JsonResponse({"message": "File processed successfully"})
    
    return JsonResponse({"error": "Invalid request"}, status=400)

def convertir_precio(precio_str):

    if isinstance(precio_str, str):
        precio_str = precio_str.replace('€', '').strip()
        print(precio_str)
    
    # Convertir a decimal
    try:
        return Decimal(precio_str)
    except Exception as e:
        print(f"Error al convertir el precio: {e}")
        return Decimal(0)  # Devolvemos un valor por defecto (0)
    
def convertir_fecha(fecha):
    try:
        fecha_convertida = datetime.strptime(fecha, "%d/%m/%y").date()
        return fecha_convertida
    except ValueError:
        fecha_actual = datetime.today().strftime("%d%m%y")
        return datetime.strptime(fecha_actual, "%d%m%y").date()

def upload_pdf_page(request):
    return render(request, "upload_pdf.html")
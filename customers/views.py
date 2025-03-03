# views.py
from django.shortcuts import render, get_object_or_404
from .models import Plato, Restaurante, ValoracionRestaurante, ValoracionPlato, Reserva, PlatoReserva
from authentication.models import Usuario
from admin_panel.models import MenuDiario, MenuPlato
from datetime import date
from datetime import date
from django.db.models import Avg
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
import os
from dotenv import load_dotenv
import re
from groq import Groq
from datetime import datetime

load_dotenv()

def customer_view(request):
    hoy = date.today()
    menus_hoy = MenuDiario.objects.filter(fecha_inicio__lte=hoy, fecha_final__gte=hoy)
    for menu in menus_hoy:
        menu.id_restaurante.media_valoraciones = ValoracionRestaurante.objects.filter(id_restaurante=menu.id_restaurante).aggregate(Avg('puntuacion'))['puntuacion__avg'] or 0
    return render(request, 'customer.html', {'menus': menus_hoy})

def restaurant_view(request, menu_id):
    menu = MenuDiario.objects.get(id=menu_id)
    platos = MenuPlato.objects.filter(id_menu=menu_id)
    primeros = [p.id_plato for p in platos if p.id_plato.tipo.lower() == 'primero']
    segundos = [p.id_plato for p in platos if p.id_plato.tipo.lower() == 'segundo']
    postres = [p.id_plato for p in platos if p.id_plato.tipo.lower() == 'postre']
    return render(request, 'restaurant.html', {'menu': menu, 'primeros': primeros, 'segundos': segundos, 'postres': postres})

@csrf_exempt
def enviar_valoracion_restaurante(request):
    if request.method == "POST":
        data = json.loads(request.body)

        restaurante_id = data.get("restaurante_id")
        id_usuario = int(request.session.get("user_id"))
        puntuacion = data.get("puntuacion")
        comentario = data.get("comentario")
        
        if not (1 <= puntuacion <= 5):
            return JsonResponse({"error": "Puntuación fuera de rango"}, status=400)
        
        valoracion = ValoracionRestaurante.objects.create(
            id_restaurante_id=restaurante_id,
            id_usuario_id=id_usuario,
            puntuacion=puntuacion,
            comentario=comentario,
            fecha=date.today()
        )
        
        return JsonResponse({"message": "Valoración enviada correctamente"}, status=201)
    
    return JsonResponse({"error": "Método no permitido"}, status=405)

@csrf_exempt
def enviar_valoracion_plato(request):
    if request.method == "POST":
        data = json.loads(request.body)
        plato_id = data.get("plato_id")
        usuario_id = int(request.session.get("user_id"))  # Suponiendo que el usuario está autenticado
        puntuacion = data.get("puntuacion")
        comentario = data.get("comentario")
        
        if not (1 <= puntuacion <= 5):
            return JsonResponse({"error": "Puntuación fuera de rango"}, status=400)
        
        valoracion = ValoracionPlato.objects.create(
            id_plato_id=plato_id,
            id_usuario_id=usuario_id,
            puntuacion=puntuacion,
            comentario=comentario,
            fecha=date.today()
        )
        
        return JsonResponse({"message": "Valoración enviada correctamente"}, status=201)
    
    return JsonResponse({"error": "Método no permitido"}, status=405)


@csrf_exempt
def reservar(request):
    if request.method == "POST":
        data = json.loads(request.body)
        platos = data.get("platos")
        usuario_id = int(request.session.get("user_id"))  # Suponiendo que el usuario está autenticado
        restaurante_id = data.get("restaurante_id") 
        
        reserva = Reserva.objects.create(
            id_cliente_id=usuario_id,
            id_restaurante_id=restaurante_id,
            fecha=date.today()
        )
        
        for plato in platos:
            if platos[plato] is not None:
                PlatoReserva.objects.create(
                    id_plato_id = platos[plato],
                    id_reserva = reserva
                )
        
        return JsonResponse({"message": "Valoración enviada correctamente"}, status=201)
    
    return JsonResponse({"error": "Método no permitido"}, status=405)

@csrf_exempt
def search_restaurants(request):
    search_endpoint = os.getenv('SEARCH_SERVICE_ENDPOINT')
    search_key = os.getenv('SEARCH_SERVICE_QUERY_KEY')
    search_index = os.getenv('SEARCH_INDEX_NAME')

    client = SearchIndexClient(endpoint=search_endpoint, credential=AzureKeyCredential(search_key))

    # Obtener el índice
    index = client.get_index(search_index)

    indexes=""
    # Imprimir los campos
    for field in index.fields:
        indexes+=f"{field.name}, "
    
    # Obtener parámetros de búsqueda del request
    query = request.POST.get("query", "")
    query_formated = process_text_with_groq(text= query, indexes=indexes)

    if query_formated:
        print(query_formated)
        text = query_formated.get("text", "")
        filter = query_formated.get("filter", "")
        order_by = query_formated.get("order_by", "")
        
        # Crear cliente de búsqueda
        search_client = SearchClient(endpoint=search_endpoint, index_name=search_index, credential=AzureKeyCredential(search_key))
        
        # Realizar la búsqueda
        results = search_client.search(
            search_text=text,
            filter=filter,
            order_by=order_by,
            include_total_count=True,
            select=["menu_id"]
        )
        
        menus = [] 

        if results.get_count() > 0:

            for result in results:
                menu_id = result["menu_id"]
                if menu_id not in menus:  # Evitar duplicados
                    menus.append(menu_id)
            
            # Lista para almacenar el menú de cada restaurante
            menus_filtrados = []
            
            # Obtener el menú de hoy para cada restaurante
            for id_menu in menus:
                try:
                    # Obtener el único menú para este restaurante y esta fecha
                    menu = MenuDiario.objects.get(id=id_menu)
                    menu.id_restaurante.media_valoraciones = ValoracionRestaurante.objects.filter(id_restaurante=menu.id_restaurante).aggregate(Avg('puntuacion'))['puntuacion__avg'] or 0
                    menus_filtrados.append(menu)
                except MenuDiario.DoesNotExist:
                    continue
            
            # Renderizar el template con los menús encontrados
            return render(request, 'customer.html', {'menus': menus_filtrados})
        else:
            return render(request, 'customer.html', {'error': '😢 Lo sentimos, no hemos encontrado nada con tu búsqueda.'})

    else:
        return render(request, 'customer.html', {'error': 'Por favor, ingrese un término de búsqueda.'})
def process_text_with_groq(text, indexes):
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

    client = Groq(api_key=GROQ_API_KEY)
    
    prompt = f"""
You are an assistant that converts natural language queries into OData queries for Azure AI Search. Your task is to return a response in JSON format with the following structure:
{{
"text": "<search text>",
"filter": "<some filter>",
"order_by": "<ordering field>"
}}

You will be provided with the fields of an Azure AI Search index in a variable called indexes, which will help you understand how to construct the queries.
For you, it is important to know that it is a searcher of menus in restaurants
You must interpret the natural language input in Spanish and return an OData query in the specified format.
Here is an example:\n
**User**: "Mejores lentejas en Madrid"
**System**:\n
{{
    "text": "lentejas",
    "filter": "ciudad eq 'Madrid'",
    "order_by": "plato_puntuacion"
}}
## Guidelines:
- text: This text must be information of food names, food description or type of restaurant. If there is nothing of that parameters specified, fill it with "*". 
- filter: This should include any relevant filter conditions, such as location or category. If there is nothing, let it empty
- order_by: This should specify how to order the results (e.g., by a rating or score).If there is nothing, let it empty
Please use the provided indexes variable to understand the available fields and determine how to construct the query.
Indexes: {indexes}
## How to use indexes:
- You must difference between 'ciudad' (city) (e.g. Madrid, Barcelona) and 'ubicacion' (location) that are streets (e.g. Calle Badalona, 15)
-This indexes will contain the field names and types of the Azure AI Search index. Use it as base of parametrizing
-You should map the Spanish query to the relevant fields in the index and apply filters accordingly (e.g., "ciudad" for location or "plato_puntuacion" for rating of dishes, but for restaurants should be restaurante_puntuacion).
-You can also infer ordering fields from the index (e.g., if there is a field like plato_puntuacion, you should use it in order_by to sort by score or rating)
- The field, "restaurante_tipo" its only the type of food that the restaurant serve
-Also, use "desc" and "asc" for order_by as well as it is required, based on the query user
Now, your task is to respond in the following format when the user submits a query:

###Text: {text}
"""

    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama3-8b-8192",
    )

    json_match = re.search(r'{.*}', response.choices[0].message.content, re.DOTALL)

    if json_match:
        # Convertir la cadena JSON a un diccionario
        json_data = json.loads(json_match.group(0))
        return json_data
    else:
        print("No se encontró JSON en la respuesta.")
        return None
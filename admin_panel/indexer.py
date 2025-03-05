import requests
from dotenv import load_dotenv
import os

load_dotenv()

# Configuración de Azure AI Search
ENDPOINT = os.getenv('SEARCH_SERVICE_ENDPOINT')  
INDEXER_NAME =  "restaurantes-indexer"
API_KEY =  os.getenv('SEARCH_SERVICE_QUERY_KEY')

# Encabezados para autenticación
HEADERS = {
    "Content-Type": "application/json",
    "api-key": API_KEY
}

# 1️⃣ **Reiniciar el indexador**
def reset_indexer():
    reset_url = f"{ENDPOINT}/indexers/{INDEXER_NAME}/reset?api-version=2020-06-30"
    try:
        response_reset = requests.post(reset_url, headers=HEADERS)
        print(response_reset.status_code)
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")

    if response_reset.status_code == 204:
        run_url = f"{ENDPOINT}/indexers/{INDEXER_NAME}/run?api-version=2020-06-30"
        try:
            response_run = requests.post(run_url, headers=HEADERS)
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de conexión: {e}")
        
        print(response_run.status_code)
        if response_run.status_code == 202:
            return True

    return False

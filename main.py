import os, json, time, requests
from apify_client import ApifyClient
import google.generativeai as genai

# Clase simple para hablar con Supabase usando solo 'requests'
class SupabaseClient:
    def __init__(self, url, key):
        self.url = f"{url}/rest/v1"
        self.headers = {"apikey": key, "Content-Type": "application/json"}

    def from_(self, table):
        self.table = table
        return self

    def select(self, columns):
        self.params = {"select": columns}
        return self

    def eq(self, column, value):
        self.params[column] = f"eq.{value}"
        return self

    def limit(self, count):
        self.params["limit"] = str(count)
        return self

    def insert(self, data):
        response = requests.post(f"{self.url}/{self.table}", headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

    def update(self, data):
        self.update_data = data
        return self

    def execute(self):
        response = requests.get(f"{self.url}/{self.table}", headers=self.headers, params=self.params)
        response.raise_for_status()
        return {"data": response.json(), "count": len(response.json())}

def inicializar_servicios():
    supabase = SupabaseClient(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))
    # ... (el resto de inicializaciones) ...
    apify_client = ApifyClient(os.environ.get("APIFY_KEY"))
    genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
    model_ia = genai.GenerativeModel('gemini-1.5-flash')
    print("✅ Conexiones a Supabase (vía Requests), Apify y Google IA establecidas.")
    return supabase, apify_client, model_ia

# ... (El resto del código del Cazador es el mismo, pero usando la nueva clase 'SupabaseClient') ...

def main():
    # ...
    response = supabase.from_("campanas").select("*").eq('estado_campana', 'cazando').limit(1).execute()
    # ...
    supabase.from_("prospectos").insert(prospecto_data)
    # ...
    supabase.from_("campanas").update({'estado_campana': 'analizando'}).eq('id', campana['id']).execute()
    # ...

# ... (bucle while) ...

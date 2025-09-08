import os, json, time
from postgrest import PostgrestClient
from apify_client import ApifyClient
import google.generativeai as genai

def inicializar_servicios():
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    supabase = PostgrestClient(base_url=supabase_url, headers={"apikey": supabase_key})

    apify_key = os.environ.get("APIFY_KEY")
    apify_client = ApifyClient(apify_key)

    google_api_key = os.environ.get("GOOGLE_API_KEY")
    genai.configure(api_key=google_api_key)
    model_ia = genai.GenerativeModel('gemini-1.5-flash')
    
    print("✅ Conexiones a Supabase (vía Postgrest), Apify y Google IA establecidas.")
    return supabase, apify_client, model_ia

def generar_plan_de_caza(model_ia, que_vendes, cliente_ideal, ubicacion):
    print("\n🧠 Fase Estratégica: La IA está pensando...")
    prompt = f'Actúa como un estratega de marketing. Para un cliente que vende "{que_vendes}" y busca "{cliente_ideal}" en "{ubicacion}", crea un plan de caza en formato JSON con una lista de 5 a 10 términos de búsqueda específicos para Google Maps. Genera solo el JSON con la clave "plan_de_busqueda".'
    try:
        response = model_ia.generate_content(prompt)
        json_text = response.text.strip().replace('```json', '').replace('```', '')
        plan = json.loads(json_text)
        print("✅ Plan de Caza generado por la IA.")
        return plan.get('plan_de_busqueda', [])
    except Exception as e:
        print(f"❌ Error al generar plan con la IA: {e}")
        return [f"{cliente_ideal} en {ubicacion}"]

def ejecutar_caza(apify_client, terminos, limite):
    print("\n🕵️‍♂️ Fase de Ejecución: El Cazador está en el campo...")
    resultados = []
    for termino in terminos:
        print(f"  -> Buscando: '{termino}'...")
        run_input = {"searchStringsArray": [termino], "maxCrawledPlacesPerSearch": limite, "language": "es"}
        try:
            run = apify_client.actor("compass/crawler-google-places").call(run_input=run_input)
            items = list(apify_client.dataset(run["defaultDatasetId"]).iterate_items())
            resultados.extend(items)
            print(f"    -> Se encontraron {len(items)} resultados.")
        except Exception as e:
            print(f"    -> ❌ Error al buscar '{termino}': {e}")
    return resultados

def guardar_prospectos(supabase, prospectos, id_campana):
    print("\n💾 Guardando prospectos...")
    contador = 0
    for lugar in prospectos:
        prospecto_data = {'campana_id': id_campana, 'nombre_negocio': lugar.get('title'), 'url_google_maps': lugar.get('url'), 'url_sitio_web': lugar.get('website'), 'telefono': lugar.get('phone'), 'email_contacto': lugar.get('email'), 'estado_prospecto': 'cazado'}
        try:
            # Postgrest usa una sintaxis ligeramente diferente
            supabase.from_("prospectos").insert(prospecto_data).execute()
            contador += 1
        except Exception as e:
            # Ignorar duplicados (el error contendrá 'duplicate key value violates unique constraint')
            pass
    print(f"\n👍 Se han guardado {contador} nuevos prospectos.")

def main():
    print("--- INICIO DE MISIÓN DEL CAZADOR ESTRATÉGICO (Postgrest Edition) ---")
    supabase, apify_client, model_ia = inicializar_servicios()
    
    # Buscamos una campaña en estado 'cazando'
    response = supabase.from_("campanas").select("*").eq('estado_campana', 'cazando').limit(1).execute()
    if not response.data:
        print("No hay campañas activas para cazar.")
        return

    campana = response.data[0]
    criterios = json.loads(campana['criterio_busqueda'])
    
    plan = generar_plan_de_caza(model_ia, criterios['que_vendes'], criterios['cliente_ideal'], criterios['ubicacion'])
    
    if plan:
        limite = criterios.get('cantidad', 20) // len(plan) + 1
        resultados = ejecutar_caza(apify_client, plan, limite)
        if resultados:
            guardar_prospectos(supabase, resultados, campana['id'])
            # Cambiamos el estado para que el Analista pueda empezar
            supabase.from_("campanas").update({'estado_campana': 'analizando'}).eq('id', campana['id']).execute()

    print("\n🎉 ¡MISIÓN DEL CAZADOR COMPLETADA!")

if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:
            print(f"Ocurrió un error en el ciclo principal del Cazador: {e}")
        
        print(f"\nCazador en modo de espera por 1 hora...")
        time.sleep(3600)

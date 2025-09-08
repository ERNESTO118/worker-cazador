import os, json, time
from supabase import create_client
from apify_client import ApifyClient
import google.generativeai as genai

def inicializar_servicios():
    supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))
    apify_client = ApifyClient(os.environ.get("APIFY_KEY"))
    genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
    model_ia = genai.GenerativeModel('gemini-1.5-flash')
    print("✅ Conexiones a Supabase, Apify y Google IA establecidas.")
    return supabase, apify_client, model_ia

def generar_plan_de_caza(model_ia, que_vendes, cliente_ideal, ubicacion):
    print("\n🧠 Fase Estratégica: La IA está pensando...")
    prompt = f'Actúa como un director de estrategia de marketing. Mi cliente vende: "{que_vendes}". Su cliente ideal es: "{cliente_ideal}". La búsqueda se centrará en: "{ubicacion}". Crea un "Plan de Caza" en formato JSON con una lista de 5 a 10 términos de búsqueda específicos y creativos para Google Maps. Genera únicamente el objeto JSON con la clave "plan_de_busqueda".'
    try:
        response = model_ia.generate_content(prompt)
        json_text = response.text.strip().replace('```json', '').replace('```', '')
        plan = json.loads(json_text)
        print("✅ Plan de Caza generado por la IA.")
        return plan['plan_de_busqueda']
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
        prospecto = {'campana_id': id_campana, 'nombre_negocio': lugar.get('title'), 'url_google_maps': lugar.get('url'), 'url_sitio_web': lugar.get('website'), 'telefono': lugar.get('phone'), 'email_contacto': lugar.get('email'), 'estado_prospecto': 'cazado'}
        try:
            supabase.table('prospectos').insert(prospecto).execute()
            contador += 1
        except:
            pass # Ignorar duplicados
    print(f"\n👍 Se han guardado {contador} nuevos prospectos.")

def main():
    print("--- INICIO DE MISIÓN DEL CAZADOR ESTRATÉGICO ---")
    supabase, apify_client, model_ia = inicializar_servicios()
    
    response = supabase.table('campanas').select('*').eq('estado_campana', 'cazando').limit(1).execute()
    if not response.data:
        print("No hay campañas activas para cazar.")
        return

    campana = response.data[0]
    criterios = json.loads(campana['criterio_busqueda'])
    
    plan = generar_plan_de_caza(model_ia, criterios['que_vendes'], criterios['cliente_ideal'], criterios['ubicacion'])
    
    if plan:
        limite = criterios['cantidad'] // len(plan) + 1
        resultados = ejecutar_caza(apify_client, plan, limite)
        if resultados:
            guardar_prospectos(supabase, resultados, campana['id'])
            supabase.table('campanas').update({'estado_campana': 'analizando'}).eq('id', campana['id']).execute()

    print("\n🎉 ¡MISIÓN DEL CAZADOR COMPLETADA!")

if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:
            print(f"Ocurrió un error en el ciclo principal del Cazador: {e}")
        
        print(f"\nCazador en modo de espera por 1 hora...")
        time.sleep(3600)

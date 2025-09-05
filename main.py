import os
import json
from supabase import create_client, Client
from apify_client import ApifyClient
import google.generativeai as genai
import time

# --- 1. CONEXIONES A TODOS NUESTROS SERVICIOS ---
def inicializar_servicios():
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    supabase = create_client(supabase_url, supabase_key)

    apify_key = os.environ.get("APIFY_KEY")
    apify_client = ApifyClient(apify_key)

    google_api_key = os.environ.get("GOOGLE_API_KEY")
    genai.configure(api_key=google_api_key)
    model_ia = genai.GenerativeModel('gemini-1.5-flash')

    print("✅ Conexiones a Supabase, Apify y Google IA establecidas.")
    return supabase, apify_client, model_ia

# --- 2. LA FASE ESTRATÉGICA: PENSAR ANTES DE ACTUAR ---
def generar_plan_de_caza(model_ia, que_vendes, cliente_ideal, ubicacion):
    print("\n🧠 Fase Estratégica: La IA está pensando...")
    prompt = f"""
    Actúa como un director de estrategia de marketing de clase mundial.
    Mi cliente vende: "{que_vendes}".
    Su cliente ideal es: "{cliente_ideal}".
    La búsqueda se centrará en la siguiente ubicación: "{ubicacion}".
    Tu misión es crear un "Plan de Caza" en formato JSON. Este plan debe contener una lista de 5 a 10 términos de búsqueda para Google Maps que sean específicos, creativos y con alta probabilidad de encontrar clientes potenciales de calidad.
    Genera únicamente el objeto JSON con una clave "plan_de_busqueda" que contenga la lista de términos.
    """
    try:
        response = model_ia.generate_content(prompt)
        json_text = response.text.strip().replace('```json', '').replace('```', '')
        plan = json.loads(json_text)
        print("✅ Plan de Caza generado por la IA:")
        print(plan['plan_de_busqueda'])
        return plan['plan_de_busqueda']
    except Exception as e:
        print(f"❌ Error al generar el plan de caza con la IA: {e}")
        return [f"{cliente_ideal} en {ubicacion}"]

# --- 3. LA FASE DE EJECUCIÓN: CAZAR ---
def ejecutar_caza(apify_client, terminos_de_busqueda, limite_por_busqueda):
    print("\n🕵️‍♂️ Fase de Ejecución: El Cazador está en el campo...")
    todos_los_resultados = []
    for termino in terminos_de_busqueda:
        print(f"  -> Buscando: '{termino}'...")
        run_input = {
            "searchStringsArray": [termino],
            "maxCrawledPlacesPerSearch": limite_por_busqueda,
            "language": "es"
        }
        try:
            run = apify_client.actor("compass/crawler-google-places").call(run_input=run_input)
            items = list(apify_client.dataset(run["defaultDatasetId"]).iterate_items())
            todos_los_resultados.extend(items)
            print(f"    -> Se encontraron {len(items)} resultados.")
        except Exception as e:
            print(f"    -> ❌ Error al buscar '{termino}': {e}")
    return todos_los_resultados

# --- 4. GUARDADO INTELIGENTE ---
def guardar_prospectos(supabase, prospectos, id_campana):
    print("\n💾 Guardando prospectos en la base de datos...")
    contador_guardados = 0
    for lugar in prospectos:
        nuevo_prospecto = {
            'campana_id': id_campana, 'nombre_negocio': lugar.get('title'),
            'url_google_maps': lugar.get('url'), 'url_sitio_web': lugar.get('website'),
            'telefono': lugar.get('phone'), 'email_contacto': lugar.get('email'),
            'estado_prospecto': 'cazado'
        }
        try:
            supabase.table('prospectos').insert(nuevo_prospecto).execute()
            print(f"  -> ✅ Guardado: {nuevo_prospecto['nombre_negocio']}")
            contador_guardados += 1
        except Exception as e:
            print(f"  -> 🟡 Omitido (posiblemente duplicado): {nuevo_prospecto['nombre_negocio']}")
    
    print(f"\n👍 Se han guardado {contador_guardados} nuevos prospectos.")

# --- EL PUNTO DE ENTRADA: main() ---
def main():
    QUE_VENDE_EL_CLIENTE = "Servicios de construcción de lujo para viviendas y hoteles."
    CLIENTE_IDEAL = "Arquitectos y desarrolladores inmobiliarios"
    UBICACION = "Miami, Florida"
    PROSPECTOS_POR_DIA = 20
    ID_CAMPANA_ACTUAL = 1

    print("--- INICIO DE MISIÓN DEL CAZADOR ESTRATÉGICO v2.0 ---")
    
    try:
        supabase, apify_client, model_ia = inicializar_servicios()
        plan_de_caza = generar_plan_de_caza(model_ia, QUE_VENDE_EL_CLIENTE, CLIENTE_IDEAL, UBICACION)
        
        if plan_de_caza:
            limite_por_busqueda = PROSPECTOS_POR_DIA // len(plan_de_caza) + 1
            resultados_caza = ejecutar_caza(apify_client, plan_de_caza, limite_por_busqueda)
            if resultados_caza:
                guardar_prospectos(supabase, resultados_caza, ID_CAMPANA_ACTUAL)
    except Exception as e:
        print(f"❌ Ocurrió un error fatal en la misión: {e}")
    
    print("\n🎉 ¡MISIÓN DEL CAZADOR ESTRATÉGICO COMPLETADA!")

# --- Ejecutamos la función principal en un bucle infinito ---
if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:
            print(f"Ocurrió un error en el ciclo principal: {e}")
        
        # El trabajador se "duerme" por 1 hora antes de volver a buscar trabajo.
        print("\nCazador en modo de espera por 1 hora...")
        time.sleep(3600)

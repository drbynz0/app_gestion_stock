from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
import httpx
import psycopg2
import re
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from pathlib import Path

logger = logging.getLogger(__name__)

# Configuration base de données PostgreSQL
DB_CONFIG = {
    'dbname': settings.DATABASES['default']['NAME'],
    'user': settings.DATABASES['default']['USER'],
    'password': settings.DATABASES['default']['PASSWORD'],
    'host': settings.DATABASES['default']['HOST'],
    'port': settings.DATABASES['default']['PORT'],
}

# Charger la structure de la BDD pour contextualiser l'IA
STRUCTURE_FILE = Path(settings.BASE_DIR) / "structure_bdd.txt"
with open(STRUCTURE_FILE, "r", encoding="utf-8") as f:
    BDD_STRUCTURE = f.read()

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def call_ai_api(client, question):
    """Appelle le modèle LLM (Groq ou autre) avec un prompt structuré"""
    system_prompt = (
        f"Tu es CTI Assistant, un expert en gestion commerciale, stock, vente et informatique. "
        f"Tu aides un gérant d’entreprise à obtenir des réponses claires et simples. "
        f"Voici la structure de sa base de données PostgreSQL :\n\n{BDD_STRUCTURE}\n\n"
        f"Ta tâche : répondre de manière claire et directe à ses questions. "
        f"Si c’est une question sur les données, attend que le système execute automatiquement une requête à la base de donnée selon la question demandée, puis tu le donne le résultats de la requête avec une reformulation claire et simple. "
        f"Exemple de réponse idéale :\n\n"
        f"Voici la liste des noms des clients :\n\n"
        f"```sql\n"
        f"SELECT name FROM customers_customer\n"
        f"```\n\n"
        f"Cette requête retourne (nombre) clients. Pour obtenir plus d'informations comme "
        f"l'email ou le téléphone, vous pouvez modifier la requête.\n\n"
        f"Si la requête retourne null , vous pouvez répondre par exemple : \n\n"
        f"Aucune donnée n'est disponible pour cette question.\n\n"
        f"N'utilise que des requêtes SELECT. Tu peux aussi répondre à des questions générales sur la vente, le commerce, la gestion, ou l'informatique."
    )

    payload = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ],
        "temperature": 0.2,
        "max_tokens": 1000
    }

    response = await client.post(
        settings.GROQ_API_URL,
        headers={
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json=payload,
        timeout=30.0
    )
    response.raise_for_status()
    return response.json()

def extract_sql_and_explanation(content):
    """Extrait la partie explication + SQL"""
    sql_match = re.search(r"```sql\s*(.*?)```", content, re.DOTALL)
    sql = sql_match.group(1).strip() if sql_match else None
    explanation = re.split(r"```sql\s*.*?```", content, flags=re.DOTALL)[0].strip()
    return explanation, sql

def execute_sql(sql):
    """Exécute une requête SELECT sur la base PostgreSQL"""
    if not sql.strip().lower().startswith("select"):
        raise ValueError("Seules les requêtes SELECT sont autorisées")

    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
    return {"columns": columns, "rows": rows, "query": sql}

@csrf_exempt
async def ask_ai(request):
    """Vue principale pour interroger l'IA"""
    if request.method != "POST":
        return JsonResponse({"error": "Méthode non autorisée"}, status=405)

    try:
        body = json.loads(request.body)
        question = body.get("question", "").strip()
        if not question:
            return JsonResponse({"error": "Le champ 'question' est requis"}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Données JSON invalides"}, status=400)

    try:
        async with httpx.AsyncClient() as client:
            response = await call_ai_api(client, question)
            content = response['choices'][0]['message']['content']
            explanation, sql = extract_sql_and_explanation(content)

            if sql:
                try:
                    result = execute_sql(sql)
                    return JsonResponse({
                        "success": True,
                        "human_response": explanation,
                        "data": result["rows"],
                        "columns": result["columns"],
                        "generated_sql": sql
                    })
                except Exception as e:
                    logger.error(f"Erreur lors de l'exécution SQL : {str(e)}")
                    return JsonResponse({"success": False, "error": str(e), "generated_sql": sql}, status=500)
            else:
                # Pas de SQL — réponse générale (question sur commerce/informatique)
                return JsonResponse({"success": True, "human_response": explanation})

    except Exception as e:
        logger.exception("Erreur inattendue dans l'assistant")
        return JsonResponse({"success": False, "error": "Erreur interne du serveur"}, status=500)

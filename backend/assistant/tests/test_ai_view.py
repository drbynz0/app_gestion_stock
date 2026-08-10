from django.test import AsyncClient, TestCase
from django.urls import reverse
from unittest.mock import patch, AsyncMock
import json

class AskAiViewTest(TestCase):
    def setUp(self):
        self.client = AsyncClient()
        self.url = reverse('ask_ai')

    @patch("assistant.views.call_groq_api", new_callable=AsyncMock)
    @patch("assistant.views.execute_sql_query")
    async def test_valid_sql_question(self, mock_execute_sql_query, mock_call_groq_api):
        # Simule la réponse de l'API Groq
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(return_value={
            "choices": [
                {
                    "message": {
                        "content": "Voici les résultats:\n```sql\nSELECT * FROM product;\n```"
                    }
                }
            ]
        })
        mock_call_groq_api.return_value = mock_response

        # Simule la réponse de la base de données
        mock_execute_sql_query.return_value = {
            "columns": ["id", "name"],
            "rows": [(1, "Routeur")],
            "query": "SELECT * FROM product;"
        }

        response = await self.client.post(
            self.url,
            data=json.dumps({"question": "Quels sont les produits ?"}),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        print("Status Code:", response.status_code)
        print("Response JSON:", response.content)
        self.assertTrue(data["success"])
        self.assertEqual(data["columns"], ["id", "name"])
        self.assertEqual(data["rows"], [[1, "Routeur"]])

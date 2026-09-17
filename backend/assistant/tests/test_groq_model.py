from django.test import SimpleTestCase

from assistant.views import get_groq_model_name


class GroqModelConfigTests(SimpleTestCase):
    def test_default_model_is_active_and_supported(self):
        self.assertEqual(get_groq_model_name(), 'qwen/qwen3.8-27b')

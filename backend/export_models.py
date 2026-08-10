import os
import django

# Initialisation de Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cti_app_dj.settings")
django.setup()

from django.apps import apps
from django.db import models

def get_field_description(field):
    return f"{field.name} ({field.get_internal_type()})"

def export_model_structure(file_path="structure_bdd_all.txt"):
    with open(file_path, "w", encoding="utf-8") as f:
        for model in apps.get_models():
            f.write(f"Modèle : {model.__name__}\n")
            f.write(f"  Table : {model._meta.db_table}\n")
            for field in model._meta.fields:
                f.write(f"    - {get_field_description(field)}\n")
            f.write("\n")

    print(f"Structure exportée dans {file_path}")

# Exécution
if __name__ == "__main__":
    export_model_structure()

#!/bin/sh
set -e

echo "=== Démarrage du backend Django ==="

# Application des migrations de base de données
echo "Application des migrations..."
python manage.py migrate --noinput || echo "Avertissement: Les migrations n'ont pas pu être appliquées automatiquement."

# Collecte des fichiers statiques
echo "Collecte des fichiers statiques..."
python manage.py collectstatic --noinput || true

echo "Lancement du serveur backend..."
exec "$@"

# ![Flutter](https://img.shields.io/badge/Flutter-02569B?logo=flutter&logoColor=white) ![Django](https://img.shields.io/badge/Django-092E20?logo=django&logoColor=white) ![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white) ![Android](https://img.shields.io/badge/Android-3DDC84?logo=android&logoColor=white) ![iOS](https://img.shields.io/badge/iOS-000000?logo=ios&logoColor=white)

# Application Mobile de Gestion de Stock

## Description du Projet
L'application mobile de gestion de stock est conçue pour faciliter la gestion des stocks d'une entreprise de vente et d'achat. Elle permet aux utilisateurs de suivre les produits, gérer les commandes, et visualiser les statistiques de vente. Grâce à une interface intuitive, cette application répond aux besoins quotidiens des commerçants.

### Fonctionnalités Clés
- Gestion des produits et des catégories.
- Suivi des commandes internes et externes.
- Gestion des clients et des fournisseurs.
- Création et gestion des factures.
- Statistiques de vente et rapports.
- Notifications en temps réel pour les mises à jour importantes.

## Tech Stack
| Technologie      | Description                       |
|------------------|-----------------------------------|
| ![Flutter](https://img.shields.io/badge/Flutter-02569B?logo=flutter&logoColor=white) | Framework pour le développement d'applications mobiles. |
| ![Django](https://img.shields.io/badge/Django-092E20?logo=django&logoColor=white)   | Framework web Python pour le développement backend. |
| ![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)   | Langage de programmation utilisé pour le backend. |
| ![Android](https://img.shields.io/badge/Android-3DDC84?logo=android&logoColor=white) | Plateforme pour le développement d'applications Android. |
| ![iOS](https://img.shields.io/badge/iOS-000000?logo=ios&logoColor=white)             | Plateforme pour le développement d'applications iOS. |

## Instructions d'Installation

### Prérequis
- Flutter SDK
- Python 3.x
- Django
- Node.js (pour les dépendances front-end)
- Gradle (pour Android)

### Étapes d'Installation
1. **Clonez le dépôt :**
   ```bash
   git clone https://github.com/drbynz0/app_stock.git
   cd app_stock/cti_app
   ```

2. **Installez les dépendances Python :**
   ```bash
   cd cti_app_dj
   pip install -r requirements.txt
   ```

3. **Installez les dépendances Flutter :**
   ```bash
   cd ../
   flutter pub get
   ```

4. **Configurez les variables d'environnement :**
   Créez un fichier `.env` à la racine du projet et ajoutez les variables nécessaires, par exemple :
   ```env
   SECRET_KEY=your_secret_key
   DEBUG=True
   ```

5. **Démarrez le serveur Django :**
   ```bash
   python manage.py runserver
   ```

6. **Lancez l'application Flutter :**
   ```bash
   flutter run
   ```

## Utilisation

### Comment exécuter le projet
- Pour accéder à l'application, ouvrez votre navigateur et allez à `http://localhost:8000` pour le backend Django.
- Pour l'application mobile, utilisez un émulateur ou un appareil physique.

### Exemples d'utilisation
- **Ajouter un produit :** Utilisez l'interface pour entrer les détails du produit.
- **Consulter les statistiques de vente :** Naviguez vers la section des statistiques pour visualiser les performances.

## Structure du Projet

Voici un aperçu de la structure du projet :

```
app_stock/
├── cti_app/
│   ├── android/                # Code source pour l'application Android
│   ├── ios/                    # Code source pour l'application iOS
│   ├── lib/                    # Code source principal de l'application Flutter
│   │   ├── models/             # Modèles de données
│   │   ├── screens/            # Écrans de l'application
│   │   ├── services/           # Services pour les appels API
│   │   └── main.dart           # Point d'entrée de l'application Flutter
│   ├── pubspec.yaml            # Dépendances de l'application Flutter
│   └── README.md               # Documentation de l'application
└── cti_app_dj/                 # Code source pour le backend Django
    ├── manage.py               # Script de gestion Django
    ├── requirements.txt        # Dépendances Python
    ├── cti_app_dj/             # Configuration du projet Django
    │   ├── settings.py         # Paramètres de configuration
    │   └── urls.py             # Routes de l'application
    └── activities/             # Gestion des activités
```

Nous vous remercions de votre intérêt pour le projet et sommes impatients de voir vos contributions !

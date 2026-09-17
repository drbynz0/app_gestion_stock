"""L'assistant est stateless : aucune conversation n'est stockée en base.

L'historique temporaire reste dans l'état mémoire du frontend et est envoyé
au backend uniquement pendant la requête en cours.
"""

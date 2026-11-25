"""
Utilitaire pour enregistrer les activités dans l'historique.
Utilisation : from historical.utils import log_activity
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def log_activity(company, description: str, icon: str = "information-outline") -> None:
    """
    Crée une entrée dans l'historique pour une entreprise donnée.
    La fonction est silencieuse en cas d'erreur pour ne pas bloquer
    la réponse principale.
    """
    try:
        from .models import Historical
        Historical.objects.create(
            company=company,
            description=description,
            icon=icon,
        )
    except Exception as exc:  # pragma: no cover
        logger.warning("log_activity failed: %s", exc)

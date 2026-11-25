import os
import logging
import httpx
from django.conf import settings

logger = logging.getLogger(__name__)


def send_sms(to_phone: str, message: str) -> dict:
    """
    Service d'envoi de SMS transactionnels multi-fournisseurs.
    Fournisseurs supportés (configurables dans var.env) :
    1. Brevo Transactional SMS (Recommandé en France/Europe - https://api.brevo.com/v3/transactionalSMS/send)
    2. Twilio (Mondial - https://api.twilio.com)
    3. Mode développement / console si aucune clé n'est encore configurée.
    """
    if not to_phone or not to_phone.strip():
        return {'success': False, 'error': 'Numéro de téléphone manquant'}

    clean_phone = to_phone.strip().replace(' ', '').replace('-', '')
    
    # --- 1. BREVO TRANSACTIONAL SMS ---
    brevo_key = getattr(settings, 'BREVO_API_KEY', None) or os.getenv('BREVO_API_KEY')
    if brevo_key:
        try:
            sender = getattr(settings, 'BREVO_SMS_SENDER', None) or os.getenv('BREVO_SMS_SENDER') or 'StockPro'
            # Brevo exige max 11 caractères alphanumériques pour le sender
            sender = sender[:11]
            
            resp = httpx.post(
                'https://api.brevo.com/v3/transactionalSMS/send',
                headers={
                    'api-key': brevo_key,
                    'Content-Type': 'application/json',
                },
                json={
                    'sender': sender,
                    'recipient': clean_phone,
                    'content': message,
                    'type': 'transactional',
                },
                timeout=12.0,
            )
            if resp.status_code in (200, 201):
                logger.info(f"[Brevo SMS] SMS envoyé avec succès à {clean_phone}")
                return {'success': True, 'provider': 'brevo', 'response': resp.json()}
            else:
                logger.warning(f"[Brevo SMS] Erreur {resp.status_code}: {resp.text}")
        except Exception as exc:
            logger.error(f"[Brevo SMS] Exception: {exc}")

    # --- 2. TWILIO SMS ---
    twilio_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None) or os.getenv('TWILIO_ACCOUNT_SID')
    twilio_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None) or os.getenv('TWILIO_AUTH_TOKEN')
    twilio_from = getattr(settings, 'TWILIO_PHONE_NUMBER', None) or os.getenv('TWILIO_PHONE_NUMBER')

    if twilio_sid and twilio_token and twilio_from:
        try:
            url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Messages.json"
            resp = httpx.post(
                url,
                auth=(twilio_sid, twilio_token),
                data={
                    'From': twilio_from,
                    'To': clean_phone,
                    'Body': message,
                },
                timeout=12.0,
            )
            if resp.status_code in (200, 201):
                logger.info(f"[Twilio SMS] SMS envoyé avec succès à {clean_phone}")
                return {'success': True, 'provider': 'twilio', 'response': resp.json()}
            else:
                logger.warning(f"[Twilio SMS] Erreur {resp.status_code}: {resp.text}")
        except Exception as exc:
            logger.error(f"[Twilio SMS] Exception: {exc}")

    # --- 3. LOG CONSOLE (Aucune clé SMS configurée dans var.env) ---
    print("\n" + "=" * 60)
    print(f"[CELLULAR SMS NOTICE] Pour délivrer des vrais SMS physiques sur le réseau mobile :")
    print(f"Numéro destinataire : {clean_phone}")
    print(f"Message : {message}")
    print(f"Statut : En attente d'une clé API SMS dans var.env (BREVO_API_KEY ou TWILIO_ACCOUNT_SID).")
    print("=" * 60 + "\n")

    return {
        'success': False,
        'simulated': True,
        'message': "Passerelle SMS non configurée (ajoutez BREVO_API_KEY ou TWILIO_ACCOUNT_SID dans var.env).",
    }

import logging
from django.conf import settings
from django.core.mail import send_mail
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def _get_from_email():
    return getattr(settings, 'DEFAULT_FROM_EMAIL', None) or getattr(settings, 'EMAIL_HOST_USER', 'noreply@stockapp.com')


def _render_base_email(title: str, subtitle: str, body_html: str) -> str:
    """Modèle d'email HTML professionnel et responsive avec branding moderne."""
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #0f172a; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #f8fafc;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #0f172a; padding: 40px 15px;">
    <tr>
      <td align="center">
        <table width="100%" max-width="580" style="max-width: 580px; background-color: #1e293b; border-radius: 16px; border: 1px solid #334155; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.35);">
          <!-- Header Banner -->
          <tr>
            <td style="padding: 32px 32px 24px; background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); border-bottom: 1px solid #334155; text-align: center;">
              <div style="display: inline-block; padding: 10px 16px; background-color: rgba(0, 229, 153, 0.12); border-radius: 12px; border: 1px solid rgba(0, 229, 153, 0.3); margin-bottom: 14px;">
                <span style="color: #00E599; font-weight: 800; font-size: 16px; letter-spacing: 1px;">GESTION DE STOCK PRO</span>
              </div>
              <h1 style="margin: 0; font-size: 22px; font-weight: 700; color: #ffffff;">{title}</h1>
              {f'<p style="margin: 8px 0 0; font-size: 14px; color: #94a3b8;">{subtitle}</p>' if subtitle else ''}
            </td>
          </tr>
          
          <!-- Body Content -->
          <tr>
            <td style="padding: 32px; font-size: 15px; line-height: 1.6; color: #cbd5e1;">
              {body_html}
            </td>
          </tr>
          
          <!-- Footer -->
          <tr>
            <td style="padding: 24px 32px; background-color: #0f172a; border-top: 1px solid #334155; text-align: center; font-size: 12px; color: #64748b;">
              <p style="margin: 0;">Ce message automatique vous a été envoyé par votre système de gestion de stock sécurisé.</p>
              <p style="margin: 6px 0 0;">Si vous n'êtes pas à l'origine de cette demande, veuillez ignorer ce message ou contacter votre administrateur.</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def send_verification_code_email(email: str, code: str, purpose: str = "Vérification de sécurité") -> bool:
    """Envoi réel du code à 6 chiffres pour l'onboarding, la mise à jour de profil ou le 2FA."""
    subject = f"[{code}] Votre code de sécurité - Gestion de Stock"
    title = "Code de vérification"
    subtitle = purpose

    body_html = f"""
      <p style="margin-top: 0;">Bonjour,</p>
      <p>Voici votre code de vérification à 6 chiffres requis pour valider votre action :</p>
      
      <div style="text-align: center; margin: 30px 0;">
        <div style="display: inline-block; letter-spacing: 10px; font-size: 34px; font-weight: 900; color: #00E599; background: #0b1329; padding: 16px 28px; border-radius: 12px; border: 2px dashed #00E599;">
          {code}
        </div>
      </div>
      
      <p style="font-size: 13px; color: #94a3b8; text-align: center; margin-bottom: 0;">
        Ce code est strictement confidentiel et expirera dans <strong>10 minutes</strong>.
      </p>
    """

    html_content = _render_base_email(title, subtitle, body_html)
    plain_content = f"Bonjour,\n\nVotre code de vérification est : {code}\nCe code expire dans 10 minutes.\n\nL'équipe de gestion de stock."

    try:
        send_mail(
            subject=subject,
            message=plain_content,
            from_email=_get_from_email(),
            recipient_list=[email],
            html_message=html_content,
            fail_silently=False,
        )
        logger.info(f"Email de vérification envoyé à {email}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'email à {email}: {e}")
        return False


def send_company_welcome_email(user, company) -> bool:
    """Email de bienvenue professionnel envoyé après la création de l'entreprise."""
    if not user.email:
        return False

    subject = f"Bienvenue sur votre plateforme - {company.name}"
    title = f"Félicitations pour la création de {company.name} !"
    subtitle = "Votre espace de gestion d'entreprise est prêt"

    body_html = f"""
      <p style="margin-top: 0;">Bonjour <strong>{user.first_name or user.username}</strong>,</p>
      <p>Votre entreprise <strong>{company.name}</strong> a été initialisée avec succès avec tous ses modules de gestion :</p>
      
      <div style="background-color: #0b1329; border-radius: 12px; padding: 18px 20px; margin: 20px 0; border: 1px solid #334155;">
        <div style="margin-bottom: 8px;"><strong style="color: #00E599;">Entreprise :</strong> {company.name}</div>
        <div style="margin-bottom: 8px;"><strong style="color: #00E599;">Identifiant entreprise :</strong> @{company.company_username or company.slug}</div>
        <div style="margin-bottom: 8px;"><strong style="color: #00E599;">Admin principal :</strong> @{user.username}</div>
        <div><strong style="color: #00E599;">Devise principale :</strong> {company.currency}</div>
      </div>

      <p>En tant qu'<strong>administrateur principal</strong>, vous bénéficiez de tous les accès :</p>
      <ul style="padding-left: 20px; color: #94a3b8;">
        <li>Gestion du catalogue produit et des stocks d'entrepôt</li>
        <li>Suivi des ventes, factures et livraisons en temps réel</li>
        <li>Création et gestion des comptes de votre équipe (Vendeurs et Administrateurs délégués)</li>
        <li>Sécurité avancée (Authentification à double facteur 2FA et code PIN)</li>
      </ul>

      <p style="margin-top: 24px; color: #cbd5e1;">Nous vous souhaitons une excellente gestion commerciale !</p>
    """

    html_content = _render_base_email(title, subtitle, body_html)
    plain_content = f"Bonjour {user.username},\n\nVotre entreprise {company.name} a bien été créée.\nVous êtes l'administrateur principal.\n\nBonne utilisation !"

    try:
        send_mail(
            subject=subject,
            message=plain_content,
            from_email=_get_from_email(),
            recipient_list=[user.email],
            html_message=html_content,
            fail_silently=False,
        )
        logger.info(f"Email de bienvenue envoyé à {user.email}")
        return True
    except Exception as e:
        logger.error(f"Erreur d'envoi d'email de bienvenue à {user.email}: {e}")
        return False


def send_password_changed_notification_email(user) -> bool:
    """Notification de sécurité envoyée dès que le mot de passe est modifié."""
    if not user.email:
        return False

    subject = "Alerte de sécurité : Votre mot de passe a été modifié"
    title = "Mot de passe modifié"
    subtitle = "Notification de sécurité relative à votre compte"

    body_html = f"""
      <p style="margin-top: 0;">Bonjour <strong>{user.first_name or user.username}</strong>,</p>
      <p>Nous vous confirmons que le mot de passe de votre compte (<strong>@{user.username}</strong>) vient d'être modifié avec succès.</p>
      
      <div style="background-color: rgba(239, 68, 68, 0.1); border-left: 4px solid #ef4444; padding: 14px 18px; border-radius: 6px; margin: 24px 0;">
        <p style="margin: 0; font-size: 14px; color: #fca5a5;">
          <strong>Important :</strong> Si vous n'êtes PAS à l'origine de cette modification, contactez immédiatement l'administrateur de votre entreprise ou procédez à une réinitialisation d'urgence de votre accès.
        </p>
      </div>

      <p style="margin-bottom: 0;">Cordialement,<br>L'équipe de sécurité.</p>
    """

    html_content = _render_base_email(title, subtitle, body_html)
    plain_content = f"Bonjour {user.username},\n\nLe mot de passe de votre compte a été modifié avec succès.\nSi vous n'en êtes pas l'auteur, contactez immédiatement votre responsable."

    try:
        send_mail(
            subject=subject,
            message=plain_content,
            from_email=_get_from_email(),
            recipient_list=[user.email],
            html_message=html_content,
            fail_silently=False,
        )
        logger.info(f"Notification de changement de mot de passe envoyée à {user.email}")
        return True
    except Exception as e:
        logger.error(f"Erreur d'envoi de notification mot de passe à {user.email}: {e}")
        return False


def send_company_deletion_notification_email(email: str, company_name: str, admin_name: str) -> bool:
    """Notification finale envoyée à l'administrateur après la suppression de son entreprise."""
    if not email:
        return False

    subject = f"Confirmation de suppression définitive - {company_name}"
    title = "Entreprise supprimée"
    subtitle = "Confirmation d'effacement de vos données"

    body_html = f"""
      <p style="margin-top: 0;">Bonjour <strong>{admin_name}</strong>,</p>
      <p>Nous vous confirmons que l'entreprise <strong>{company_name}</strong> ainsi que l'ensemble des comptes utilisateurs associés et des données d'activité ont été <strong>définitivement supprimés</strong> conformément à votre demande.</p>
      
      <p style="color: #94a3b8; font-size: 13px;">
        Toutes les sessions ont été invalidées. Nous vous remercions d'avoir utilisé notre service.
      </p>
    """

    html_content = _render_base_email(title, subtitle, body_html)
    plain_content = f"Bonjour {admin_name},\n\nL'entreprise {company_name} et tous les comptes associés ont été définitivement supprimés."

    try:
        send_mail(
            subject=subject,
            message=plain_content,
            from_email=_get_from_email(),
            recipient_list=[email],
            html_message=html_content,
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Erreur d'envoi notification suppression à {email}: {e}")
        return False

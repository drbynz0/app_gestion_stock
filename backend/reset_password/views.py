from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.mail import send_mail
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model

from .models import PasswordResetCode
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

User = get_user_model()

@api_view(['POST'])
@permission_classes([AllowAny])
def request_reset_code(request):
    email = request.data.get('email')
    username = request.data.get('username')
    
    try:
        user = User.objects.get(email=email, username=username)
    except User.DoesNotExist:
        return Response({'error': 'Aucun utilisateur trouvé'}, status=400)

    code = PasswordResetCode.generate_code(user)
    
    send_mail(
        'Code de réinitialisation',
        f'Votre code est : {code}',
        'noreply@votresite.com',
        [email],
        fail_silently=False,
    )
    
    return Response({'success': 'Code envoyé'})

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_code(request):
    code = request.data.get('code')
    email = request.data.get('email')
    
    try:
        user = User.objects.get(email=email)
        reset_code = PasswordResetCode.objects.get(
            user=user,
            code=code,
            is_used=False,
            created_at__gte=timezone.now()-timedelta(minutes=30)
        )
        reset_code.is_used = True
        reset_code.save()
        return Response({'success': 'Code valide'})
    except Exception:
        return Response({'error': 'Code invalide'}, status=400)

@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    email = request.data.get('email')
    new_password = request.data.get('new_password')
    
    try:
        user = User.objects.get(email=email)
        user.set_password(new_password)
        user.save()
        return Response({'success': 'Mot de passe mis à jour'})
    except User.DoesNotExist:
        return Response({'error': 'Utilisateur non trouvé'}, status=400)
    
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])  # L'utilisateur doit être authentifié
def change_password(request):
    current_password = request.data.get('current_password')
    new_password = request.data.get('new_password')
    
    if not current_password or not new_password:
        return Response({'error': 'Les deux champs sont obligatoires'}, status=400)
    
    user = request.user  # On récupère l'utilisateur connecté
    
    # Vérification du mot de passe actuel
    if not user.check_password(current_password):
        return Response({'error': 'Mot de passe actuel incorrect'}, status=400)
    
    # Vérification que le nouveau est différent
    if user.check_password(new_password):
        return Response({'error': 'Le nouveau mot de passe doit être différent'}, status=400)
    
    # Mise à jour du mot de passe
    user.set_password(new_password)
    user.save()
    
    return Response({'success': 'Mot de passe mis à jour avec succès'})

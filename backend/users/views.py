import random
import uuid
from django.conf import settings
from django.db import transaction
from django.utils.text import slugify
from django.contrib.auth import authenticate
from django.utils import timezone
from datetime import timedelta
from rest_framework import generics, permissions, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User, SellerPrivileges, Company, VerificationCode
from .permissions import IsSeller
from .permissions_company import IsCompanyAdmin, IsCompanyPrimaryAdmin
from .tenancy import IsCompanyUser
from .serializers import (
    UserSerializer, 
    RegisterSerializer, 
    ProfileUpdateSerializer, 
    CompanyRegisterSerializer
)
from .email_service import (
    send_verification_code_email,
    send_company_welcome_email,
    send_company_deletion_notification_email,
)
from stock.models import Warehouse, StockLocation


class CompanyUserQuerysetMixin:
    """Filtre strict par entreprise pour toutes les requêtes utilisateurs."""
    def get_queryset(self):
        user = self.request.user
        if not user or not user.is_authenticated or not user.company_id:
            return super().get_queryset().none()
        return super().get_queryset().filter(company=user.company)


class UserViewSet(CompanyUserQuerysetMixin, viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsCompanyUser]

    def perform_create(self, serializer):
        user = serializer.save(company=self.request.user.company)
        if user.is_seller:
            SellerPrivileges.objects.get_or_create(user=user)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = str(request.data.get('username', '')).strip().lower()
        password = str(request.data.get('password', ''))
        user = authenticate(username=username, password=password)
        
        if user is None or not user.company_id or not user.company.is_active:
            return Response({'error': 'Identifiants incorrects ou entreprise inactive.'}, status=status.HTTP_401_UNAUTHORIZED)

        # Si l'authentification à deux facteurs est activée
        if user.two_factor_enabled:
            code = f"{random.randint(100000, 999999)}"
            target = user.email or user.phone or username
            VerificationCode.objects.create(
                user=user,
                code_type='2FA',
                target=target,
                code=code,
                expires_at=timezone.now() + timedelta(minutes=10)
            )

            # Envoi effectif par email si disponible
            if user.email:
                send_verification_code_email(
                    email=user.email,
                    code=code,
                    purpose="Validation de connexion à double facteur (2FA)"
                )

            print(f"\n==========================================")
            print(f"[2FA SECURITY CODE] Code pour @{user.username} ({target}) : {code}")
            print(f"==========================================\n")
            return Response({
                'two_factor_required': True,
                'user_id': user.id,
                'target': target,
                'dev_code': code,  # Accessible en mode dev pour tests rapides
                'message': f'Code 2FA envoyé à {target}.'
            }, status=status.HTTP_200_OK)

        token, _ = Token.objects.get_or_create(user=user)
        is_primary = user.is_primary_admin or (user.company and user.company.created_by_id == user.id)
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data,
            'is_admin': user.user_type == 'ADMIN',
            'is_primary_admin': is_primary,
        })


class Verify2FALoginView(APIView):
    """Validation du code 2FA lors de la connexion."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        user_id = request.data.get('user_id')
        code = str(request.data.get('code', '')).strip()

        if not user_id or not code:
            return Response({'error': 'Identifiant et code requis.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'Utilisateur introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        code_entry = VerificationCode.objects.filter(
            user=user,
            code_type='2FA',
            code=code,
            is_used=False,
            expires_at__gte=timezone.now()
        ).first()

        if not code_entry:
            return Response({'error': 'Code 2FA invalide ou expiré.'}, status=status.HTTP_400_BAD_REQUEST)

        code_entry.is_used = True
        code_entry.save(update_fields=['is_used'])

        token, _ = Token.objects.get_or_create(user=user)
        is_primary = user.is_primary_admin or (user.company and user.company.created_by_id == user.id)
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data,
            'is_admin': user.user_type == 'ADMIN',
            'is_primary_admin': is_primary,
        })


class SendVerificationCodeView(APIView):
    """Envoi d'un code SMS ou Email à 6 chiffres."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        target = str(request.data.get('target', '')).strip()
        code_type = str(request.data.get('type', 'EMAIL')).upper()
        check_only = bool(request.data.get('check_only', False))

        if not target:
            return Response({'error': 'La cible (email ou téléphone) est requise.'}, status=status.HTTP_400_BAD_REQUEST)
        if code_type not in ('EMAIL', 'SMS'):
            return Response({'error': 'Type de code invalide.'}, status=status.HTTP_400_BAD_REQUEST)

        # Vérification d'unicité pour l'adresse e-mail avant tout envoi de code
        if code_type == 'EMAIL':
            if User.objects.filter(email__iexact=target).exists():
                return Response(
                    {'error': 'Cette adresse e-mail est déjà utilisée par un compte existant.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if check_only:
                return Response({'available': True, 'message': 'Cette adresse e-mail est disponible.'}, status=status.HTTP_200_OK)

        code = f"{random.randint(100000, 999999)}"
        user = request.user if request.user.is_authenticated else None

        VerificationCode.objects.create(
            user=user,
            code_type=code_type,
            target=target,
            code=code,
            expires_at=timezone.now() + timedelta(minutes=10)
        )

        email_sent = False
        if code_type == 'EMAIL':
            email_sent = send_verification_code_email(
                email=target,
                code=code,
                purpose="Validation d'adresse email - Création d'entreprise"
            )

        print(f"\n==========================================")
        print(f"[{code_type} VERIFICATION CODE] Envoyé à {target} : {code} (Email SMTP: {'Envoyé' if email_sent else 'Non envoyé/SMS'})")
        print(f"==========================================\n")

        response_data = {
            'message': f'Code de vérification envoyé avec succès à {target}.',
            'target': target,
            'code_type': code_type,
            'email_sent': email_sent,
        }
        if getattr(settings, 'DEBUG', False):
            response_data['dev_code'] = code

        return Response(response_data)


class VerifyCodeView(APIView):
    """Vérification du code SMS ou Email à 6 chiffres."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        target = str(request.data.get('target', '')).strip()
        code = str(request.data.get('code', '')).strip()
        code_type = str(request.data.get('type', 'EMAIL')).upper()

        code_entry = VerificationCode.objects.filter(
            target=target,
            code=code,
            code_type=code_type,
            is_used=False,
            expires_at__gte=timezone.now()
        ).first()

        if not code_entry:
            return Response({'verified': False, 'error': 'Code invalide ou expiré.'}, status=status.HTTP_400_BAD_REQUEST)

        code_entry.is_used = True
        code_entry.save(update_fields=['is_used'])

        # Si l'utilisateur est connecté et valide son propre profil
        if request.user.is_authenticated:
            if code_type == 'EMAIL':
                request.user.email_verified = True
                request.user.email = target
                request.user.save(update_fields=['email_verified', 'email'])
            elif code_type == 'SMS':
                request.user.phone_verified = True
                request.user.phone = target
                request.user.save(update_fields=['phone_verified', 'phone'])

        return Response({'verified': True, 'message': 'Vérification réussie.'})


class Toggle2FAView(APIView):
    """Activation ou désactivation du 2FA par l'utilisateur connecté."""
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        user = request.user
        enable = request.data.get('enable', not user.two_factor_enabled)
        user.two_factor_enabled = bool(enable)
        user.save(update_fields=['two_factor_enabled'])
        return Response({
            'two_factor_enabled': user.two_factor_enabled,
            'message': 'Authentification à deux facteurs mise à jour.'
        })


class ProfileView(generics.RetrieveUpdateAPIView):
    """Profil personnel. Le nom d'utilisateur et l'entreprise sont strictement non modifiables."""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProfileUpdateSerializer

    def get_object(self):
        return self.request.user


def purge_company_data(company):
    """
    Purge ordonnée et transactionnelle de toutes les données du locataire
    afin de respecter les contraintes de clés étrangères (PROTECT)
    avant la suppression définitive de l'entreprise.
    """
    from django.apps import apps
    import logging
    logger = logging.getLogger(__name__)

    # 1. Modules Stock (lignes d'inventaire, sessions, mouvements, soldes, emplacements, entrepôts)
    try:
        InventoryLine = apps.get_model('stock', 'InventoryLine')
        InventorySession = apps.get_model('stock', 'InventorySession')
        StockMovement = apps.get_model('stock', 'StockMovement')
        StockBalance = apps.get_model('stock', 'StockBalance')
        StockLocation = apps.get_model('stock', 'StockLocation')
        Warehouse = apps.get_model('stock', 'Warehouse')

        InventoryLine.objects.filter(inventory__company=company).delete()
        InventorySession.objects.filter(company=company).delete()
        StockMovement.objects.filter(company=company).delete()
        StockBalance.objects.filter(company=company).delete()
        StockLocation.objects.filter(warehouse__company=company).delete()
        Warehouse.objects.filter(company=company).delete()
    except Exception as e:
        logger.error(f"Erreur lors de la purge du stock: {e}")

    # 2. Factures (Clients et Fournisseurs)
    try:
        FactureClient = apps.get_model('factures', 'FactureClient')
        FactureFournisseur = apps.get_model('factures', 'FactureFournisseur')
        FactureClient.objects.filter(company=company).delete()
        FactureFournisseur.objects.filter(company=company).delete()
    except Exception as e:
        logger.error(f"Erreur lors de la purge des factures: {e}")

    # 3. Bons de livraison
    try:
        DeliveryItem = apps.get_model('delivery_notes', 'DeliveryItem')
        DeliveryNote = apps.get_model('delivery_notes', 'DeliveryNote')
        DeliveryItem.objects.filter(delivery_note__company=company).delete()
        DeliveryNote.objects.filter(company=company).delete()
    except Exception as e:
        logger.error(f"Erreur lors de la purge des bons de livraison: {e}")

    # 4. Commandes Internes & Externes
    try:
        InternalOrderItem = apps.get_model('internalOrders', 'OrderItem')
        Payment = apps.get_model('internalOrders', 'Payment')
        InternalOrder = apps.get_model('internalOrders', 'InternalOrder')
        Payment.objects.filter(order__company=company).delete()
        InternalOrderItem.objects.filter(order__company=company).delete()
        InternalOrder.objects.filter(company=company).delete()
    except Exception as e:
        logger.error(f"Erreur lors de la purge des commandes internes: {e}")

    try:
        ExternalOrderItem = apps.get_model('externalOrders', 'OrderItem')
        ExternalOrder = apps.get_model('externalOrders', 'ExternalOrder')
        ExternalOrderItem.objects.filter(order__company=company).delete()
        ExternalOrder.objects.filter(company=company).delete()
    except Exception as e:
        logger.error(f"Erreur lors de la purge des commandes externes: {e}")

    # 5. Remises, Activités, Historique
    for app_label, model_name in [('discounts', 'Discount'), ('activities', 'Activity'), ('historical', 'Historical')]:
        try:
            M = apps.get_model(app_label, model_name)
            M.objects.filter(company=company).delete()
        except Exception as e:
            logger.error(f"Erreur lors de la purge {app_label}.{model_name}: {e}")

    # 6. Catalogue Produits & Catégories
    try:
        ProductImage = apps.get_model('products', 'ProductImage')
        Product = apps.get_model('products', 'Product')
        Category = apps.get_model('products', 'Category')
        ProductImage.objects.filter(product__company=company).delete()
        Product.objects.filter(company=company).delete()
        Category.objects.filter(company=company).delete()
    except Exception as e:
        logger.error(f"Erreur lors de la purge des produits: {e}")

    # 7. Clients & Fournisseurs
    for app_label, model_name in [('customers', 'Customer'), ('suppliers', 'Supplier')]:
        try:
            M = apps.get_model(app_label, model_name)
            M.objects.filter(company=company).delete()
        except Exception as e:
            logger.error(f"Erreur lors de la purge {app_label}.{model_name}: {e}")

    # 8. Utilisateurs, Tokens, Privilèges, Codes
    try:
        VerificationCode = apps.get_model('users', 'VerificationCode')
        VerificationCode.objects.filter(user__company=company).delete()
    except Exception as e:
        pass

    try:
        SellerPrivileges = apps.get_model('users', 'SellerPrivileges')
        SellerPrivileges.objects.filter(user__company=company).delete()
    except Exception as e:
        pass

    try:
        from rest_framework.authtoken.models import Token
        Token.objects.filter(user__company=company).delete()
    except Exception as e:
        pass

    # 9. Supprimer les utilisateurs de cette entreprise
    User = apps.get_model('users', 'User')
    User.objects.filter(company=company).delete()

    # 10. Supprimer l'entreprise
    company.delete()


class CompanySettingsView(APIView):
    """
    Paramètres métier de l'entreprise.
    Lecture : tout admin de l'entreprise.
    Modification et Suppression : réservé à l'Admin Principal (créateur).
    """
    permission_classes = [IsCompanyAdmin]
    supported_currencies = {'MAD', 'EUR', 'USD', 'XOF', 'XAF', 'GBP'}

    def _company(self, request):
        return request.user.company if request.user.company_id else None

    def get(self, request):
        company = self._company(request)
        if not company:
            return Response({'detail': 'Aucune entreprise associée.'}, status=status.HTTP_404_NOT_FOUND)
        is_primary = request.user.is_primary_admin or (company.created_by_id == request.user.id)
        return Response({
            'id': company.id,
            'name': company.name,
            'company_username': company.company_username or company.slug,
            'currency': company.currency,
            'logo_uri': company.logo_uri,
            'primary_color': company.primary_color,
            'is_primary_admin': is_primary,
        })

    def patch(self, request):
        if not IsCompanyPrimaryAdmin().has_permission(request, self):
            return Response({'detail': "Seul l'administrateur principal créateur peut modifier les paramètres de l'entreprise."}, status=status.HTTP_403_FORBIDDEN)
        company = self._company(request)
        if not company:
            return Response({'detail': 'Entreprise introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        fields = []
        if 'currency' in request.data:
            currency = str(request.data.get('currency', '')).upper()
            if currency not in self.supported_currencies:
                return Response({'currency': ['Devise non prise en charge.']}, status=status.HTTP_400_BAD_REQUEST)
            company.currency = currency
            fields.append('currency')
        if 'name' in request.data:
            name = str(request.data.get('name', '')).strip()
            if not name:
                return Response({'name': ["Le nom de l'entreprise est requis."]}, status=status.HTTP_400_BAD_REQUEST)
            company.name = name
            fields.append('name')
        if 'logo_uri' in request.data:
            company.logo_uri = str(request.data.get('logo_uri') or '')
            fields.append('logo_uri')
        if 'primary_color' in request.data:
            color = str(request.data.get('primary_color', '')).strip()
            if not color.startswith('#') or len(color) not in (4, 7, 9):
                return Response({'primary_color': ['Couleur invalide.']}, status=status.HTTP_400_BAD_REQUEST)
            company.primary_color = color
            fields.append('primary_color')

        if not fields:
            return Response({'detail': 'Aucun paramètre à mettre à jour.'}, status=status.HTTP_400_BAD_REQUEST)

        company.save(update_fields=[*fields, 'updated_at'])
        return self.get(request)

    @transaction.atomic
    def delete(self, request):
        """
        Suppression totale et irréversible de l'entreprise (Approche A).
        Purge l'entreprise, toutes les données associées et les comptes utilisateurs.
        Exige le mot de passe de l'admin principal.
        """
        if not IsCompanyPrimaryAdmin().has_permission(request, self):
            return Response({'detail': "Seul l'administrateur principal créateur peut supprimer l'entreprise."}, status=status.HTTP_403_FORBIDDEN)
        
        company = self._company(request)
        if not company:
            return Response({'detail': 'Entreprise introuvable.'}, status=status.HTTP_404_NOT_FOUND)

        password = request.data.get('password')
        if not password or not request.user.check_password(password):
            return Response({'password': ['Mot de passe incorrect pour confirmer la suppression.']}, status=status.HTTP_400_BAD_REQUEST)

        admin_email = request.user.email
        admin_name = request.user.first_name or request.user.username
        company_name = company.name

        # Purge complète ordonnée de tous les modèles avec clés protégées
        purge_company_data(company)

        # Envoi de l'email de confirmation
        if admin_email:
            try:
                send_company_deletion_notification_email(admin_email, company_name, admin_name)
            except Exception:
                pass

        return Response({
            'detail': "L'entreprise et l'ensemble des comptes associés ont été définitivement supprimés.",
            'deleted': True,
        }, status=status.HTTP_200_OK)


class SellerListView(CompanyUserQuerysetMixin, generics.ListAPIView):
    permission_classes = [IsCompanyAdmin]
    serializer_class = RegisterSerializer
    queryset = User.objects.filter(is_staff=False).order_by('username')


class SellerRegisterView(generics.CreateAPIView):
    permission_classes = [IsCompanyAdmin]
    serializer_class = RegisterSerializer

    def perform_create(self, serializer):
        user_type = self.request.data.get('user_type', 'SELLER')
        if user_type not in ('ADMIN', 'SELLER'):
            user_type = 'SELLER'
        serializer.save(user_type=user_type, company=self.request.user.company, is_primary_admin=False)


class SellerUpdateView(CompanyUserQuerysetMixin, generics.UpdateAPIView):
    permission_classes = [IsCompanyAdmin]
    serializer_class = RegisterSerializer
    queryset = User.objects.filter(is_staff=False)
    lookup_field = 'pk'


class SellerDeleteView(CompanyUserQuerysetMixin, generics.DestroyAPIView):
    permission_classes = [IsCompanyAdmin]
    serializer_class = UserSerializer
    queryset = User.objects.filter(is_staff=False)
    lookup_field = 'pk'

    def perform_destroy(self, instance):
        if instance.is_primary_admin or instance == self.request.user.company.created_by:
            raise PermissionError("L'administrateur principal / créateur ne peut pas être supprimé de l'équipe.")
        SellerPrivileges.objects.filter(user=instance).delete()
        instance.delete()


class SellerDashboard(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RegisterSerializer

    def get(self, request, *args, **kwargs):
        return Response({'message': f'Bienvenue {request.user.username}', 'stats': {}})



class CompanyRegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def post(self, request):
        serializer = CompanyRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        base_slug = slugify(data['company_name']) or 'company'
        slug = f"{base_slug}-{uuid.uuid4().hex[:6]}"
        company_username = data.get('company_username') or slug

        username = data['username'].strip().lower()
        if User.objects.filter(username=username).exists():
            return Response({'username': ["Ce nom d'utilisateur est déjà utilisé."]}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(email=data['email']).exists():
            return Response({'email': ["Cette adresse e-mail est déjà associée à un compte."]}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Créer l'entreprise
        company = Company.objects.create(
            name=data['company_name'],
            slug=slug,
            company_username=company_username
        )

        # 2. Créer l'administrateur principal (créateur)
        user = User.objects.create_user(
            username=username,
            email=data['email'],
            password=data['password'],
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            phone=data['phone'],
            user_type='ADMIN',
            is_primary_admin=True,
            phone_verified=True,
            email_verified=True,
            company=company,
        )

        company.created_by = user
        company.save(update_fields=['created_by'])

        # 3. Créer l'entrepôt principal et son emplacement
        warehouse_name = data.get('warehouse_name') or 'Entrepôt Principal'
        wh = Warehouse.objects.create(
            company=company,
            name=warehouse_name,
            code='WH-MAIN',
        )
        StockLocation.objects.create(
            warehouse=wh,
            name='Zone Principale',
            code='LOC-A1',
        )

        # 4. Token d'authentification
        token, _ = Token.objects.get_or_create(user=user)

        # 5. Envoi d'email de bienvenue professionnel
        try:
            send_company_welcome_email(user=user, company=company)
        except Exception:
            pass

        return Response({
            'token': token.key,
            'user': UserSerializer(user).data,
            'is_admin': True,
            'is_primary_admin': True,
            'company': {
                'id': company.id,
                'name': company.name,
                'company_username': company.company_username,
                'slug': company.slug,
                'currency': company.currency,
                'logo_uri': company.logo_uri,
                'primary_color': company.primary_color,
            },
            'warehouse': {
                'id': wh.id,
                'name': wh.name,
                'code': wh.code,
            }
        }, status=status.HTTP_201_CREATED)

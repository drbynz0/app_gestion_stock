import uuid
from django.db import transaction
from django.utils.text import slugify
from django.contrib.auth import authenticate
from django.http import Http404
from rest_framework import generics, permissions, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User, SellerPrivileges, Company
from .permissions import IsSeller
from .permissions_company import IsCompanyAdmin, IsPlatformAdmin
from .tenancy import IsCompanyUser
from .serializers import UserSerializer, RegisterSerializer, CompanyRegisterSerializer, CompanyAdminSerializer, CompanyDetailSerializer
from stock.models import Warehouse, StockLocation


class CompanyUserQuerysetMixin:
    def get_queryset(self):
        if self.request.user.user_type == 'PLATFORM_ADMIN' or self.request.user.is_superuser:
            return super().get_queryset()
        return super().get_queryset().filter(company=self.request.user.company)


class UserViewSet(CompanyUserQuerysetMixin, viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    # La devise et l'identité doivent être lisibles par tous les membres afin
    # que les montants restent cohérents. Leur modification reste réservée à
    # l'administrateur de l'entreprise.
    permission_classes = [IsCompanyUser]

    def perform_create(self, serializer):
        user = serializer.save(company=self.request.user.company)
        if user.is_seller:
            SellerPrivileges.objects.get_or_create(user=user)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        user = authenticate(username=request.data.get('username'), password=request.data.get('password'))
        if user is None or not user.company_id or not user.company.is_active:
            return Response({'error': 'Identifiants incorrects'}, status=status.HTTP_401_UNAUTHORIZED)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'user': UserSerializer(user).data, 'is_admin': user.user_type == 'ADMIN'})


class SellerRegisterView(generics.CreateAPIView):
    permission_classes = [IsCompanyAdmin]
    serializer_class = RegisterSerializer

    def perform_create(self, serializer):
        serializer.save(user_type='SELLER', company=self.request.user.company)


class ProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RegisterSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        if 'user_type' in request.data or 'company' in request.data:
            return Response({'error': 'Ce champ ne peut pas être modifié depuis votre profil.'}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)


class CompanySettingsView(APIView):
    """Paramètres métier propres au tenant ; jamais modifiables par un vendeur."""
    permission_classes = [IsCompanyAdmin]
    supported_currencies = {'MAD', 'EUR', 'USD', 'XOF', 'XAF', 'GBP'}

    def _company_or_error(self, request):
        if not request.user.company_id:
            return None
        return request.user.company

    def get(self, request):
        company = self._company_or_error(request)
        if not company:
            return Response({'detail': 'Les paramètres d’entreprise ne sont pas disponibles pour un administrateur plateforme.'}, status=status.HTTP_403_FORBIDDEN)
        return Response({'id': company.id, 'name': company.name, 'currency': company.currency, 'logo_uri': company.logo_uri, 'primary_color': company.primary_color})

    def patch(self, request):
        if not IsCompanyAdmin().has_permission(request, self):
            return Response({'detail': 'Vous n’êtes pas autorisé à modifier les paramètres de l’entreprise.'}, status=status.HTTP_403_FORBIDDEN)
        company = self._company_or_error(request)
        if not company:
            return Response({'detail': 'Les paramètres d’entreprise ne sont pas disponibles pour un administrateur plateforme.'}, status=status.HTTP_403_FORBIDDEN)
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
                return Response({'name': ['Le nom de l’entreprise est requis.']}, status=status.HTTP_400_BAD_REQUEST)
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


class CompanyAdminViewSet(viewsets.ModelViewSet):
    """Platform-only tenant governance: review, suspend or update a company."""
    queryset = Company.objects.all().order_by('-created_at')
    serializer_class = CompanyAdminSerializer
    permission_classes = [IsPlatformAdmin]
    http_method_names = ['get', 'patch', 'head', 'options']

    def get_serializer_class(self):
        return CompanyDetailSerializer if self.action == 'retrieve' else CompanyAdminSerializer


class SellerDashboard(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RegisterSerializer

    def get(self, request, *args, **kwargs):
        return Response({'message': f'Bienvenue {request.user.username}', 'stats': {}})


class SellerListView(CompanyUserQuerysetMixin, generics.ListAPIView):
    permission_classes = [IsCompanyAdmin]
    serializer_class = RegisterSerializer
    queryset = User.objects.filter(is_staff=False).order_by('username')


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
        SellerPrivileges.objects.filter(user=instance).delete()
        instance.delete()


class CompanyRegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def post(self, request):
        serializer = CompanyRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        base_slug = slugify(data['company_name']) or 'company'
        slug = f"{base_slug}-{uuid.uuid4().hex[:6]}"

        if User.objects.filter(username=data['username']).exists():
            return Response({'username': ["Ce nom d'utilisateur est déjà utilisé."]}, status=status.HTTP_400_BAD_REQUEST)
        if data.get('email') and User.objects.filter(email=data['email']).exists():
            return Response({'email': ["Cette adresse e-mail est déjà associée à un compte."]}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Créer la compagnie
        company = Company.objects.create(name=data['company_name'], slug=slug)

        # 2. Créer le compte Administrateur
        user = User.objects.create_user(
            username=data['username'],
            email=data.get('email', ''),
            password=data['password'],
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            phone=data.get('phone', ''),
            user_type='ADMIN',
            company=company,
        )

        # 3. Créer l'entrepôt principal et l'emplacement par défaut
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

        return Response({
            'token': token.key,
            'user': UserSerializer(user).data,
            'company': {
                'id': company.id,
                'name': company.name,
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

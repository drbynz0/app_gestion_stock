from rest_framework import generics, permissions, status,viewsets # type: ignore
from rest_framework.views import APIView # type: ignore
from rest_framework.response import Response # type: ignore
from rest_framework.authtoken.models import Token # type: ignore
from django.contrib.auth import authenticate # type: ignore
from .models import User, SellerPrivileges
from .serializers import UserSerializer, LoginSerializer, RegisterSerializer
from .permissions import IsSeller


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        if user.is_seller:
            SellerPrivileges.objects.create(user=user)

class LoginView(APIView):
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        
        username = request.data.get('username')
        password = request.data.get('password')
        
        user = authenticate(username=username, password=password)
        
        if user is not None:        
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data,
                'is_admin': user.is_staff,  # Pour identifier les admins (superusers)
            })
        else:
            return Response({'error': 'Identifiants incorrects'}, status=status.HTTP_401_UNAUTHORIZED)
        

class SellerRegisterView(generics.CreateAPIView):
    permission_classes = [permissions.IsAdminUser]  # Assurez-vous que seuls les admins peuvent créer des vendeurs
    serializer_class = RegisterSerializer
    
    def perform_create(self, serializer):
        serializer.save(user_type='SELLER')
        

class ProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RegisterSerializer
    
    def get_object(self):
        return self.request.user

    def get_serializer_context(self):
        """Passe le contexte de la requête au serializer"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Ne permet pas la modification du rôle via cette vue
        if 'user_type' in request.data:
            return Response(
                {"error": "Vous ne pouvez pas modifier votre rôle via cette interface"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

class SellerDashboard(generics.RetrieveAPIView):
    permission_classes = [IsSeller, permissions.IsAdminUser]  # Assurez-vous que seuls les vendeurs et les admins peuvent accéder à cette vue
    serializer_class = RegisterSerializer
    
    def get(self, request, *args, **kwargs):
        # Exemple de vue réservée aux vendeurs
        return Response({
            'message': f'Bienvenue vendeur {request.user.username}',
            'stats': {}  # Ajoutez des stats métiers ici
        })
        
class SellerListView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = RegisterSerializer
    
    def get_queryset(self):
        return User.objects.filter(is_staff=False).order_by('username')

class SellerUpdateView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = RegisterSerializer
    queryset = User.objects.filter(is_staff=False)
    lookup_field = 'pk'  # ou 'id' selon ta route

    def get_object(self):
        seller = super().get_object()
        if seller.is_staff:
            raise Response({'error': 'Utilisateur non vendeur'}, status=status.HTTP_400_BAD_REQUEST)
        return seller
    
class SellerDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = UserSerializer
    queryset = User.objects.filter(is_staff=False)
    lookup_field = 'pk'

    def perform_destroy(self, instance):
        # Supprimer ses privilèges s'ils existent
        SellerPrivileges.objects.filter(user=instance).delete()
        instance.delete()



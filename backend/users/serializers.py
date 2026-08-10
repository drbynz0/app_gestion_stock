from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken  # Ajout
from .models import SellerPrivileges

User = get_user_model()

class SellerPrivilegesSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellerPrivileges
        fields = [
            'add_product', 'edit_product', 'delete_product',
            'add_order', 'edit_order', 'delete_order',
            'add_client', 'edit_client', 'delete_client',
            'add_supplier', 'edit_supplier', 'delete_supplier',
            'add_category', 'edit_category', 'delete_category',
        ]

class UserSerializer(serializers.ModelSerializer):
    privileges = SellerPrivilegesSerializer(read_only=True)
    token = serializers.SerializerMethodField()  # Modifié

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'token', 'user_type', 'phone', 'privileges']
    
    def get_token(self, obj):
        refresh = RefreshToken.for_user(obj)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(**data)
        if user and user.is_active:
            refresh = RefreshToken.for_user(user)  # Génération du token
            user.token = str(refresh.access_token)  # Mise à jour du token
            user.save()
            return {
                'user': user,
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            }
        raise serializers.ValidationError("Identifiants incorrects")

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    privileges = SellerPrivilegesSerializer(required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'password', 
                  'token', 'user_type', 'phone', 'is_staff', 'is_admin', 'last_login', 'date_joined', 'privileges']
        extra_kwargs = {
            'password': {'write_only': True},
            'token': {'read_only': True}  # Ajout
        }

    def create(self, validated_data):
        privileges_data = validated_data.pop('privileges', None)
        
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            user_type=validated_data.get('user_type', ''),
            phone=validated_data.get('phone', '')
        )

        # Génération du token après création
        refresh = RefreshToken.for_user(user)
        user.token = str(refresh.access_token)
        user.save()

        if user.user_type == 'SELLER':
            SellerPrivileges.objects.create(
                user=user,
                **(privileges_data or {})
            )

        return user

    def update(self, instance, validated_data):
        privileges_data = validated_data.pop('privileges', None)

        for attr, value in validated_data.items():
            if attr == 'password':
                instance.set_password(value)
            else:
                setattr(instance, attr, value)
        
        # Régénération du token lors de la mise à jour
        refresh = RefreshToken.for_user(instance)
        instance.token = str(refresh.access_token)
        instance.save()

        if instance.user_type == 'SELLER' and privileges_data:
            try:
                privileges = SellerPrivileges.objects.get(user=instance)
                for attr, value in privileges_data.items():
                    setattr(privileges, attr, value)
                privileges.save()
            except SellerPrivileges.DoesNotExist:
                SellerPrivileges.objects.create(user=instance, **privileges_data)

        return instance
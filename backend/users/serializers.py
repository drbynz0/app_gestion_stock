from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from .models import SellerPrivileges, Company, validate_username_format

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
    token = serializers.SerializerMethodField()
    company_name = serializers.CharField(source='company.name', read_only=True)
    is_primary_admin = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email', 'token', 'user_type', 'phone', 
            'is_primary_admin', 'phone_verified', 'email_verified', 'two_factor_enabled',
            'company_id', 'company_name', 'privileges'
        ]
    
    def get_is_primary_admin(self, obj):
        return bool(obj.is_primary_admin or (obj.company and obj.company.created_by_id == obj.id))

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
            refresh = RefreshToken.for_user(user)
            user.token = str(refresh.access_token)
            user.save()
            return {
                'user': user,
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            }
        raise serializers.ValidationError("Identifiants incorrects.")


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    privileges = SellerPrivilegesSerializer(required=False)
    username = serializers.CharField(validators=[validate_username_format])

    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email', 'password', 
            'token', 'user_type', 'phone', 'is_staff', 'is_admin', 'is_primary_admin',
            'phone_verified', 'email_verified', 'two_factor_enabled',
            'last_login', 'date_joined', 'privileges'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'token': {'read_only': True}
        }

    def validate_username(self, value):
        val = value.strip().lower()
        validate_username_format(val)
        return val

    def create(self, validated_data):
        privileges_data = validated_data.pop('privileges', None)
        user_type = validated_data.get('user_type', 'SELLER')
        
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data.get('password'),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            user_type=user_type,
            phone=validated_data.get('phone', ''),
            company=validated_data.get('company')
        )

        refresh = RefreshToken.for_user(user)
        user.token = str(refresh.access_token)
        user.save()

        # Si c'est un vendeur, on initialise ses privilèges
        if user.user_type == 'SELLER':
            SellerPrivileges.objects.create(
                user=user,
                **(privileges_data or {})
            )

        return user

    def update(self, instance, validated_data):
        privileges_data = validated_data.pop('privileges', None)
        validated_data.pop('username', None)  # Le nom d'utilisateur NE PEUT JAMAIS être modifié

        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        refresh = RefreshToken.for_user(instance)
        instance.token = str(refresh.access_token)
        instance.save()

        if instance.user_type == 'SELLER' and privileges_data is not None:
            privileges, _ = SellerPrivileges.objects.get_or_create(user=instance)
            for attr, value in privileges_data.items():
                setattr(privileges, attr, value)
            privileges.save()

        return instance


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Mise à jour et consultation du profil par l'utilisateur connecté."""
    password = serializers.CharField(write_only=True, required=False)
    privileges = SellerPrivilegesSerializer(read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    is_primary_admin = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email', 'phone', 'password',
            'user_type', 'is_primary_admin', 'two_factor_enabled', 'phone_verified',
            'email_verified', 'company_id', 'company_name', 'privileges'
        ]
        read_only_fields = [
            'id', 'username', 'user_type', 'is_primary_admin', 'company_id', 'company_name'
        ]

    def get_is_primary_admin(self, obj):
        return bool(obj.is_primary_admin or (obj.company and obj.company.created_by_id == obj.id))

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class CompanyRegisterSerializer(serializers.Serializer):
    company_name = serializers.CharField(max_length=160)
    company_username = serializers.CharField(max_length=100, required=False, allow_blank=True, validators=[validate_username_format])
    username = serializers.CharField(max_length=150, validators=[validate_username_format])
    email = serializers.EmailField(required=True)
    phone = serializers.CharField(max_length=30, required=True)
    password = serializers.CharField(write_only=True, min_length=6)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default='')
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default='')
    warehouse_name = serializers.CharField(max_length=120, required=False, default='Entrepôt Principal')

    def validate_username(self, value):
        val = value.strip().lower()
        validate_username_format(val)
        return val

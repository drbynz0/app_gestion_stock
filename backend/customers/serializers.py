from rest_framework import serializers # type: ignore
from .models import Customer

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'
        extra_kwargs = {
            'email': {'required': False, 'allow_null': True, 'allow_blank': True},
            'phone_number': {'required': False, 'allow_blank': True},
            'ice': {'required': False, 'allow_null': True, 'allow_blank': True},
            'company': {'read_only': True},
        }

    def validate_email(self, value):
        if not value or not str(value).strip():
            return None
        return str(value).strip().lower()

    def validate_ice(self, value):
        if not value or not str(value).strip():
            return None
        return str(value).strip()

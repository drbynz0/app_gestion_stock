from rest_framework import serializers # type: ignore
from .models import Customer

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'
        extra_kwargs = {
            'email': {'required': True},
            'phone_number': {'required': True}
        }

    def validate_ice(self, value):
        if value and len(value) != 15:
            raise serializers.ValidationError("L'ICE doit contenir exactement 15 caractères")
        return value
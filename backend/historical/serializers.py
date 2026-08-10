from rest_framework import serializers # type: ignore
from .models import Historical

class HistoricalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Historical
        fields = '__all__'

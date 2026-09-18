"""Assistant Groq en lecture seule et isolé par entreprise."""
import logging
from decimal import Decimal

import httpx
from django.conf import settings
from django.db.models import Count, Sum
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from customers.models import Customer
from discounts.models import Discount
from externalOrders.models import ExternalOrder
from internalOrders.models import InternalOrder
from products.models import Product
from stock.models import InventorySession
from suppliers.models import Supplier
from users.models import Company
logger = logging.getLogger(__name__)
MAX_HISTORY = 8
DEFAULT_GROQ_MODEL = 'qwen/qwen3.8-27b'


def get_groq_model_name():
    return getattr(settings, 'GROQ_MODEL', DEFAULT_GROQ_MODEL) or DEFAULT_GROQ_MODEL


def money(value):
    return str(value or Decimal('0'))


def company_snapshot(company):
    """Aperçu métier limité, sans PII ni accès SQL généré par le LLM."""
    products = Product.objects.filter(company=company)
    orders = InternalOrder.objects.filter(company=company)
    purchases = ExternalOrder.objects.filter(company=company)
    low_stock = list(products.filter(stock__lte=5).order_by('stock', 'name').values('name', 'code', 'stock')[:8])
    recent_products = list(products.order_by('-created_at').values_list('name', flat=True)[:6])
    stock_value = sum((p.price or 0) * p.stock for p in products.only('price', 'stock'))
    return {
        'entreprise': company.name,
        'devise': company.currency,
        'indicateurs': {
            'produits': products.count(),
            'unites_en_stock': products.aggregate(total=Sum('stock'))['total'] or 0,
            'valeur_stock_estimee': money(stock_value),
            'clients': Customer.objects.filter(company=company).count(),
            'fournisseurs': Supplier.objects.filter(company=company).count(),
            'promotions_actives': Discount.objects.filter(company=company, validity='active').count(),
            'inventaires_en_cours': InventorySession.objects.filter(company=company, status__in=['DRAFT', 'COUNTING']).count(),
            'ventes': orders.count(),
            'chiffre_affaires_commandes': money(orders.aggregate(total=Sum('total_price'))['total']),
            'encaisse': money(orders.aggregate(total=Sum('total_paid'))['total']),
            'reste_a_encaisser': money(orders.aggregate(total=Sum('remaining_price'))['total']),
            'achats_fournisseurs': money(purchases.aggregate(total=Sum('total_price'))['total']),
            'reste_a_payer_fournisseurs': money(purchases.aggregate(total=Sum('remaining_price'))['total']),
        },
        'alertes_stock_faible': low_stock,
        'nouveaux_produits': recent_products,
        'genere_le': timezone.now().isoformat(),
    }


def platform_snapshot():
    return {
        'portefeuille_plateforme': {
            'entreprises': Company.objects.count(),
            'entreprises_actives': Company.objects.filter(is_active=True).count(),
            'utilisateurs': Company.objects.aggregate(total=Count('users'))['total'] or 0,
        },
        'entreprises': [company_snapshot(company) for company in Company.objects.order_by('name')[:30]],
    }


class ChatInputSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=1200, trim_whitespace=True)
    company_id = serializers.IntegerField(required=False, min_value=1, allow_null=True)
    history = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_empty=True,
        max_length=MAX_HISTORY,
    )

    def validate_question(self, value):
        if not value.strip():
            raise serializers.ValidationError('Votre question ne peut pas être vide.')
        return value.strip()

    def validate_history(self, value):
        clean_history = []
        for item in value:
            role = item.get('role')
            content = item.get('content')
            if role not in ('USER', 'ASSISTANT') or not isinstance(content, str) or not content.strip():
                raise serializers.ValidationError('Historique de conversation invalide.')
            clean_history.append({
                'role': 'user' if role == 'USER' else 'assistant',
                'content': content.strip()[:1200],
            })
        return clean_history


class AssistantAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def resolve_company(self, request, company_id):
        is_platform = request.user.user_type == 'PLATFORM_ADMIN' or request.user.is_superuser
        if is_platform:
            if company_id is None:
                return None
            try:
                return Company.objects.get(pk=company_id)
            except Company.DoesNotExist:
                raise serializers.ValidationError({'company_id': 'Entreprise introuvable.'})
        if company_id is not None and company_id != request.user.company_id:
            raise serializers.ValidationError({'company_id': 'Accès à cette entreprise refusé.'})
        if not request.user.company_id:
            raise serializers.ValidationError({'company_id': 'Aucune entreprise n’est associée à ce compte.'})
        return request.user.company


class AssistantChatView(AssistantAPIView):
    def post(self, request):
        payload = ChatInputSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        company = self.resolve_company(request, payload.validated_data.get('company_id'))
        question = payload.validated_data['question']
        history = payload.validated_data.get('history', [])
        context = company_snapshot(company) if company else platform_snapshot()
        system = (
            "Tu es StockPro IA, conseiller de gestion d'entreprise. Réponds exclusivement en français, clairement, de façon structurée et direct. "
            "Tu reçois un contexte en lecture seule : ne prétends jamais modifier des données, exécuter une action ou consulter une autre source. "
            "Analyse les chiffres, signale les limites des données et propose des stratégies concrètes si c'est demandé. "
            "Ne donne pas des reponses longues si ce n'est pas necessaires."
            "Ne fournis ni SQL, ni données personnelles, ni moyens de contourner les permissions."
        )
        messages = [{'role': 'system', 'content': system + '\n\nCONTEXTE AUTORISÉ:\n' + str(context)}]
        messages.extend(history)
        messages.append({'role': 'user', 'content': question})
        if not settings.GROQ_API_KEY or not settings.GROQ_API_URL:
            return Response({'detail': 'Le service IA n’est pas configuré.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        try:
            result = httpx.post(settings.GROQ_API_URL, headers={'Authorization': f'Bearer {settings.GROQ_API_KEY}', 'Content-Type': 'application/json'}, json={
                'model': get_groq_model_name(), 'messages': messages, 'temperature': 0.35, 'max_tokens': 900,
            }, timeout=35.0)
            result.raise_for_status()
            answer = result.json()['choices'][0]['message']['content'].strip()
        except (httpx.HTTPError, KeyError, IndexError, TypeError):
            logger.exception('Groq assistant request failed')
            return Response({'detail': 'Le service IA est temporairement indisponible.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response({'answer': answer, 'scope': company.name if company else 'Toutes les entreprises'})

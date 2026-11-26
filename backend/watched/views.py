from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import WatchedItem
from .serializers import WatchedItemSerializer


class WatchedListView(APIView):
    """
    GET /api/watched/           → liste des favoris de l'utilisateur connecté
    GET /api/watched/?item_type=product  → filtre par type
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = WatchedItem.objects.filter(user=request.user)
        item_type = request.query_params.get('item_type')
        if item_type:
            qs = qs.filter(item_type=item_type)
        serializer = WatchedItemSerializer(qs, many=True)
        return Response(serializer.data)


class WatchedToggleView(APIView):
    """
    POST /api/watched/toggle/
    Body: { item_type, item_id, item_label, item_meta? }
    → crée si absent, supprime si déjà présent
    → retourne { watching: bool, item?: WatchedItem }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        item_type = request.data.get('item_type')
        item_id = request.data.get('item_id')
        item_label = request.data.get('item_label', '')
        item_meta = request.data.get('item_meta', '')

        if not item_type or item_id is None:
            return Response(
                {'error': 'item_type et item_id sont requis'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            item_id = int(item_id)
        except (ValueError, TypeError):
            return Response({'error': 'item_id doit être un entier'}, status=status.HTTP_400_BAD_REQUEST)

        existing = WatchedItem.objects.filter(
            user=request.user,
            item_type=item_type,
            item_id=item_id,
        ).first()

        if existing:
            existing.delete()
            return Response({'watching': False})
        else:
            obj = WatchedItem.objects.create(
                user=request.user,
                item_type=item_type,
                item_id=item_id,
                item_label=item_label,
                item_meta=item_meta,
            )
            serializer = WatchedItemSerializer(obj)
            return Response({'watching': True, 'item': serializer.data}, status=status.HTTP_201_CREATED)

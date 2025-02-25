from rest_framework import viewsets, status
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .services import SwipeSystem
from .serializers import AnnouncementSerializer, MatchSerializer

User = get_user_model()

class SwipeViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    swipe_system = SwipeSystem()

    @action(detail=False, methods=['GET'])
    def next_cards(self, request):
        """Получение следующих карточек для свайпа"""
        admin_user = User.objects.get(id=1)
        cards = self.swipe_system.get_next_cards(admin_user.id)
        serializer = AnnouncementSerializer(cards, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['POST'])
    def swipe(self, request, pk=None):
        """Обработка свайпа"""
        direction = request.data.get('direction')
        if not direction:
            return Response({'error': 'Не указано направление свайпа'}, status=status.HTTP_400_BAD_REQUEST)
            
        admin_user = User.objects.get(id=1)
        is_match = self.swipe_system.process_swipe(
            user_id=admin_user.id,
            announcement_id=pk,
            direction=direction
        )
        
        return Response({'match': is_match}) 
from . models import Card, InventoryCard, PinnedPost, InventoryHistory
from rest_framework import generics, permissions, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.shortcuts import get_object_or_404
from apps.main.models import Post
from .services import perform_mana_transfer
from django.utils import timezone
from .serializers import (
    CardSerializers, 
    InventoryCardSerializers,
    InventoryCardCreateSerializer,
    InventoryHistorySerializer,
    PinnedPostSerializer,
    PinPostSerializer,
    UnpinPostSerializer
)
class CardListView(generics.ListAPIView):
    queryset = Card.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = CardSerializers
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    filterset_fields = ['type', 'price']
    ordering = ['-created_at']



class InventoryCardListCreateView(generics.ListCreateAPIView):
    queryset = InventoryCard.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = InventoryCardSerializers
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'end_date']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = InventoryCard.objects.filter(user=self.request.user)
        return queryset
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return InventoryCardCreateSerializer
        return InventoryCardSerializers



class InventoryHistoryView(generics.ListAPIView):
    queryset = InventoryHistory.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = InventoryHistorySerializer

    def get_queryset(self):
        user = self.request.user
        queryset = InventoryHistory.objects.filter(user=user)
        return queryset


class PinnedPostView(generics.RetrieveDestroyAPIView):
    """Показать закрепленный пост автора, либо удалить пост из закрепа"""
    queryset = PinnedPost.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PinnedPostSerializer

    # Достаем конкретный один пост автора
    def get_object(self):
        try:
            return self.request.user.pinned_post
        except PinnedPost.DoesNotExist:
            return None
        
    def retrieve(self, request, *args, **kwargs):
        pinned_post = self.get_object()
        if pinned_post:
            serializer = self.get_serializer(pinned_post)
            return Response(serializer.data)
        return Response('Нету закреп поста', status=status.HTTP_404_NOT_FOUND)
    
    def destroy(self, request, *args, **kwargs):
        pinned_post = self.get_object()
        if pinned_post:
            pinned_post.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({
                'detail': 'Нету закреп поста'
            }, status=status.HTTP_404_NOT_FOUND)
        

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def pin_post(request):
    """Закрепление поста"""
    serializer = PinPostSerializer(data=request.data, context={'request': request})

    if serializer.is_valid():
        post_id = serializer.validated_data['post_id']

        try:
            post = get_object_or_404(Post, id=post_id, status='published')

            has_card = request.user.inventary.filter(subscription_card__type = 'premium', status = 'active', subscription_card__is_active = True).exists()
            if not has_card:
                return Response('Для закрепления постов необходима активная Premium-карточка', status=status.HTTP_403_FORBIDDEN)
            
            if hasattr(request.user, 'pinned_post'):
                request.user.pinned_post.delete()
            
            pinned_post = PinnedPost.objects.create(
                user=request.user,
                post=post
            )

            response_serializer = PinnedPostSerializer(pinned_post)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
                    return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def unpin_post(request):
    """Открепление поста пользователя"""
    serializer = UnpinPostSerializer(data=request.data, context={'requst': request}) #  просто проверка есть ли у этого юзера закреп пост

    if serializer.is_valid():
        try:
            unpin_post = request.user.pinned_post
            unpin_post.delete()
            return Response({
                'message': 'Пост был откреплен'
            }, status=status.HTTP_200_OK)
        
        except PinnedPost.DoesNotExist:
            return Response({
                'error': 'No pinned post found'
            }, status=status.HTTP_404_NOT_FOUND)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_post_list(request):
    """Все посты которые закрепленные вывод списком"""
    pin_post = PinnedPost.objects.select_related(
        'post', 'post__author', 'post__category',
    ).filter(
        user__inventary__subscription_card__type = 'premium',
        user__inventary__subscription_card__is_active = True,
        user__inventary__status = 'active',
        user__inventary__end_date__gt=timezone.now(),
    )

    posts_data = []
    for pin_posts in pin_post:
        post = pin_posts.post
        posts_data.append({
            'id': post.id,
            'title': post.title,
            'description': post.description[:200] + '...' if len(post.description) > 200 else post.description,
            'image': post.image.url if post.image else None,
            'status': post.status,
            'slug': post.slug,
            'author': {
                'id': post.author.id,
                'username': post.author.username,
                'full_name': post.author.full_name,
            },
            'category': post.category.title if post.category else None,
            'tag': [tag.title for tag in post.tag.all()] if hasattr(post, 'tag') else [],
            'views_count': post.views_count,
            'comments_count': post.comments_count
        })
    return Response({
        'results': posts_data,
        'count': len(posts_data)
    })



@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def send_mana(request):
    receiver_id = request.data.get('receiver_id')
    amount = request.data.get('amount')

    result = perform_mana_transfer(request.user, receiver_id, amount) # в данный момент стоият позицыонные аргументы но так же можно использовать именнованые: sender=request.user, receiver_id=receiver_id, amount=amount

    if result['success']:
        return Response({'message': result['message']}, status=status.HTTP_200_OK)
    else:
        return Response({'error': result['message']}, status=status.HTTP_400_BAD_REQUEST)

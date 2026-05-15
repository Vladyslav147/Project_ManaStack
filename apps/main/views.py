from . models import Category, Post, Tag
from rest_framework import generics, permissions, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.shortcuts import get_object_or_404

from .serializer import(
    TagShortSerializer,
    CategorySerializer,
    PostListSerializer,
    PostDetailSerializer,
    PostCreateUpdateSerializer,
    TagListSerializer
)

from .permissions import IsAuthorOrReadOnly


class TagListView(generics.ListAPIView):
    """Вывод тегов"""
    queryset = Tag.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = TagListSerializer

class CategoryListView(generics.ListAPIView):
    """Список категорий на сайте"""
    queryset = Category.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = CategorySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['title', 'created_at']


class PostListCreateView(generics.ListCreateAPIView):
    """Список постов и создание поста"""
    queryset = Post.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    serializer_class = PostListSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['views_count', 'created_at']
    filterset_fields = ['title', 'description']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = Post.objects.select_related('author', 'category')

        if not self.request.user.is_authenticated:
            queryset = Post.objects.filter(status='published')
        else:
            queryset = queryset.filter(
                Q(status='published') | Q(author=self.request.user) 
            )
        return queryset
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PostCreateUpdateSerializer
        return PostListSerializer
    

class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Детальный пост"""
    queryset = Post.objects.select_related('author', 'category')
    permission_classes = [IsAuthorOrReadOnly]
    serializer_class = PostDetailSerializer
    lookup_field = 'slug'

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return PostCreateUpdateSerializer
        return PostDetailSerializer
    
    def retrieve(self, request, *args, **kwargs): # он срабатывает когда срабатывает метод детальной информации
        instance = self.get_object()
        if request.method == 'GET':
            instance.increment_views()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    

class MyPostView(generics.ListAPIView):
    """Мои посты"""
    queryset = Post.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PostListSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'status']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'views_count']
    ordering = ['-created_at']

    def get_queryset(self):
        return Post.objects.filter(
            author = self.request.user
        ).select_related('author', 'category')
     


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def post_by_category(request, category_slug):
    """Посты определенной категории"""
    category = get_object_or_404(Category, slug=category_slug)
    posts = Post.objects.with_card_info().filter(category=category, status='published')

    from django.db.models import Case, When, Value, DateTimeField, BooleanField, F
    from django.utils import timezone
    
    posts = posts.annotate(
        effective_date=Case( # подставить дату закрпление
            When(
                pin_info__isnull = False,
                pin_info__user__inventary__subscription_card__type = 'premium',
                pin_info__user__inventary__end_date__gt=timezone.now(),
                then=F('pin_info__pinned_at'),
            ),
            default=F('created_at'),
            output_field=DateTimeField()
        ),
        is_pinned_flag=Case( # подставить Try если пост закреплен
            When(
                pin_info__isnull = False,
                pin_info__user__inventary__subscription_card__type = 'premium',
                pin_info__user__inventary__end_date__gt=timezone.now(),
                then=Value(True),
            ),
            default=Value(False),
            output_field=BooleanField()
        ),
    ).order_by('-is_pinned_flag', 'effective_date')

    serializer = PostListSerializer(posts, many=True, context={'request': request})

    return Response({
        'category': CategorySerializer(category).data,
        'posts': serializer.data,
        'posts_count': len(serializer.data)
    })



@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def popular_posts(request):
    """Топ 10 популярных постов"""
    posts = Post.objects.filter(status='published').select_related('author', 'category').prefetch_related('tag').order_by('-views_count')[:10]

    serializer = PostListSerializer(posts, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def recent_posts(request):
    posts = Post.objects.filter(status='published').select_related('author', 'category').prefetch_related('tag').order_by('created_at')[:10]

    serializer = PostListSerializer(posts, many=True, context={'request': request})
    return Response(serializer.data)
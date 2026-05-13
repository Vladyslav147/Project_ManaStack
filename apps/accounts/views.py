from rest_framework import status, generics, permissions, permissions, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django.contrib.auth import login
from apps.main.permissions import IsAuthorOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend

from .models import User
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    UserUpdateSerializer,
    UsersListSerializer
)

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save() # Уже создался пользователь он уже в базе мы вызвали created  в нутри erializer который сделал сохранение и тут уже в переменной user лежыт пользователь с его данными маной имя id и так далее
        
        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserProfileSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'Пользователь был зарегистрирован',
        }, status=status.HTTP_201_CREATED)
    

class LoginView(generics.GenericAPIView):
    serializer_class = UserLoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        login(request, user)
        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserProfileSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'Пользователь был залогинен',
        }, status=status.HTTP_200_OK)
    


class ProfileView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthorOrReadOnly]
    lookup_field = 'id'
    
    def get_serializer_class(self):
        if self.request.method == 'PUT' or self.request.method == 'PATCH':
            return UserUpdateSerializer
        return UserProfileSerializer


class UsersListView(generics.ListAPIView):
    """Вывод пользователей всех и поиск по их нику почте и т.д"""
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UsersListSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['email', 'first_name', 'username', 'last_name']
    
    def get_queryset(self):
        queryset = User.objects.filter(is_active=True).exclude(id=self.request.user)
        return queryset

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        return Response({
            'message': 'Вы успешно вышли'
        }, status=status.HTTP_200_OK)
    except Exception:
        return Response({'error': 'Не валидный токен'}, status=status.HTTP_400_BAD_REQUEST)
    


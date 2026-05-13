from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from .models import User
from apps.main.models import Post
from apps.main.serializer import TagShortSerializer
from apps.store.serializers import InventoryCardSerializers
from django.contrib.auth import get_user_model



class UserRegistrationSerializer(serializers.ModelSerializer):
    """Регистрацыя пользователя"""
    password = serializers.CharField(validators=[validate_password], write_only=True)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'password', 'password_confirm']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password': 'Пароль не совпадает'})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user
        


class UserLoginSerializer(serializers.Serializer):
    """Сериализатор входа логин"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                username=email,
                password=password
            )
            if not user:
                raise serializers.ValidationError('Такого пользователя нет')
            
            if not user.is_active:
                raise serializers.ValidationError('Пользователь был заблокирован')
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Пароль или Email небыли введены')
        


class UserPostsSerializer(serializers.ModelSerializer):
    tag = TagShortSerializer(many=True, read_only=True)
    class Meta:
        model = Post
        fields = ['id', 'title', 'image', 'status', 'slug', 'author', 'category', 'tag', 'created_at', 'views_count']



class UserProfileSerializer(serializers.ModelSerializer):
    """Профель пользователя"""
    full_name = serializers.ReadOnlyField()
    posts_count = serializers.SerializerMethodField()
    card_count = serializers.SerializerMethodField()
    posts = serializers.SerializerMethodField()
    card = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'avatar', 'bio', 'mana', 'rank', 'created_at', 'full_name', 'rank_name', 'posts_count','posts','card', 'card_count']
        read_only_fields = ('id', 'mana', 'rank', 'created_at')
    
    def get_posts(self, obj):
        user = self.context['request'].user
        if obj == user:
            queryset = obj.posts.all()
        else:
            queryset = obj.posts.filter(status='published')
        return UserPostsSerializer(queryset, many=True, context=self.context).data
    
    def get_card(self, obj):
        user = self.context['request'].user
        if obj == user:
            queryset = obj.inventary.all()
        else:
            queryset = obj.inventary.filter(status='active')
        return InventoryCardSerializers(queryset, many=True, context=self.context).data

    def get_posts_count(self, obj):
        request = self.context.get('request')
        user = request.user if request else None
        if obj == user:
            return obj.posts.count()
        
        return obj.posts.filter(status='published').count()
        
    def get_card_count(self, obj):
        user = self.context['request'].user
        if obj == user:
            return obj.inventary.count()
        return obj.inventary.filter(status='active').count()




class UserUpdateSerializer(serializers.ModelSerializer):
    """Обновление профеля"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'avatar', 'bio']

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
    
class UsersListSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'username', 'last_name','full_name']
        read_only_fields = ['email', 'first_name', 'username', 'last_name']

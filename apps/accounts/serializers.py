from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from .models import User

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
        


class UserProfileSerializer(serializers.ModelSerializer):
    """Профель пользователя"""
    full_name = serializers.ReadOnlyField()
    posts_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'avatar', 'bio', 'mana', 'rank', 'created_at', 'full_name', 'rank_name', 'posts_count']
        read_only_fields = ('id', 'mana', 'rank', 'created_at')
    
    def get_posts_count(self, obj):
        return obj.posts.count()



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
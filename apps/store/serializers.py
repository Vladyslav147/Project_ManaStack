from rest_framework import serializers
from .models import Card, InventoryCard, PinnedPost, InventoryHistory
from django.utils import timezone
from datetime import timedelta
from django.db import transaction


class CardSerializers(serializers.ModelSerializer):
    """Просмотр всех карточек"""
    class Meta:
        model = Card
        fields = ['id', 'name', 'description', 'avatar', 'price', 'duration_days', 'type', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']



class InventoryCardSerializers(serializers.ModelSerializer):
    """Вывод активных подписок, и информацыя под карточку на каждой подписке"""
    type_card = CardSerializers(source='subscription_card', read_only = True)
    user_info = serializers.SerializerMethodField()
    is_active = serializers.ReadOnlyField()
    days_remaining = serializers.ReadOnlyField()

    class Meta:
        model = InventoryCard
        fields = ['id', 'user', 'subscription_card', 'status', 'start_date', 'end_date', 'created_at', 'type_card', 'user_info', 'is_active', 'days_remaining']
        read_only_fields = ['status', 'start_date', 'end_date', 'type_card', 'user_info', 'is_active']

    def get_user_info(self, obj):
        user = obj.user
        return {
            'id': user.id,
            'username': user.username,
            'full_name': user.full_name,
            'email': user.email,
        }
    

class InventoryCardCreateSerializer(serializers.ModelSerializer):
    """Покупка карточки"""
    class Meta:
        model = InventoryCard
        fields = ['subscription_card']
    
    def validate_subscription_card(self, value):
        if not value.is_active:
            raise serializers.ValidationError('Карточка не активна в данный момент')
        
        user = self.context['request'].user
        if user.mana < value.price:
            raise serializers.ValidationError('У вас не достаточно маны') 
        
        return value
    
    @transaction.atomic
    def create(self, validated_data):
        card = validated_data['subscription_card']
        user = self.context['request'].user

        user.mana -= card.price
        user.save()

        validated_data['user'] = user
        validated_data['status'] = 'active'
        validated_data['start_date'] = timezone.now()
        validated_data['end_date'] = timezone.now() + timedelta(days=card.duration_days)
        inventory_card = super().create(validated_data)

        InventoryHistory.objects.create(
            user=user,
            card=inventory_card,
            mana_amount=-card.price,
            status='buy_card',
            description= f'Пользователь {user.username}, купил карточку - {card.name}'
        )
        return inventory_card


    
class PinnedPostSerializer(serializers.ModelSerializer):
    """Создание пин поста, и вывод всех закрепов"""
    post_info = serializers.SerializerMethodField()

    class Meta:
        model = PinnedPost
        fields = ['id', 'user', 'post', 'pinned_at','post_info']
        read_only_fields = ['id', 'pinned_at']

    def get_post_info(self, obj):
        return {
            'id': obj.post.id,
            'title': obj.post.title,
            'description': obj.post.description,
            'image': obj.post.image.url if obj.post.image else None,
            'status': obj.post.status,
            'slug': obj.post.slug,
            'views_count': obj.post.views_count,
        }
    
    def validate_post(self, value):
        user = self.context['request'].user
        if value.user != user:
            raise serializers.ValidationError('Можна закрепить только свои посты')
        
        if value.status != 'published':
            raise serializers.ValidationError('Пост должен быть опубликован')
        return value
    
    def validate(self, attrs):
        user = self.context['request'].user

        has_card = user.inventary.filter(subscription_card__type = 'premium', status = 'active', subscription_card__is_active = True).exists()
        if not has_card:
            raise serializers.ValidationError({
                'error': 'Для закрепления постов необходима активная Premium-карточка'
            })
        return attrs
        


class InventoryHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = InventoryHistory
        fields = ['id', 'user', 'card', 'mana_amount', 'status', 'description', 'created_at']
        read_only_fields = ['id', 'created_at', 'mana_amount', 'status', 'description']



class PinPostSerializer(serializers.Serializer):
    post_id = serializers.IntegerField()

    def validate_post_id(self, value):
        from apps.main.models import Post

        try:
            post = Post.objects.get(id=value, status = 'published')
        except Post.DoesNotExist:
            raise serializers.ValidationError('Пост не найден или не опубликован')
        
        user = self.context['request'].user
        if post.author != user:
            raise serializers.ValidationError('Пост должен пренадлежать автору')
        return value
    
    def validate(self, attrs):
        user = self.context['request'].user
        has_card = user.inventary.filter(subscription_card__type = 'premium', status = 'active', subscription_card__is_active = True).exists()
        if not has_card:
            raise serializers.ValidationError('Для закрепления постов необходима активная Premium-карточка')
        return attrs



class UnpinPostSerializer(serializers.Serializer):
    """Сериализатор для открепления поста"""

    def validate(self, attrs):
        user = self.context['request'].user

        if not hasattr(user, 'pinned_post'):
            raise serializers.ValidationError('Нету закреп поста')
        return attrs
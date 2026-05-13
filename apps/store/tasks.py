from celery import shared_task
from django.utils import timezone
from .models import PinnedPost, InventoryCard, InventoryHistory
from django.db import transaction
from django.contrib.auth import get_user_model
from django.db.models import F

@shared_task
def check_expired_card():
    """Проверка на истекшые сроки карточек"""
    now = timezone.now()

    # Достать все карточки у каоторых закнчился срок и они активные
    card_expired = InventoryCard.objects.filter(
        status = 'active',
        subscription_card__type = 'premium',
        end_date__lt = now
    ).select_related('user', 'user__pinned_post')

    card_expired_count = 0
    pinned_post_remove = 0

    with transaction.atomic():
        for card in card_expired:
            user = card.user
            
            card_expired_count += 1

            InventoryHistory.objects.create(
                user=user,
                card=card,
                status='end_card', 
                description=f'У пользователя  "{user.username}"  закончился срок карточки  "{card.subscription_card.name}"'
            )

            card.delete()
            
            try:
                has_other_premium = user.inventary.filter(subscription_card__type='premium', status = 'active').exists()
                if not has_other_premium:
                    if hasattr(user, 'pinned_post'):
                        user.pinned_post.delete()
                        pinned_post_remove += 1

            except PinnedPost.DoesNotExist:
                pass

    return {
        'card_expired': card_expired_count,
        'pinned_post_remove': pinned_post_remove
    }



@shared_task
def daily_mana_bonus():
    """Начисление бонусов (маны)"""
    user = get_user_model()
    users = user.objects.filter(is_active=True)

    with transaction.atomic():
        for user in users:
            user.mana = F('mana') + 20 # это прямое сохранение в базу сразу же к тому же числу какое там есть, иначе пользователь может чтото купить и в ту же секунду когда сохранялось это +20 оно вернет ему потраченные деньги потому что в памяти была старая запись его маны, а в таком случае мы говорим прибавь сразу к тому же числу 
            user.save()

            InventoryHistory.objects.create(
                user=user,
                mana_amount = 20,
                status = 'mana_accrual',
                description = f'Бонусное начисление маны -- {user.username}'
            )

    return f"Начислено бонусов для {users.count()} пользователей"
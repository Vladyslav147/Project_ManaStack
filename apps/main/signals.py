from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
from apps.store.models import InventoryHistory
from . models import Post

@receiver(pre_save, sender=Post)
def count_post_save(sender, instance, created, **kwargs):
    if created:
        user = instance.author
        count = Post.objects.filter(author=user, status='published').count()

        if count == 5:
            user.mana += 100
            user.save()

            InventoryHistory.objects.create(
                user=user,
                mana_amount = 100,
                status='mana_accrual',
                description=f'Вам начисленно 100 маны за 5-тий опубликованный пост'
            )
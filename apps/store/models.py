from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class Card(models.Model):
    STATUS_CHOICES = [
        ('pin_post', 'pin_post'),
        ('premium', 'premium'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField(max_length=255)
    avatar = models.ImageField(upload_to='card/avatar/', blank=True, null=True)

    price = models.PositiveIntegerField()
    duration_days = models.PositiveIntegerField(default=2)
    type = models.CharField(max_length=10, choices=STATUS_CHOICES, default='premium')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'Card'
        verbose_name = 'Card plan'
        verbose_name_plural = 'Cards plans'
        ordering = ['price']

    def __str__(self):
        return f'{self.name} {self.price}'



class InventoryCard(models.Model):
    STATUS_CHOICES = [
        ('active', 'active'),
        ('inactive', 'inactive')
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='inventary')
    subscription_card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='type_card')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'InventoryCard'
        verbose_name = 'InventoryCard'
        verbose_name_plural = 'InventoryCards'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['end_date', 'status']), #Создает как бы невидимый столб в таблица с сортированными данными, в даном случай берет конец каждой карточки "end_date" и каждую дату сортирует по каждый статус "status", получается что будет "active" и все его "end_date" и так со всеми
        ]
    
    def __str__(self):
        return f'{self.user.username} {self.subscription_card.name} - ({self.status})'
    
    @property
    def is_active(self):
        """Активна ли карточка"""
        return (
            self.status == 'active' and self.end_date > timezone.now()
        )
    
    @property
    def days_remaining(self):
        """Колличетсво дней до окончание """
        if not self.is_active:
            return 0
        delta = self.end_date - timezone.now() # вычисление ростояние времени между сегоднешнем днем и конца подписки
        return max(0, delta.days)
    
    def cancel(self):
        """Отмена подписки"""
        self.status = 'inactive'
        self.save()

    def activate(self):
        self.status = 'active'
        self.start_date = timezone.now()
        self.end_date = self.start_date + timedelta(days=self.subscription_card.duration_days)
        self.save()
    


class PinnedPost(models.Model):
    """Модель закрепленного поста"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='pinned_post')
    post = models.OneToOneField('main.Post', on_delete=models.CASCADE, related_name='pin_info')
    penned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'PinnedPost'
        verbose_name = 'PinnedPost'
        verbose_name_plural = 'PinnedPosts'
    
    def __str__(self):
        return f'{self.user.username} pinned: {self.post.title}'
    
    def save(self, *args, **kwargs):
        has_card = self.user.inventary.filter(
            subscription_card__type = 'premium',
            subscription_card__is_active = True,
            status = 'active',
            end_date__gt=timezone.now()  # gt — расшифровывается как Greater Than (Больше чем >). # lt — Less Than (Меньше чем <). # gte — Greater Than or Equal (Больше или равно >=).
        ).exists()

        if not has_card:
            raise ValueError("У вас нет активной карточки 'Premium' или её срок истёк.")
        
        super().save(*args, **kwargs)
    


class InventoryHistory(models.Model):
    ACTION_CHOICES = [
        ('buy_card', 'Покупка карточки'),
        ('end_card', 'Закончился срок карточки'),
        ('mana_accrual', 'Начисление маны'),
        ('mana_spend', 'Трата маны'), 
        ('mana_send', 'Передача маны'), 
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='inventory_history' 
    )
    
    card = models.ForeignKey(
        'InventoryCard', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='history'
    )
    
    mana_amount = models.IntegerField(help_text="Кол-во маны (отрицательное при трате, положительное при получении)")
    
    status = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'inventory_history'
        verbose_name = 'История инвентаря'
        verbose_name_plural = 'История инвентаря'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} | {self.status} | {self.mana_amount}"
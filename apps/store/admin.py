from django.contrib import admin
from .models import Card, InventoryCard, InventoryHistory, PinnedPost

admin.site.register(Card)
admin.site.register(InventoryCard)
admin.site.register(PinnedPost)

@admin.register(InventoryHistory)
class InventoryHistoryAdmin(admin.ModelAdmin):
    # Добавляем поле в список "только для чтения"
    readonly_fields = ('created_at',)
    
    # Чтобы видеть дату прямо в списке всех записей, добавь её сюда:
    list_display = ('user', 'status', 'mana_amount', 'created_at')


from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

User = get_user_model()

# Снимаем стандартную регистрацию (безопасно)
if admin.site.is_registered(User):
    admin.site.unregister(User)

@admin.register(User)
class MyUserAdmin(UserAdmin):
    # Добавляем ману в список
    list_display = ('username', 'email', 'mana', 'is_staff')
    
    # Добавляем ману в саму карточку пользователя
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('mana',)}),
    )
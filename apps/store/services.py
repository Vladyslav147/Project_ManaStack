from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import InventoryHistory

User = get_user_model()


def perform_mana_transfer(sender, receiver_id, amount):
    amount = int(amount)
    receiver = get_object_or_404(User, id=receiver_id)
    

    if sender == receiver:
        return {"success": False, "message": "Нельзя переводить самому себе"}
    
    if amount <= 0:
        return {"success": False, "message": "Число должно быть положытельным"}
    
    if sender.mana <= amount:
        return {"success": False, "message": "У пользователя не достаточно маны"}
    
    if not sender.is_active or not receiver.is_active:
        return {"success": False, "message": "Пользователь заблокирован"}
    
    
    with transaction.atomic():
        sender.mana -= amount
        sender.save()

        receiver.mana += amount
        receiver.save()

        InventoryHistory.objects.create(
            user=sender,
            mana_amount = -amount,
            status = 'mana_send',
            description=f'Пользователь  {sender.username}  отправил {amount}-маны,  Пользоватлю -  {receiver.username}'
        )
        InventoryHistory.objects.create(
            user=receiver,
            mana_amount = amount,
            status = 'mana_accrual',
            description=f'Пользователь  {sender.username}  отправил вам  {amount} маны'
        )
        return {"success": True, "message": f"Вы успешно перевели {amount} маны,  для {receiver.username}"}






        


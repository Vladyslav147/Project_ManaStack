from rest_framework import permissions

class IsAuthorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user
    



# has_object_permission — это охранник, который стоит не у входа в здание, а у конкретного сейфа (объекта).
# SAFE_METHODS — это безопастные методы только для чтение 

# has_permission: Общая проверка. Можно ли пользователю вообще зайти на этот «склад»? (Например: авторизован он или нет).
#has_object_permission: Точечная проверка. Можно ли пользователю взять именно эту «коробку» со склада? (Например: является ли он автором этого поста).

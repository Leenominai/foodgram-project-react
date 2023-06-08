from rest_framework import permissions


class AdminOrReadOnly(permissions.BasePermission):
    """
    Проверяем, является ли пользователь администратором.
    """
    message = 'Данное действие доступно только администратору.'

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return (request.method in permissions.SAFE_METHODS
                    or request.user.is_admin)
        return request.method in permissions.SAFE_METHODS


class IsAuthorAdminModeratorOrReadOnly(permissions.BasePermission):
    """
    Проверяем является ли пользователь автором,
    модератором или администратором.
    """
    message = 'У вас недостаточно прав для выполнения данного действия.'

    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or obj.author == request.user
                or request.user.is_superuser
                or request.user.is_staff
                )

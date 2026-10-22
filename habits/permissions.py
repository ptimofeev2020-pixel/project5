from rest_framework.permissions import BasePermission


class IsOwner(BasePermission):
    message = 'Доступ только к своим привычкам.'

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

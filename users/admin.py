from django.contrib import admin

from users.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'tg_chat_id', 'is_active')
    search_fields = ('email',)

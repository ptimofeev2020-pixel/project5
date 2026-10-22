from django.contrib import admin

from habits.models import Habit


@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'action', 'time', 'place', 'is_pleasant', 'is_public', 'periodicity')
    list_filter = ('is_pleasant', 'is_public')
    search_fields = ('action', 'place')

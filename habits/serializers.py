from rest_framework import serializers

from habits.models import Habit
from habits.validators import (
    RewardOrRelatedValidator,
    DurationValidator,
    RelatedHabitIsPleasantValidator,
    PleasantHabitValidator,
    PeriodicityValidator,
)


class HabitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Habit
        fields = [
            'id', 'user', 'place', 'time', 'action', 'is_pleasant', 'related_habit',
            'periodicity', 'reward', 'duration', 'is_public',
        ]
        read_only_fields = ['user']
        validators = [
            RewardOrRelatedValidator(),
            DurationValidator(),
            RelatedHabitIsPleasantValidator(),
            PleasantHabitValidator(),
            PeriodicityValidator(),
        ]

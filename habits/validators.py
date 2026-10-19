from rest_framework.serializers import ValidationError

MAX_DURATION_SECONDS = 120
MAX_PERIODICITY_DAYS = 7


def get_value(attrs, instance, field):
    if field in attrs:
        return attrs[field]
    return getattr(instance, field, None) if instance else None


class RewardOrRelatedValidator:
    requires_context = True

    def __call__(self, attrs, serializer):
        instance = serializer.instance
        if get_value(attrs, instance, 'reward') and get_value(attrs, instance, 'related_habit'):
            raise ValidationError(
                'Нельзя одновременно указать вознаграждение и связанную привычку — выберите что-то одно.'
            )


class DurationValidator:
    requires_context = True

    def __call__(self, attrs, serializer):
        duration = get_value(attrs, serializer.instance, 'duration')
        if duration is not None and duration > MAX_DURATION_SECONDS:
            raise ValidationError({'duration': 'Время выполнения не должно превышать 120 секунд.'})


class RelatedHabitIsPleasantValidator:
    requires_context = True

    def __call__(self, attrs, serializer):
        related = get_value(attrs, serializer.instance, 'related_habit')
        if related and not related.is_pleasant:
            raise ValidationError(
                {'related_habit': 'Связанной может быть только привычка с признаком приятной.'}
            )


class PleasantHabitValidator:
    requires_context = True

    def __call__(self, attrs, serializer):
        instance = serializer.instance
        if get_value(attrs, instance, 'is_pleasant') and (
            get_value(attrs, instance, 'reward') or get_value(attrs, instance, 'related_habit')
        ):
            raise ValidationError(
                'У приятной привычки не может быть вознаграждения или связанной привычки.'
            )


class PeriodicityValidator:
    requires_context = True

    def __call__(self, attrs, serializer):
        periodicity = get_value(attrs, serializer.instance, 'periodicity')
        if periodicity is not None and not 1 <= periodicity <= MAX_PERIODICITY_DAYS:
            raise ValidationError(
                {'periodicity': 'Привычку нужно выполнять не реже 1 раза в 7 дней (периодичность от 1 до 7).'}
            )

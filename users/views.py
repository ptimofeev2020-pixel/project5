from rest_framework import generics
from rest_framework.permissions import AllowAny

from users.models import User
from users.serializers import UserRegisterSerializer


class UserRegisterAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]

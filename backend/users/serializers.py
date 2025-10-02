from djoser.serializers import UserCreateSerializer, UserSerializer

from .models import User


class UserCreateSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = ['email', 'username', 'first_name', 'last_name', 'password']


class UserSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

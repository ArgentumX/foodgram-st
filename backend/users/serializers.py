# users/serializers.py
import base64
import binascii
import uuid
from djoser import serializers as djoser_serializers
from rest_framework.serializers import SerializerMethodField
from foodgram.serializers import Base64ImageField
from recipes.serializers import ShortRecipeSerializer

from .models import User


class UserCreateSerializer(djoser_serializers.UserCreateSerializer):
    class Meta(djoser_serializers.UserCreateSerializer.Meta):
        model = User
        fields = [
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password'
        ]
        read_only_fields = ['id']


class UserSerializer(djoser_serializers.UserSerializer):
    is_subscribed = SerializerMethodField()

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated or request.user == obj:
            return False
        return obj.subscribers.filter(subscriber=request.user).exists()

    class Meta(djoser_serializers.UserSerializer.Meta):
        model = User
        fields = [
            'id',
            'username',
            'email',
            'avatar',
            'first_name',
            'last_name',
            'is_subscribed'
        ]


class SubscriptionSerializer(UserSerializer):
    recipes = ShortRecipeSerializer(many=True, read_only=True)
    recipes_count = SerializerMethodField()
    avatar = Base64ImageField(required=False)

    class Meta(UserSerializer.Meta):
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "avatar",
            "is_subscribed",
            "recipes",
            "recipes_count",
        )
        read_only_fields = ("__all__",)

    def get_is_subscribed(self, obj):
        return True

    def get_recipes_count(self, obj):
        return obj.recipes.count()

# users/serializers.py
import base64
import binascii
import uuid
from djoser import serializers as djoser_serializers
from rest_framework import serializers
from rest_framework.serializers import SerializerMethodField
from django.core.files.base import ContentFile
from recipes.serializers import ShortRecipeSerializer

from .models import User


class Base64ImageField(serializers.ImageField):
    MAX_FILE_SIZE = 4 * 1024 * 1024  # 4 MB

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            try:
                header, imgstr = data.split(';base64,')
                ext = header.split('/')[-1].lower()

                if ext not in {'jpg', 'jpeg', 'png', 'gif'}:
                    raise serializers.ValidationError(
                        "Поддерживаются только изображения в форматах JPG, JPEG, PNG или GIF."
                    )

                decoded = base64.b64decode(imgstr)
            except (ValueError, TypeError, binascii.Error):
                raise serializers.ValidationError(
                    "Неверный формат base64-изображения."
                )

            if len(decoded) > self.MAX_FILE_SIZE:
                max_mb = self.MAX_FILE_SIZE // (1024 * 1024)
                raise serializers.ValidationError(
                    f"Размер изображения не должен превышать {max_mb} МБ."
                )

            filename = f"{uuid.uuid4().hex[:10]}.{ext}"
            data = ContentFile(decoded, name=filename)

        return super().to_internal_value(data)


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

# users/serializers.py
import base64
import binascii
import uuid
from djoser import serializers as djoser_serializers
from rest_framework.serializers import SerializerMethodField
from rest_framework import serializers
from django.core.files.base import ContentFile

from .models import User


class Base64ImageField(serializers.ImageField):
    MAX_FILE_SIZE = 4 * 1024 * 1024

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            try:
                format, imgstr = data.split(';base64,')
                ext = format.split('/')[-1].lower()
                if ext not in ['jpg', 'jpeg', 'png', 'gif']:
                    raise serializers.ValidationError(
                        "Некорректный формат изображения.")
                decoded = base64.b64decode(imgstr)
            except (ValueError, TypeError, binascii.Error):
                raise serializers.ValidationError(
                    "Некорректные данные изображения.")

            if len(decoded) > self.MAX_FILE_SIZE:
                raise serializers.ValidationError(
                    f"Размер файла не должен превышать {self.MAX_FILE_SIZE // (1024 * 1024)} MB."
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
    avatar = Base64ImageField(required=False, allow_null=True)

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            return False
        if request.user == obj:
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
    # TODO: если у вас есть короткий сериализатор рецепта, раскомментируйте и используйте:
    # from .recipes_serializers import ShortRecipeSerializer
    # recipes = ShortRecipeSerializer(many=True, read_only=True)
    recipes_count = SerializerMethodField()

    class Meta(UserSerializer.Meta):
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            # "recipes",
            "recipes_count",
        )
        read_only_fields = ("__all__",)

    def get_is_subscribed(self, obj):
        return True

    def get_recipes_count(self, obj):
        return 0

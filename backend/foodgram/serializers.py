import base64
import binascii
import uuid
from django.conf import settings
from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}
    DEFAULT_MAX_SIZE = settings.DEFAULT_CLIENT_MAX_FILESIZE

    def __init__(self, *args, max_size=None, **kwargs):
        self.max_size = max_size if max_size is not None else self.DEFAULT_MAX_SIZE
        super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        if not isinstance(data, str) or not data.startswith('data:image'):
            return super().to_internal_value(data)

        try:
            header, encoded_data = data.split(';base64,', 1)
        except ValueError:
            raise serializers.ValidationError(
                "Неверный формат base64-изображения.")

        try:
            mime_type = header.replace('data:', '')
            ext = mime_type.split('/')[-1].lower()
        except IndexError:
            raise serializers.ValidationError(
                "Не удалось определить расширение изображения.")

        if ext not in self.ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                "Поддерживаются только изображения в форматах JPG, JPEG, PNG или GIF."
            )

        try:
            decoded = base64.b64decode(encoded_data)
        except (TypeError, binascii.Error, ValueError):
            raise serializers.ValidationError(
                "Неверный формат base64-изображения.")

        if len(decoded) > self.max_size:
            max_mb = self.max_size // (1024 * 1024)
            raise serializers.ValidationError(
                f"Размер изображения не должен превышать {max_mb} МБ."
            )

        filename = f"{uuid.uuid4().hex[:10]}.{ext}"
        file = ContentFile(decoded, name=filename)
        return super().to_internal_value(file)

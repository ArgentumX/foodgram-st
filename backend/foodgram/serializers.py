import base64
import binascii
import uuid
from rest_framework import serializers
from django.core.files.base import ContentFile


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

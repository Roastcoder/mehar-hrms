from rest_framework import serializers
from PIL import Image, UnidentifiedImageError

from .models import *


class FaceDetectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FaceDetection
        fields = "__all__"


class EmployeeFaceDetectionSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeFaceDetection
        fields = "__all__"

    def get_image(self, obj):
        if not obj.image:
            return None
        request = self.context.get("request")
        image_url = obj.image.url
        return request.build_absolute_uri(image_url) if request else image_url

    def validate_image(self, value):
        if not value:
            return value

        max_size = 5 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError("Image size must be 5 MB or less.")

        try:
            image = Image.open(value)
            image.verify()
        except (UnidentifiedImageError, OSError, ValueError):
            raise serializers.ValidationError("Upload a valid image file.")

        value.seek(0)
        image = Image.open(value)
        width, height = image.size
        if width < 160 or height < 160:
            raise serializers.ValidationError(
                "Image resolution must be at least 160x160 pixels."
            )

        value.seek(0)
        return value

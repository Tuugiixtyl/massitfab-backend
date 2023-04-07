from rest_framework import serializers
from datetime import datetime


class GallerySerializer(serializers.Serializer):
    resource = serializers.CharField()
    membership_id = serializers.CharField(allow_blank=True, required=False)


class CreateContentSerializer(serializers.Serializer):
    title = serializers.CharField()
    description = serializers.CharField()
    schedule = serializers.CharField(
        required=False, allow_blank=True, default="")
    start_date = serializers.CharField(
        required=False, allow_blank=True, default="")
    end_date = serializers.CharField(
        required=False, allow_blank=True, default="")
    subcategory_id = serializers.IntegerField()
    hashtags = serializers.CharField(required=False)
    st_price = serializers.DecimalField(max_digits=10, decimal_places=2)


class CreateProductSerializer(serializers.Serializer):
    content = CreateContentSerializer()
    source = serializers.ListField(child=serializers.CharField())
    gallery = serializers.ListField(child=GallerySerializer())


class UpdateContentSerializer(serializers.Serializer):
    title = serializers.CharField()
    description = serializers.CharField()
    subcategory_id = serializers.IntegerField()
    hashtags = serializers.CharField(required=False)
    st_price = serializers.DecimalField(max_digits=10, decimal_places=2)


class UpdateProductSerializer(serializers.Serializer):
    content = UpdateContentSerializer()
    source = serializers.ListField(child=serializers.CharField())
    gallery = serializers.ListField(child=GallerySerializer())


class UpdateProfileSerializer(serializers.Serializer):
    username = serializers.CharField()
    summary = serializers.CharField(required=False)
    profile_picture = serializers.CharField()

from rest_framework import serializers
from datetime import datetime

# class LongStringField(serializers.Field):
#     def to_representation(self, value):
#         return value

#     def to_internal_value(self, data):
#         return data

# class GallerySerializer(serializers.Serializer):
#     ### resource = LongStringField()
#     resource = serializers.CharField()
#     membership_id = serializers.CharField(allow_blank=True, required=False)


# class CreateContentSerializer(serializers.Serializer):
#     title = serializers.CharField()
#     description = serializers.CharField()
#     schedule = serializers.CharField(required=False, allow_blank=True, default="")
#     start_date = serializers.CharField(required=False, allow_blank=True, default="")
#     end_date = serializers.CharField(required=False, allow_blank=True, default="")
#     subcategory_id = serializers.IntegerField()
#     hashtags = serializers.CharField(required=False)
#     st_price = serializers.DecimalField(max_digits=10, decimal_places=2)


# class CreateContentSerializer(serializers.Serializer):
#     content = CreateContentSerializer()
#     source = serializers.ListField(child=serializers.CharField())
#     gallery = serializers.ListField(child=GallerySerializer())


class CreateProductSerializer(serializers.Serializer):
    title = serializers.CharField()
    description = serializers.CharField()
    subcategory_id = serializers.CharField()
    st_price = serializers.CharField()
    source = serializers.CharField()
    resource = serializers.ListField(child=serializers.ImageField())

# class UpdateContentSerializer(serializers.Serializer):
#     title = serializers.CharField()
#     description = serializers.CharField()
#     subcategory_id = serializers.IntegerField()
#     hashtags = serializers.CharField(required=False)
#     st_price = serializers.DecimalField(max_digits=10, decimal_places=2)


# class UpdateDeletedSerializer(serializers.Serializer):
#     gallery = serializers.ListField(child=serializers.CharField())
#     source = serializers.ListField(child=serializers.CharField())


# class UpdateProductSerializer(serializers.Serializer):
#     content = UpdateContentSerializer()
#     source = serializers.ListField(child=serializers.CharField())
#     gallery = serializers.ListField(child=GallerySerializer())
#     deleted = serializers.ListField(child=UpdateDeletedSerializer())


class UpdateProfileSerializer(serializers.Serializer):
    username = serializers.CharField()
    summary = serializers.CharField(allow_blank=True, required=False)
    profile_picture = serializers.ImageField(
        max_length=None, allow_empty_file=True)


class UpdateProductSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    subcategory_id = serializers.CharField(required=False, allow_blank=True)
    st_price = serializers.CharField(required=False, allow_blank=True)
    source = serializers.CharField(required=False, allow_blank=True)
    resource = serializers.ListField(child=serializers.ImageField())
    source_deleted = serializers.CharField(required=False, allow_blank=True)
    resource_deleted = serializers.CharField(required=False, allow_blank=True)


class AddToWishlistSerializer(serializers.Serializer):
    product_id = serializers.CharField()
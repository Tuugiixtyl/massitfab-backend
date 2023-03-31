from rest_framework import serializers

class GallerySerializer(serializers.Serializer):
    resource = serializers.CharField()
    membership_id = serializers.CharField(required=False)

class CreateContentSerializer(serializers.Serializer):
    title = serializers.CharField()
    description = serializers.CharField()
    schedule = serializers.CharField()
    start_date = serializers.CharField()
    end_date = serializers.CharField()
    subcategory_id = serializers.IntegerField()
    hashtags = serializers.CharField()
    st_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    source = serializers.ListField(
        child=serializers.CharField()
    )
    gallery = serializers.ListField(
        child=GallerySerializer()
    )
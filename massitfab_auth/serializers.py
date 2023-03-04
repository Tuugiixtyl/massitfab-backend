from rest_framework import serializers


class RegisterUserSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    # passwordre = serializers.CharField(write_only=True)


class LoginUserSerializer(serializers.Serializer):
    # id = serializers.IntegerField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class CreatorSerializer(serializers.Serializer):
    id = serializers.IntegerField()
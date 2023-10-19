from rest_framework import serializers
from .models import Comment, Post, ClientInfo

class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = '__all__'  # Либо укажите только нужные поля, которые вы хотите сериализовать

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'

class ClientInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientInfo
        fields = ['ip_address', 'user_agent', 'user_name']
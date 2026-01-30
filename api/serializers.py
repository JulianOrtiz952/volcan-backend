from rest_framework import serializers
from .models import Project, Task, Subtask
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password']
        )
        return user

class SubtaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subtask
        fields = ['id', 'task', 'title', 'completed', 'created_at']
        read_only_fields = ['id', 'created_at']

class TaskSerializer(serializers.ModelSerializer):
    subtasks = SubtaskSerializer(many=True, read_only=True)

    class Meta:
        model = Task
        fields = ['id', 'project', 'title', 'completed', 'progress', 'subtasks', 'created_at']
        read_only_fields = ['id', 'progress', 'created_at']

class ProjectSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'user', 'user_name', 'name', 'description', 'status', 'progress', 'tasks', 'created_at']
        read_only_fields = ['id', 'user', 'user_name', 'progress', 'created_at']

    def create(self, validated_data):
        # Auto-assign current user if context available
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class CommunityProjectSerializer(serializers.ModelSerializer):
    """Simplified serializer for the public view"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Project
        fields = ['id', 'user_name', 'name', 'progress', 'status']

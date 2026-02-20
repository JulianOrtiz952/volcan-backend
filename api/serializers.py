from rest_framework import serializers
from .models import Project, Task, Subtask, Profile, FocusSession, Note, Community, SharedProject, SharedTask, SharedNote, Notification
from django.contrib.auth import get_user_model

User = get_user_model()

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['display_name', 'avatar_index']

class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'profile']
        read_only_fields = ['id']

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

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
    display_name = serializers.CharField(source='user.profile.display_name', read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'user', 'user_name', 'display_name', 'name', 'description', 'status', 'progress', 'tasks', 'created_at']
        read_only_fields = ['id', 'user', 'user_name', 'display_name', 'progress', 'created_at']

    def create(self, validated_data):
        # Auto-assign current user if context available
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class CommunityProjectSerializer(serializers.ModelSerializer):
    """Simplified serializer for the public view"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    display_name = serializers.CharField(source='user.profile.display_name', read_only=True)
    
    class Meta:
        model = Project
        fields = ['id', 'user_name', 'display_name', 'name', 'progress', 'status']

class FocusSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FocusSession
        fields = ['id', 'user', 'project', 'tag', 'start_time', 'end_time', 'duration_minutes', 'is_completed']
        read_only_fields = ['id', 'user', 'start_time']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ['id', 'user', 'title', 'content', 'note_type', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class CommunityMemberSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(source='profile.display_name', read_only=True, default='')

    class Meta:
        model = User
        fields = ['id', 'username', 'display_name']


class SharedTaskSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = SharedTask
        fields = ['id', 'project', 'title', 'completed', 'created_by', 'created_by_name', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_by', 'created_by_name', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class SharedNoteSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = SharedNote
        fields = ['id', 'project', 'title', 'content', 'created_by', 'created_by_name', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_by', 'created_by_name', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class SharedProjectSerializer(serializers.ModelSerializer):
    shared_tasks = SharedTaskSerializer(many=True, read_only=True)
    shared_notes = SharedNoteSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    progress = serializers.FloatField(read_only=True)

    class Meta:
        model = SharedProject
        fields = ['id', 'community', 'name', 'description', 'status', 'progress',
                  'created_by', 'created_by_name', 'shared_tasks', 'shared_notes', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_by', 'created_by_name', 'progress', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class CommunitySerializer(serializers.ModelSerializer):
    members = CommunityMemberSerializer(many=True, read_only=True)
    owner_name = serializers.CharField(source='owner.username', read_only=True)
    projects = SharedProjectSerializer(many=True, read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Community
        fields = ['id', 'name', 'description', 'owner', 'owner_name', 'members', 'member_count', 'projects', 'created_at']
        read_only_fields = ['id', 'owner', 'owner_name', 'members', 'member_count', 'projects', 'created_at']

    def get_member_count(self, obj):
        return obj.members.count()

    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        community = super().create(validated_data)
        # Owner is also a member
        community.members.add(self.context['request'].user)
        return community


class NotificationSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source='actor.username', read_only=True)
    community_name = serializers.CharField(source='community.name', read_only=True, default='')

    class Meta:
        model = Notification
        fields = ['id', 'recipient', 'actor', 'actor_name', 'notification_type', 'status',
                  'message', 'community', 'community_name', 'created_at']
        read_only_fields = ['id', 'recipient', 'actor', 'actor_name', 'notification_type',
                            'message', 'community', 'community_name', 'created_at']

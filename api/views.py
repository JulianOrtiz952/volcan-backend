from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from .models import Project, Task, Subtask, Profile, FocusSession, Note, Community, SharedProject, SharedTask, SharedNote, Notification
from .serializers import (
    ProjectSerializer, TaskSerializer, SubtaskSerializer,
    CommunityProjectSerializer, RegisterSerializer, UserSerializer,
    ProfileSerializer, ChangePasswordSerializer, FocusSessionSerializer,
    NoteSerializer, CommunitySerializer, SharedProjectSerializer,
    SharedTaskSerializer, SharedNoteSerializer, CommunityMemberSerializer,
    NotificationSerializer
)
from django.contrib.auth import get_user_model

User = get_user_model()

class MeView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

class ProfileUpdateView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProfileSerializer

    def get_object(self):
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        return profile

class ChangePasswordView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.data.get("old_password")):
            return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(serializer.data.get("new_password"))
        user.save()
        return Response({"status": "password set"}, status=status.HTTP_200_OK)

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            "user": UserSerializer(user).data,
            "token": token.key
        }, status=status.HTTP_201_CREATED)

class ProjectViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProjectSerializer

    def get_queryset(self):
        # Default queryset is personal projects
        return Project.objects.filter(user=self.request.user).order_by('-updated_at')

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def community(self, request):
        """
        Public view of all projects with their progress.
        """
        projects = Project.objects.filter(status__in=['IN_PROGRESS', 'COMPLETED']).order_by('-progress')
        serializer = CommunityProjectSerializer(projects, many=True)
        return Response(serializer.data)

class TaskViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TaskSerializer

    def get_queryset(self):
        # Only show tasks from user's projects
        queryset = Task.objects.filter(project__user=self.request.user).order_by('created_at')
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset

class SubtaskViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SubtaskSerializer

    def get_queryset(self):
        return Subtask.objects.filter(task__project__user=self.request.user).order_by('created_at')

class FocusSessionViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FocusSessionSerializer

    def get_queryset(self):
        return FocusSession.objects.filter(user=self.request.user).order_by('-start_time')

    @action(detail=False, methods=['get'])
    def reports(self, request):
        """
        Get productivity reports aggregated by tag/project and daily stats.
        """
        sessions = self.get_queryset()
        from django.db.models import Sum
        from django.db.models.functions import TruncDate
        from django.utils import timezone
        from datetime import timedelta

        # Aggregations by Tag and Project
        tag_data = sessions.values('tag').annotate(total_minutes=Sum('duration_minutes'))
        project_data = sessions.filter(project__isnull=False).values('project__name').annotate(total_minutes=Sum('duration_minutes'))
        
        # Daily stats for the last 365 days (for heatmap and histogram)
        today = timezone.now().date()
        one_year_ago = today - timedelta(days=365)
        
        daily_stats = sessions.filter(start_time__date__gte=one_year_ago) \
            .annotate(date=TruncDate('start_time')) \
            .values('date') \
            .annotate(total_minutes=Sum('duration_minutes')) \
            .order_by('date')

        return Response({
            "by_tag": tag_data,
            "by_project": project_data,
            "daily_stats": daily_stats
        })

class NoteViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NoteSerializer

    def get_queryset(self):
        return Note.objects.filter(user=self.request.user).order_by('-updated_at')


class CommunityViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CommunitySerializer

    def get_queryset(self):
        """Returns communities the user owns OR is a member of."""
        return Community.objects.filter(members=self.request.user).order_by('-created_at')

    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        """Send an invitation (Notification) instead of adding directly."""
        community = self.get_object()
        if community.owner != request.user:
            return Response({'detail': 'Only the owner can invite members.'}, status=status.HTTP_403_FORBIDDEN)
        username = request.data.get('username')
        if not username:
            return Response({'detail': 'Username is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'detail': f'User "{username}" not found.'}, status=status.HTTP_404_NOT_FOUND)
        if user in community.members.all():
            return Response({'detail': 'User is already a member.'}, status=status.HTTP_400_BAD_REQUEST)
        # Check if there is already a pending invite
        existing = Notification.objects.filter(
            recipient=user,
            community=community,
            notification_type='community_invite',
            status='pending'
        ).exists()
        if existing:
            return Response({'detail': 'Invitation already sent.'}, status=status.HTTP_400_BAD_REQUEST)
        # Create the invitation notification
        Notification.objects.create(
            recipient=user,
            actor=request.user,
            notification_type='community_invite',
            message=f'{request.user.username} te ha invitado a la comunidad "{community.name}"',
            community=community,
        )
        return Response({'detail': f'Invitación enviada a {username}.'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def remove_member(self, request, pk=None):
        community = self.get_object()
        if community.owner != request.user:
            return Response({'detail': 'Only the owner can remove members.'}, status=status.HTTP_403_FORBIDDEN)
        username = request.data.get('username')
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'detail': f'User "{username}" not found.'}, status=status.HTTP_404_NOT_FOUND)
        if user == community.owner:
            return Response({'detail': 'Cannot remove the owner.'}, status=status.HTTP_400_BAD_REQUEST)
        community.members.remove(user)
        return Response(CommunitySerializer(community, context={'request': request}).data)


class SharedProjectViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SharedProjectSerializer

    def get_queryset(self):
        """Only projects from communities the user belongs to."""
        return SharedProject.objects.filter(
            community__members=self.request.user
        ).order_by('-updated_at')

    def get_serializer_context(self):
        return {**super().get_serializer_context(), 'request': self.request}

    def perform_create(self, serializer):
        """Create project and notify all community members."""
        project = serializer.save(created_by=self.request.user)
        community = project.community
        # Notify all members except the creator
        for member in community.members.exclude(id=self.request.user.id):
            Notification.objects.create(
                recipient=member,
                actor=self.request.user,
                notification_type='new_project',
                message=f'{self.request.user.username} creó el proyecto "{project.name}" en {community.name}',
                community=community,
            )


class SharedTaskViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SharedTaskSerializer

    def get_queryset(self):
        queryset = SharedTask.objects.filter(
            project__community__members=self.request.user
        ).order_by('created_at')
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset


class SharedNoteViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SharedNoteSerializer

    def get_queryset(self):
        queryset = SharedNote.objects.filter(
            project__community__members=self.request.user
        ).order_by('-updated_at')
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset

    def perform_create(self, serializer):
        """Create note and notify all community members."""
        note = serializer.save(created_by=self.request.user)
        community = note.project.community
        for member in community.members.exclude(id=self.request.user.id):
            Notification.objects.create(
                recipient=member,
                actor=self.request.user,
                notification_type='new_note',
                message=f'{self.request.user.username} creó la nota "{note.title}" en {community.name}',
                community=community,
            )


class NotificationViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerializer
    http_method_names = ['get', 'post', 'delete']

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """How many unread/pending notifications."""
        count = Notification.objects.filter(
            recipient=request.user,
            status__in=['pending']
        ).count()
        return Response({'count': count})

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Accept a community invite."""
        notification = self.get_object()
        if notification.notification_type != 'community_invite':
            return Response({'detail': 'Only invitations can be accepted.'}, status=status.HTTP_400_BAD_REQUEST)
        if notification.status != 'pending':
            return Response({'detail': 'Already processed.'}, status=status.HTTP_400_BAD_REQUEST)
        # Add user to community
        community = notification.community
        if community:
            community.members.add(request.user)
        notification.status = 'accepted'
        notification.save()
        return Response(NotificationSerializer(notification).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a community invite."""
        notification = self.get_object()
        if notification.notification_type != 'community_invite':
            return Response({'detail': 'Only invitations can be rejected.'}, status=status.HTTP_400_BAD_REQUEST)
        if notification.status != 'pending':
            return Response({'detail': 'Already processed.'}, status=status.HTTP_400_BAD_REQUEST)
        notification.status = 'rejected'
        notification.save()
        return Response(NotificationSerializer(notification).data)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark an informational notification as read."""
        notification = self.get_object()
        if notification.status == 'pending' and notification.notification_type != 'community_invite':
            notification.status = 'read'
            notification.save()
        return Response(NotificationSerializer(notification).data)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all non-invite pending notifications as read."""
        Notification.objects.filter(
            recipient=request.user,
            status='pending',
        ).exclude(notification_type='community_invite').update(status='read')
        return Response({'detail': 'OK'})

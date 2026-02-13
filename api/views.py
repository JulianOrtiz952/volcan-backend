from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from .models import Project, Task, Subtask, Profile, FocusSession
from .serializers import (
    ProjectSerializer, TaskSerializer, SubtaskSerializer, 
    CommunityProjectSerializer, RegisterSerializer, UserSerializer,
    ProfileSerializer, ChangePasswordSerializer, FocusSessionSerializer
)

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

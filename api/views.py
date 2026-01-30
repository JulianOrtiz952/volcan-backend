from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from .models import Project, Task, Subtask
from .serializers import ProjectSerializer, TaskSerializer, SubtaskSerializer, CommunityProjectSerializer, RegisterSerializer, UserSerializer

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

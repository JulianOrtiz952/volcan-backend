from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProjectViewSet, TaskViewSet, SubtaskViewSet, FocusSessionViewSet,
    MeView, ProfileUpdateView, ChangePasswordView, NoteViewSet,
    CommunityViewSet, SharedProjectViewSet, SharedTaskViewSet, SharedNoteViewSet,
    NotificationViewSet
)

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'subtasks', SubtaskViewSet, basename='subtask')
router.register(r'focus-sessions', FocusSessionViewSet, basename='focus-session')
router.register(r'notes', NoteViewSet, basename='note')
router.register(r'communities', CommunityViewSet, basename='community')
router.register(r'shared-projects', SharedProjectViewSet, basename='shared-project')
router.register(r'shared-tasks', SharedTaskViewSet, basename='shared-task')
router.register(r'shared-notes', SharedNoteViewSet, basename='shared-note')
router.register(r'notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
    path('me/', MeView.as_view(), name='me'),
    path('profile/', ProfileUpdateView.as_view(), name='profile-update'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
]

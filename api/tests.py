from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Project, Task, Subtask

User = get_user_model()

class ProjectAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.client.force_authenticate(user=self.user)
        self.project = Project.objects.create(user=self.user, name="Test Project", description="Test Description")
        self.task = Task.objects.create(project=self.project, title="Test Task")
        self.subtask = Subtask.objects.create(task=self.task, title="Test Subtask")

    def test_delete_project(self):
        response = self.client.delete(f'/api/projects/{self.project.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Project.objects.count(), 0)
        self.assertEqual(Task.objects.count(), 0)
        self.assertEqual(Subtask.objects.count(), 0)

    def test_update_project(self):
        response = self.client.patch(f'/api/projects/{self.project.id}/', {'name': 'Updated Project'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, 'Updated Project')

    def test_update_task(self):
        response = self.client.patch(f'/api/tasks/{self.task.id}/', {'title': 'Updated Task'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, 'Updated Task')

    def test_update_subtask(self):
        response = self.client.patch(f'/api/subtasks/{self.subtask.id}/', {'title': 'Updated Subtask'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.subtask.refresh_from_db()
        self.assertEqual(self.subtask.title, 'Updated Subtask')

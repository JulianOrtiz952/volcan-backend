from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    display_name = models.CharField(max_length=100, blank=True)
    avatar_index = models.IntegerField(default=0) # Index for predefined avatars

    def __str__(self):
        return f"Profile of {self.user.username}"

class Project(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('ARCHIVED', 'Archived'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    progress = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Calculated average of tasks' progress"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Task(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=255)
    completed = models.BooleanField(default=False)
    progress = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Calculated average of subtasks' completion or 100 if completed"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Subtask(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='subtasks')
    title = models.CharField(max_length=255)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class FocusSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='focus_sessions')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='focus_sessions')
    tag = models.CharField(max_length=100)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.FloatField(default=0.0)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.tag} ({self.duration_minutes} min)"

class Note(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notes')
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True, null=True)
    note_type = models.CharField(max_length=100, default='Personal')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.user.username}"


class Community(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_communities')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    members = models.ManyToManyField(User, related_name='communities', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} (owner: {self.owner.username})"


class SharedProject(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('ARCHIVED', 'Archived'),
    ]

    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='projects')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='shared_projects_created')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='IN_PROGRESS')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} [{self.community.name}]"

    @property
    def progress(self):
        tasks = self.shared_tasks.all()
        if not tasks:
            return 0.0
        completed = tasks.filter(completed=True).count()
        return round((completed / tasks.count()) * 100, 1)


class SharedTask(models.Model):
    project = models.ForeignKey(SharedProject, on_delete=models.CASCADE, related_name='shared_tasks')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='shared_tasks_created')
    title = models.CharField(max_length=255)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class SharedNote(models.Model):
    project = models.ForeignKey(SharedProject, on_delete=models.CASCADE, related_name='shared_notes')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='shared_notes_created')
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} [{self.project.name}]"


class Notification(models.Model):
    TYPE_CHOICES = [
        ('community_invite', 'Community Invitation'),
        ('new_project', 'New Shared Project'),
        ('new_note', 'New Shared Note'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('read', 'Read'),
    ]

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    actor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    message = models.CharField(max_length=500)
    community = models.ForeignKey(Community, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.notification_type}] {self.actor.username} → {self.recipient.username}"

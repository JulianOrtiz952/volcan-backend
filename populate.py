import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from api.models import Project, Task, Subtask

User = get_user_model()

# Create Admin User
if not User.objects.filter(username='admin').exists():
    user = User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print("User 'admin' created with password 'admin'")
else:
    user = User.objects.get(username='admin')
    print("User 'admin' already exists")

# Create Sample Project
project, created = Project.objects.get_or_create(
    name="Rediseño Web (Real)",
    user=user,
    defaults={
        'description': "Data from Django Backend!",
        'status': 'IN_PROGRESS'
    }
)

if created:
    # Add Tasks
    t1 = Task.objects.create(project=project, title="Definir paleta de colores", completed=True, progress=100)
    t2 = Task.objects.create(project=project, title="Crear Componentes React", completed=False)
    
    # Add Subtasks
    Subtask.objects.create(task=t2, title="Botones y Inputs", completed=True)
    Subtask.objects.create(task=t2, title="Navbar responsive", completed=False)
    
    t2.save() # Trigger signal update
    project.save()

print("Sample data populated.")

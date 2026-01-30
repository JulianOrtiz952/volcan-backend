from django.db.models import Avg, Count, Case, When, IntegerField

def recalculate_task_progress(task):
    """
    Recalculates the progress of a Task based on its Subtasks.
    - If no subtasks: progress is 100 if completed, else 0.
    - If subtasks: progress is the percentage of completed subtasks.
    """
    subtasks = task.subtasks.all()
    total = subtasks.count()
    
    if total == 0:
        new_progress = 100.0 if task.completed else 0.0
    else:
        completed_count = subtasks.filter(completed=True).count()
        new_progress = (completed_count / total) * 100.0
    
    # Only update if changed to avoid unnecessary recursion/signals
    if abs(task.progress - new_progress) > 0.01:
        task.progress = new_progress
        # Auto-complete task if progress is 100 (optional but nice)
        if new_progress == 100.0:
            task.completed = True
        elif new_progress < 100.0 and total > 0:
             # If it has subtasks and not 100%, it's not "completed" in the binary sense?
             # User said: "Si no tiene subtareas, entonces sí es 0% o 100%."
             # For now let's update completed status based on progress = 100
             task.completed = False
             
        task.save()  # This triggers Task.post_save

def recalculate_project_progress(project):
    """
    Recalculates the progress of a Project based on its Tasks.
    - Progress is the average of all tasks' progress.
    """
    tasks = project.tasks.all()
    if not tasks.exists():
        new_progress = 0.0
    else:
        # User said: "El promedio del progreso de todas las tareas define el progreso del Proyecto."
        aggregate = tasks.aggregate(avg_progress=Avg('progress'))
        new_progress = aggregate['avg_progress'] or 0.0
        
    if abs(project.progress - new_progress) > 0.01:
        project.progress = new_progress
        # Update status based on progress
        if new_progress == 100.0:
             project.status = 'COMPLETED'
        elif new_progress > 0.0 and project.status == 'PENDING':
             project.status = 'IN_PROGRESS'
             
        project.save()

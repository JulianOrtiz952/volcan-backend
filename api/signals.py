from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Task, Subtask
from .services.progress import recalculate_task_progress, recalculate_project_progress

@receiver(post_save, sender=Subtask)
@receiver(post_delete, sender=Subtask)
def subtask_changed(sender, instance, **kwargs):
    recalculate_task_progress(instance.task)

@receiver(post_save, sender=Task)
@receiver(post_delete, sender=Task)
def task_changed(sender, instance, **kwargs):
    # Update own progress first (in case completed changed but no subtasks)
    # The function has a recursion guard so this is safe
    recalculate_task_progress(instance)
    # Then update project
    recalculate_project_progress(instance.project)

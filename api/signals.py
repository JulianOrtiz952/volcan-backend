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
    # If the task was just deleted, we don't recalculate its own progress
    # because it doesn't exist anymore and save() would fail.
    # We only update the project progress.
    if kwargs.get('created') is not None or 'update_fields' in kwargs or sender.objects.filter(pk=instance.pk).exists():
        # This is a safe way to check if it's NOT a deletion or if it still exists
        # Actually post_save has 'created', post_delete does not.
        pass

    # Better approach:
    if kwargs.get('signal') == post_save:
         recalculate_task_progress(instance)
    
    # Always update project (if it exists)
    try:
        if instance.project:
            recalculate_project_progress(instance.project)
    except Exception:
        # Project might have been deleted too (cascade)
        pass

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import SituationContext, Note, PersonalGoal, ChatMessage
from .services import N8nIntegrationService

@receiver(post_save, sender=SituationContext)
def trigger_n8n_on_context_save(sender, instance, created, **kwargs):
    """
    Trigger n8n whenever a SituationContext is created or updated.
    """
    N8nIntegrationService.trigger_context_processing(instance.id)

@receiver(post_save, sender=Note)
def trigger_n8n_on_note_save(sender, instance, created, **kwargs):
    """
    Trigger n8n for the related context when a Note is saved.
    """
    if instance.context:
        N8nIntegrationService.trigger_context_processing(instance.context.id)

@receiver(post_save, sender=PersonalGoal)
def trigger_n8n_on_goal_save(sender, instance, created, **kwargs):
    """
    Trigger n8n for the related context when a PersonalGoal is saved.
    """
    if instance.context:
        N8nIntegrationService.trigger_context_processing(instance.context.id)

@receiver(post_save, sender=ChatMessage)
def trigger_n8n_on_chat_message(sender, instance, created, **kwargs):
    """
    Trigger n8n Chat Workflow when a USER message is created.
    """
    if created and instance.role == 'user':
        # Use on_commit or async task in prod, but direct call for now
        N8nIntegrationService.trigger_chat_response(instance.session.id, instance.content)

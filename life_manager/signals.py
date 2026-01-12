from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import SituationContext, Note, PersonalGoal, ChatMessage, Achievement
from .services import N8nIntegrationService, AnalyticsService

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
    Also handles Achievement creation on completion.
    """
    if instance.context:
        N8nIntegrationService.trigger_context_processing(instance.context.id)
    
    # Check if newly completed
    # Note: 'created' is False for updates. We need to check if it JUST became completed.
    # Ideally, we should check pre_save to see previous state, but for this simple app,
    # we can check if it's completed and no achievement exists yet.
    if instance.is_completed:
        # Avoid duplicates
            Achievement.objects.create(
                goal=instance,
                title=f"Achieved: {instance.title}",
                reflection="Completed via API", # Default, can be updated later
                context=instance.context,
                points=AnalyticsService.calculate_points(instance.importance)
            )

@receiver(post_save, sender=ChatMessage)
def trigger_n8n_on_chat_message(sender, instance, created, **kwargs):
    """
    Trigger n8n Chat Workflow when a USER message is created.
    """
    if created and instance.role == 'user':
        # Use on_commit or async task in prod, but direct call for now
        N8nIntegrationService.trigger_chat_response(instance.session.id, instance.content)

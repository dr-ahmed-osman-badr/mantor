import datetime
import requests
import json
from django.conf import settings
from django.db.models import Count, Sum, Q
from .models import SituationContext, StatusOption, PersonalGoal, StatusGroup, Achievement, ContextPreset

# --- 1. Context Resolution Logic ---

def get_situation_from_selection(selected_option_ids):
    """
    Takes a list of StatusOption IDs and returns the SituationContext.
    If it doesn't exist, it creates it.
    """
    # 1. Filter out invalid IDs and ensure unique
    valid_ids = StatusOption.objects.filter(id__in=selected_option_ids).values_list('id', flat=True)
    sorted_ids = sorted([str(oid) for oid in valid_ids])
    
    # 2. Generate Signature
    signature = "-".join(sorted_ids)
    
    if not signature:
        return None, False

    # 3. Get or Create
    context, created = SituationContext.objects.get_or_create(unique_signature=signature)
    
    if created:
        options = StatusOption.objects.filter(id__in=valid_ids)
        context.options.add(*options)
        
    return context, created

# --- 2. Smart Defaults Logic ---

def get_smart_defaults(request):
    """
    Returns a list of Option IDs based on Time and Device.
    """
    defaults = []
    now = datetime.datetime.now()
    
    # A. Time Detection (Day of Week)
    # Assumes a group named "Time" exists
    day_name = now.strftime('%A') 
    day_option = StatusOption.objects.filter(group__name="Time", name=day_name).first()
    if day_option: 
        defaults.append(day_option.id)
    
    # B. Time Detection (Period of Day)
    hour = now.hour
    period = "Morning" if 5 <= hour < 12 else "Afternoon" if 12 <= hour < 17 else "Evening"
    period_option = StatusOption.objects.filter(group__name="Time", name=period).first()
    if period_option:
        defaults.append(period_option.id)
        
    # C. Device Detection
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    device_name = "Mobile" if "mobile" in user_agent else "Laptop"
    # Assumes a group named "Tools" exists
    device_option = StatusOption.objects.filter(group__name="Tools", name=device_name).first()
    if device_option:
        defaults.append(device_option.id)
        
    # D. Default Status (if available in Myself -> Status)
    # Optional: could auto-select 'Free' or 'Busy' based on time/calendar?
    # For now, let's leave internal state manual.
        
    return defaults

# --- 3. Goal Aggregation Logic ---

def get_all_relevant_goals(context):
    """
    Returns all uncompleted goals relevant to the given context.
    This includes goals linked to:
    1. The Context itself.
    2. ANY of the Options within the context.
    """
    if not context:
        return PersonalGoal.objects.none()

    option_ids = context.options.values_list('id', flat=True)
    
    relevant_goals = PersonalGoal.objects.filter(
        Q(linked_option_id__in=option_ids) | Q(context=context),
        is_completed=False
    ).distinct().order_by('-importance', '-created_at')
    
    return relevant_goals

# --- 4. Analytics Service ---

class AnalyticsService:
    @staticmethod
    def get_top_performing_locations():
        """Top places where achievements happened"""
        return StatusOption.objects.filter(group__name="Place") \
            .annotate(num_achievements=Count('contexts__achievement')) \
            .order_by('-num_achievements')

    @staticmethod
    def get_status_productivity_stats():
        """Status vs Points (Busy/Free) - Now under Myself group"""
        return StatusOption.objects.filter(group__name="Myself", category__name="Status") \
            .annotate(total_points=Sum('contexts__achievement__points')) \
            .order_by('-total_points')

    @staticmethod
    def get_mood_productivity_stats():
        """Mood vs Points (Happy/Focus) - Now under Myself group"""
        return StatusOption.objects.filter(group__name="Myself", category__name="Mood") \
            .annotate(total_points=Sum('contexts__achievement__points')) \
            .order_by('-total_points')
            
    @staticmethod
    def calculate_points(importance_level):
        points_map = {
            1: 5,   # Low
            2: 15,  # Medium
            3: 35,  # High
            4: 100, # Critical
        }
        return points_map.get(importance_level, 0)

# --- 5. N8n Integration Service ---

class N8nIntegrationService:
    # Updated with user provided ngrok URL
    N8N_WEBHOOK_URL = "https://agatha-semiacademic-marlee.ngrok-free.dev/webhook/context-trigger" 
    N8N_CHAT_WEBHOOK_URL = "https://agatha-semiacademic-marlee.ngrok-free.dev/webhook/chat-trigger"

    @staticmethod
    def trigger_chat_response(session_id, message_content):
        """
        Sends chat message to n8n for AI response.
        """
        payload = {
            "session_id": session_id,
            "message": message_content,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        try:
            print(f"--- Sending Chat to n8n: {N8nIntegrationService.N8N_CHAT_WEBHOOK_URL} ---")
            requests.post(
                N8nIntegrationService.N8N_CHAT_WEBHOOK_URL,
                json=payload,
                timeout=5
            )
        except Exception as e:
            print(f"Error triggering chat n8n: {e}")

    @staticmethod
    def trigger_context_processing(context_id):
        """
        Sends context data to n8n for AI processing.
        """
        try:
            context = SituationContext.objects.get(id=context_id)
        except SituationContext.DoesNotExist:
            return

        # 1. Prepare Data Payload
        options_data = [
            {
                "id": opt.id, 
                "name": opt.name, 
                "group": opt.group.name, 
                "category": opt.category.name if opt.category else None
            } 
            for opt in context.options.all()
        ]

        # Fetch related content for context (Notes & Goals)
        # We limit to recent or active ones to avoid huge payloads
        notes = context.notes.all().order_by('-created_at')[:5]
        goals = context.goals.filter(is_completed=False)[:5]

        payload = {
            "context_id": context.id,
            "unique_signature": context.unique_signature,
            "created_at": context.created_at.isoformat(),
            "options": options_data,
            "notes": [{"title": n.title, "content": n.content} for n in notes],
            "active_goals": [{"title": g.title, "importance": g.get_importance_display()} for g in goals],
            "timestamp": datetime.datetime.now().isoformat()
        }

        # 2. Send Webhook
        try:
            print(f"--- Sending to n8n: {N8nIntegrationService.N8N_WEBHOOK_URL} ---")
            # Using timeout to prevent hanging the Django process
            response = requests.post(
                N8nIntegrationService.N8N_WEBHOOK_URL, 
                json=payload, 
                timeout=5
            )
            print(f"n8n Response: {response.status_code} - {response.text}")
        except Exception as e:
            # Fail silently or log error so user flow isn't interrupted
            print(f"Error triggering n8n: {e}")

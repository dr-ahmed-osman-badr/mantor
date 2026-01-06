import datetime
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

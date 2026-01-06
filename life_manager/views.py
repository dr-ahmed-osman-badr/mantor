from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count
from django.views.decorators.csrf import csrf_exempt
from .models import StatusGroup, StatusOption, ContextPreset, PersonalGoal, Achievement, SituationContext, OptionCategory
from .services import get_situation_from_selection, get_smart_defaults, get_all_relevant_goals, AnalyticsService

def dashboard_view(request):
    """
    Main dashboard.
    1. Handles "Quick Presets"
    2. Handles Manual Selection
    3. Handles Smart Defaults
    4. Renders context-aware content
    """
    selected_ids = []
    
    # A. Handle Presets
    if 'preset' in request.GET:
        preset = get_object_or_404(ContextPreset, id=request.GET['preset'])
        selected_ids = list(preset.options.values_list('id', flat=True))
    else:
        # B. Handle Manual Selection + Defaults
        # Get manually selected options
        manual_ids = [int(x) for x in request.GET.getlist('options') if x.isdigit()]
        
        # Get defaults (only if not full manual override intended - logic depends on UX)
        # Here we mix them: Defaults apply unless specifically overridden or if empty.
        # Simple approach: Defaults are just initial suggestions, but if we are *loading* the page 
        # with query params, we assume the user made a choice.
        # If NO query params, we load defaults.
        if not manual_ids and not request.GET:
             manual_ids = get_smart_defaults(request)
        
        selected_ids = manual_ids

    # Deduplicate
    selected_ids = list(set(selected_ids))

    # C. Get Context
    context, created = get_situation_from_selection(selected_ids)
    
    # D. Get Notes & Goals
    notes = context.notes.all() if context else []
    goals = get_all_relevant_goals(context)
    recommendations = context.recommendations.filter(priority__gte=1).order_by('-priority', '-created_at') if context else []
    
    groups_qs = StatusGroup.objects.prefetch_related(
        'statusoption_set',
        'categories',
        'categories__subcategories',
        'categories__statusoption_set'
    ).all()
    
    # Custom ordering: Myself first, then others
    preferred_order = ["Myself", "People", "Place", "Time", "Tools"]
    groups = sorted(groups_qs, key=lambda g: preferred_order.index(g.name) if g.name in preferred_order else 999)
    
    presets = ContextPreset.objects.all()

    # F. Get/Resolve selected options objects for display
    # Order by Group Name to support {% regroup %} in template
    selected_options = StatusOption.objects.filter(id__in=selected_ids).select_related('group').order_by('group__name', 'category__name', 'name')

    context_data = {
        'context': context,
        'selected_ids': selected_ids,
        'selected_options': selected_options,
        'notes': notes,
        'goals': goals,
        'recommendations': recommendations,
        'groups': groups,
        'presets': presets,
    }
    return render(request, 'life_manager/dashboard.html', context_data)

def mark_goal_achieved(request, goal_id):
    """
    Action to complete a goal
    """
    if request.method == 'POST':
        goal = get_object_or_404(PersonalGoal, id=goal_id)
        reflection = request.POST.get('reflection', '')
        
        if not goal.is_completed:
            goal.is_completed = True
            goal.save()
            
            # Create Achievement
            Achievement.objects.create(
                context=goal.context, # Note: This might be null if goal linked to Option only. 
                                      # ideally we want the CURRENT context. 
                                      # For now, let's use the goal's context if set, or null.
                                      # FUTURE IMPROVEMENT: Pass current context ID in form.
                goal=goal,
                title=goal.title,
                description=goal.description,
                reflection=reflection,
                points=AnalyticsService.calculate_points(goal.importance)
            )
            
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

def analytics_view(request):
    """
    Reports page
    """
    top_places = AnalyticsService.get_top_performing_locations()
    status_stats = AnalyticsService.get_status_productivity_stats()
    mood_stats = AnalyticsService.get_mood_productivity_stats()
    
    return render(request, 'life_manager/analytics.html', {
        'top_places': top_places,
        'status_stats': status_stats,
        'mood_stats': mood_stats
    })

def add_option(request):
    """
    Simpler quick-add for options (e.g., adding a new Person)
    """
    if request.method == 'POST':
        group_id = request.POST.get('group_id')
        category_id = request.POST.get('category_id')
        subcategory_id = request.POST.get('subcategory_id')
        name = request.POST.get('name')
        
        if group_id and name:
            group = get_object_or_404(StatusGroup, id=group_id)
            category = None
            
            # 1. Try existing category / subcategory
            if subcategory_id:
                  category = OptionCategory.objects.filter(id=subcategory_id).first()
            elif category_id:
                category = OptionCategory.objects.filter(id=category_id).first()
            
            # Handle "Create New Category" Override (Top level only for now)
            new_cat_name = request.POST.get('category_name')
            if new_cat_name and group:
                category, _ = OptionCategory.objects.get_or_create(
                    group=group,
                    name=new_cat_name
                )

            if group:
                # Default icon for People
                icon = "fa-user" if group.name == "People" else "fa-tag"
                
                StatusOption.objects.get_or_create(
                    group=group,
                    category=category,
                    name=name,
                    defaults={'icon': icon}
                )
            
            
    return redirect('life_manager:dashboard')

def add_goal(request):
    """
    Quick add goal linked to an option
    """
    if request.method == 'POST':
        title = request.POST.get('title')
        importance = request.POST.get('importance', 2)
        linked_option_id = request.POST.get('linked_option_id')
        
        if title:
            goal = PersonalGoal(
                title=title,
                importance=int(importance)
            )
            
            if linked_option_id:
                goal.linked_option = get_object_or_404(StatusOption, id=linked_option_id)
            else:
                # If no option selected, maybe link to current context? 
                # For now, let's keep it simple: global goal if no option, or require option?
                # The user specifically asked to add targets TO items.
                pass
                
            goal.save()
            
            
    return redirect('life_manager:dashboard')

def add_note(request):
    """
    Add a note to the current context
    """
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        # We need to know WHICH context to attach to.
        # Ideally, we pass the signature or IDs. 
        # For simplicity, let's re-resolve based on active session/params or hidden input.
        # Let's use a hidden input 'context_signature' from the form
        unique_signature = request.POST.get('unique_signature')
        
        if title and content and unique_signature:
            context = SituationContext.objects.filter(unique_signature=unique_signature).first()
            if context:
                from .models import Note
                Note.objects.create(
                    context=context,
                    title=title,
                    content=content
                )
    
    return redirect('life_manager:dashboard')
    return redirect('life_manager:dashboard')

# --- API ViewSets ---
from rest_framework import viewsets
from .serializers import (
    StatusGroupSerializer, OptionCategorySerializer, StatusOptionSerializer,
    SituationContextSerializer, NoteSerializer, PersonalGoalSerializer,
    AchievementSerializer, ContextPresetSerializer, AiRecommendationSerializer
)
from .models import (
    StatusGroup, OptionCategory, StatusOption, 
    SituationContext, Note, PersonalGoal, 
    Achievement, ContextPreset, AiRecommendation
)

class GroupViewSet(viewsets.ModelViewSet):
    queryset = StatusGroup.objects.all()
    serializer_class = StatusGroupSerializer

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = OptionCategory.objects.all()
    serializer_class = OptionCategorySerializer

class OptionViewSet(viewsets.ModelViewSet):
    """
    API for listing and retrieving StatusOptions.
    """
    queryset = StatusOption.objects.select_related('group', 'category').all()
    serializer_class = StatusOptionSerializer

class ContextViewSet(viewsets.ModelViewSet):
    queryset = SituationContext.objects.prefetch_related('options').all()
    serializer_class = SituationContextSerializer

class NoteViewSet(viewsets.ModelViewSet):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer

class GoalViewSet(viewsets.ModelViewSet):
    queryset = PersonalGoal.objects.all()
    serializer_class = PersonalGoalSerializer

class AchievementViewSet(viewsets.ModelViewSet):
    queryset = Achievement.objects.all()
    serializer_class = AchievementSerializer

class RecommendationViewSet(viewsets.ModelViewSet):
    queryset = AiRecommendation.objects.all()
    serializer_class = AiRecommendationSerializer

class PresetViewSet(viewsets.ModelViewSet):
    """
    API for creating and listing ContextPresets.
    """
    queryset = ContextPreset.objects.all()
    serializer_class = ContextPresetSerializer

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count
from .models import StatusGroup, StatusOption, ContextPreset, PersonalGoal, Achievement, SituationContext
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
    
    # D. Get Articles & Goals
    articles = context.articles.all() if context else []
    goals = get_all_relevant_goals(context)
    
    # E. Get All Groups/Options for the UI Dropdowns
    groups = StatusGroup.objects.prefetch_related('options', 'categories__options').all()
    presets = ContextPreset.objects.all()

    context_data = {
        'context': context,
        'selected_ids': selected_ids,
        'articles': articles,
        'goals': goals,
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
    mood_stats = AnalyticsService.get_mood_productivity_stats()
    
    return render(request, 'life_manager/analytics.html', {
        'top_places': top_places,
        'mood_stats': mood_stats
    })

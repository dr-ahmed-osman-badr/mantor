from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count, Sum
from django.utils.decorators import method_decorator
from django.contrib.auth.models import User
from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, action
import requests
import json
from rest_framework.response import Response

from .models import (
    StatusGroup, StatusOption, ContextPreset, PersonalGoal, 
    Achievement, SituationContext, OptionCategory,
    AiRecommendation, ChatSession, ChatMessage, Note
)
from .services import get_situation_from_selection, get_smart_defaults, get_all_relevant_goals, AnalyticsService
from .serializers import (
    StatusGroupSerializer, OptionCategorySerializer, StatusOptionSerializer,
    SituationContextSerializer, NoteSerializer, PersonalGoalSerializer,
    AchievementSerializer, ContextPresetSerializer, AiRecommendationSerializer,
    ChatSessionSerializer, ChatMessageSerializer
)

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






    return redirect('life_manager:dashboard')

# --- API ViewSets ---


class ChatSessionViewSet(viewsets.ModelViewSet):
    """
    API for managing chat sessions.
    """
    queryset = ChatSession.objects.prefetch_related('messages').all()
    serializer_class = ChatSessionSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ChatMessageViewSet(viewsets.ModelViewSet):
    """
    API for managing chat messages.
    """
    queryset = ChatMessage.objects.all()
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        # 1. Check if this is the generic start message from the Mobile App
        initial_data = serializer.validated_data
        content = initial_data.get('content', '')
        
        if "I have some advice regarding" in content and "Let me know if you want to explore this further" in content:
            # 2. Check if linked to a Recommendation
            session = initial_data.get('session')
            if session and hasattr(session, 'recommendation_linked'):
                rec = session.recommendation_linked
                # 3. Swap content
                serializer.save(
                    content=f"Recommendation: '{rec.title}'\n\nSummary: {rec.summary}\n\nDetails: {rec.recommendation}\n\nI'm ready to discuss this recommendation further."
                )
                return

        serializer.save()

def _create_related_chat_session(instance, user, initial_message):
    """
    Helper: Creates a ChatSession and Initial Message for an instance.
    """
    # 1. Create Session
    title = f"Chat: {getattr(instance, 'title', 'New Item')}"
    
    if user:
        session = ChatSession.objects.create(user=user, title=title)
        
        # 2. Create System Message
        ChatMessage.objects.create(
            session=session,
            role="system",
            content=initial_message
        )
        
        # 3. Link to instance
        instance.chat_session = session
        instance.save()

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

    def perform_create(self, serializer):
        instance = serializer.save()
        _create_related_chat_session(
            instance, 
            self.request.user, 
            f"I am ready to discuss your note: '{instance.title}'."
        )

class GoalViewSet(viewsets.ModelViewSet):
    queryset = PersonalGoal.objects.all()
    serializer_class = PersonalGoalSerializer
    
    def perform_create(self, serializer):
        instance = serializer.save()
        _create_related_chat_session(
            instance, 
            self.request.user, 
            f"Let's work on your goal: '{instance.title}'. How can I help you achieve it?"
        )

class AchievementViewSet(viewsets.ModelViewSet):
    queryset = Achievement.objects.all()
    serializer_class = AchievementSerializer

class RecommendationViewSet(viewsets.ModelViewSet):
    queryset = AiRecommendation.objects.all()
    serializer_class = AiRecommendationSerializer
    
    def perform_create(self, serializer):
        instance = serializer.save()
        _create_related_chat_session(
            instance, 
            self.request.user, 
            f"Recommendation: '{instance.title}'\n\nSummary: {instance.summary}\n\nDetails: {instance.recommendation}\n\nI'm ready to discuss this recommendation further."
        )

    @action(detail=False, methods=['post'])
    def generate_plan(self, request):
        n8n_url = "https://agatha-semiacademic-marlee.ngrok-free.dev/webhook/context-trigger"
        try:
            # Prepare payload
            payload = request.data
            
            # Forward to N8N
            # We strictly pass what we received. 
            # If the user says "all notes and goals... are already present in the context", 
            # we trust the frontend sends a rich payload or at least the context reference.
            response = requests.post(n8n_url, json=payload)
            response.raise_for_status()
            
            n8n_data = response.json()
            
            # Extract recommendation details
            # Assuming N8N returns { "title": "...", "summary": "...", "recommendation": "..." }
            # Provide defaults if keys missing
            title = n8n_data.get('title', 'AI Plan')
            summary = n8n_data.get('summary', 'Generated Plan')
            recommendation_text = n8n_data.get('recommendation', '')
            if not recommendation_text:
                # Fallback: if 'output' or just raw json
                recommendation_text = n8n_data.get('output', json.dumps(n8n_data, indent=2))
            
            # Resolve Context
            # request.data might have 'context_id' or 'context': {'id': ...}
            context_id = payload.get('context_id')
            if not context_id and isinstance(payload.get('context'), dict):
                context_id = payload['context'].get('id')
            
            # Heuristic: Try to find context in notes or goals if not at top level
            if not context_id:
                notes = payload.get('notes')
                if isinstance(notes, list) and len(notes) > 0 and isinstance(notes[0], dict):
                    context_id = notes[0].get('context')
            
            if not context_id:
                goals = payload.get('goals')
                if isinstance(goals, list) and len(goals) > 0 and isinstance(goals[0], dict):
                    context_id = goals[0].get('context')

            # Lookup by Signature (Frontend seems to send 'signature')
            if not context_id:
                signature = payload.get('signature')
                if signature:
                    try:
                        situation_context = SituationContext.objects.get(unique_signature=signature)
                        context_id = situation_context.id
                    except SituationContext.DoesNotExist:
                        pass

            # Use the first context if absolutely nothing is provided but context objects exist?
            # No, that's dangerous. Fail if no context.
            if not context_id: 
                 return Response({"error": "Context ID is required. Please include 'context_id', 'signature', OR ensure notes/goals objects have 'context' field."}, status=400)

            if 'situation_context' not in locals():
                situation_context = get_object_or_404(SituationContext, pk=context_id)

            # Create Recommendation
            rec = AiRecommendation.objects.create(
                context=situation_context,
                title=title,
                summary=summary,
                recommendation=recommendation_text,
                priority=2 # Medium default
            )
            
            serializer = self.get_serializer(rec)
            return Response(serializer.data)
            
        except requests.exceptions.RequestException as e:
            return Response({"error": f"N8N Error: {str(e)}"}, status=502)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

class PresetViewSet(viewsets.ModelViewSet):
    """
    API for creating and listing ContextPresets.
    """
    queryset = ContextPreset.objects.all()
    serializer_class = ContextPresetSerializer

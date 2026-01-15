from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    dashboard_view, analytics_view, GroupViewSet, CategoryViewSet,
    OptionViewSet, ContextViewSet, NoteViewSet, GoalViewSet,
    AchievementViewSet, RecommendationViewSet, PresetViewSet,
    ChatSessionViewSet, ChatMessageViewSet, register_user, change_password
)

app_name = 'life_manager'

# Create Router and register ViewSets
router = DefaultRouter()
router.register(r'groups', GroupViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'options', OptionViewSet)
router.register(r'presets', PresetViewSet)
router.register(r'contexts', ContextViewSet)
router.register(r'notes', NoteViewSet)
router.register(r'goals', GoalViewSet)
router.register(r'achievements', AchievementViewSet)
router.register(r'recommendations', RecommendationViewSet)
router.register(r'chat_sessions', ChatSessionViewSet)
router.register(r'chat_messages', ChatMessageViewSet)

urlpatterns = [
    path('register/', register_user, name='register'),
    path('', dashboard_view, name='dashboard'),
    path('analytics/', analytics_view, name='analytics'),
    
    # API Routes managed by Router
    path('', include(router.urls)),
    path('change-password/', change_password, name='change_password'),
]

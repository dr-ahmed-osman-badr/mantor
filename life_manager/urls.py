from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'life_manager'

# Create Router and register ViewSets
router = DefaultRouter()
router.register(r'groups', views.GroupViewSet)
router.register(r'categories', views.CategoryViewSet)
router.register(r'options', views.OptionViewSet)
router.register(r'presets', views.PresetViewSet)
router.register(r'contexts', views.ContextViewSet)
router.register(r'notes', views.NoteViewSet)
router.register(r'goals', views.GoalViewSet)
router.register(r'achievements', views.AchievementViewSet)
router.register(r'recommendations', views.RecommendationViewSet)

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('analytics/', views.analytics_view, name='analytics'),
    
    # API Routes managed by Router
    path('', include(router.urls)),
]

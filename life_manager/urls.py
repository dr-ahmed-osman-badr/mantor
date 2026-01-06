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
    path('mark_goal_achieved/<int:goal_id>/', views.mark_goal_achieved, name='mark_goal_achieved'),
    path('add_option/', views.add_option, name='add_option'),
    path('add_goal/', views.add_goal, name='add_goal'),
    path('add_note/', views.add_note, name='add_note'),
    path('analytics/', views.analytics_view, name='analytics'),
    
    # API Routes managed by Router
    path('', include(router.urls)),
]

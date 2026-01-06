from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'life_manager'

# Create Router and register ViewSets
router = DefaultRouter()
router.register(r'options', views.OptionViewSet) # /options/
router.register(r'presets', views.PresetViewSet) # /presets/

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('mark_goal_achieved/<int:goal_id>/', views.mark_goal_achieved, name='mark_goal_achieved'),
    path('add_option/', views.add_option, name='add_option'),
    path('add_goal/', views.add_goal, name='add_goal'),
    path('add_article/', views.add_article, name='add_article'),
    path('analytics/', views.analytics_view, name='analytics'),
    
    # API Routes managed by Router
    path('', include(router.urls)),
]

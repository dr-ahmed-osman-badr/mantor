from django.urls import path
from . import views

app_name = 'life_manager'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('goal/<int:goal_id>/achieve/', views.mark_goal_achieved, name='mark_goal_achieved'),
    path('analytics/', views.analytics_view, name='analytics'),
]

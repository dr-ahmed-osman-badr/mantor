from django.urls import path
from . import views

app_name = 'life_manager'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('mark_goal_achieved/<int:goal_id>/', views.mark_goal_achieved, name='mark_goal_achieved'),
    path('add_option/', views.add_option, name='add_option'),
    path('add_goal/', views.add_goal, name='add_goal'),
    path('add_article/', views.add_article, name='add_article'),
    path('analytics/', views.analytics_view, name='analytics'),
    path('options/', views.get_options_api, name='get_options_api'),
    path('options/<int:option_id>/', views.delete_option_api, name='delete_option_api'),
]

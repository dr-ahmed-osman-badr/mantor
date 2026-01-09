from django.contrib import admin
from .models import (
    StatusGroup, OptionCategory, StatusOption,
    SituationContext, Note, PersonalGoal,
    Achievement, ContextPreset, AiRecommendation,
    GoalPlan, GoalTaskInfo, SubTask
)

@admin.register(AiRecommendation)
class AiRecommendationAdmin(admin.ModelAdmin):
    list_display = ('title', 'priority', 'context', 'created_at')
    list_filter = ('priority', 'created_at')

@admin.register(StatusGroup)
class StatusGroupAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(StatusOption)
class StatusOptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'group', 'category')
    list_filter = ('group', 'category')

class AiRecommendationInline(admin.StackedInline):
    model = AiRecommendation
    extra = 1

class GoalPlanInline(admin.StackedInline):
    model = GoalPlan
    extra = 0

class GoalTaskInfoInline(admin.StackedInline):
    model = GoalTaskInfo
    extra = 0

class SubTaskInline(admin.TabularInline):
    model = SubTask
    extra = 1

@admin.register(SituationContext)
class SituationContextAdmin(admin.ModelAdmin):
    list_display = ('unique_signature', 'created_at')
    inlines = [AiRecommendationInline]

@admin.register(PersonalGoal)
class PersonalGoalAdmin(admin.ModelAdmin):
    list_display = ('title', 'importance', 'is_completed', 'context', 'linked_option')
    list_filter = ('importance', 'is_completed')
    inlines = [GoalPlanInline, GoalTaskInfoInline, SubTaskInline]

admin.site.register(OptionCategory)
admin.site.register(Note)
admin.site.register(Achievement)
admin.site.register(ContextPreset)

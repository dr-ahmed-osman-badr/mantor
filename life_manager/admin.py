from django.contrib import admin
from .models import StatusGroup, OptionCategory, StatusOption, SituationContext, Article, PersonalGoal, Achievement, ContextPreset

@admin.register(StatusGroup)
class StatusGroupAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(StatusOption)
class StatusOptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'group', 'category')
    list_filter = ('group', 'category')

@admin.register(SituationContext)
class SituationContextAdmin(admin.ModelAdmin):
    list_display = ('unique_signature', 'created_at')

@admin.register(PersonalGoal)
class PersonalGoalAdmin(admin.ModelAdmin):
    list_display = ('title', 'importance', 'is_completed', 'context', 'linked_option')
    list_filter = ('importance', 'is_completed')

admin.site.register(OptionCategory)
admin.site.register(Article)
admin.site.register(Achievement)
admin.site.register(ContextPreset)

from rest_framework import serializers
from .models import (
    StatusGroup, OptionCategory, StatusOption, 
    SituationContext, Note, PersonalGoal, 
    Achievement, ContextPreset, AiRecommendation,
    ChatSession, ChatMessage
)

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'role', 'content', 'timestamp', 'session']

class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = ChatSession
        fields = ['id', 'user', 'title', 'created_at', 'messages']

class StatusGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatusGroup
        fields = '__all__'

class OptionCategorySerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source='group.name', read_only=True)
    class Meta:
        model = OptionCategory
        fields = ['id', 'group', 'group_name', 'parent', 'name']

class StatusOptionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_id = serializers.IntegerField(source='category.id', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)

    class Meta:
        model = StatusOption
        fields = ['id', 'name', 'icon', 'group', 'group_name', 'category', 'category_name', 'category_id']

class SituationContextSerializer(serializers.ModelSerializer):
    # For reading, we might want to see which options are selected.
    # For writing, we just pass IDs usually.
    # DRF defaults to PrimaryKeyRelatedField for M2M writing.
    options_details = StatusOptionSerializer(source='options', many=True, read_only=True)
    
    class Meta:
        model = SituationContext
        fields = ['id', 'unique_signature', 'created_at', 'options', 'options_details']

class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = '__all__'
        read_only_fields = []

class PersonalGoalSerializer(serializers.ModelSerializer):
    importance_display = serializers.CharField(source='get_importance_display', read_only=True)
    
    class Meta:
        model = PersonalGoal
        fields = ['id', 'title', 'description', 'importance', 'importance_display', 
                  'is_completed', 'linked_option', 'context', 'deadline', 'created_at', 'chat_session']
        read_only_fields = []

class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = '__all__'

class AiRecommendationSerializer(serializers.ModelSerializer):
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    class Meta:
        model = AiRecommendation
        fields = ['id', 'context', 'title', 'summary', 'recommendation', 'priority', 'priority_display', 'created_at', 'chat_session']
        read_only_fields = []

class ContextPresetSerializer(serializers.ModelSerializer):
    # 'options' is a ManyToManyField. By default it expects a list of IDs.
    
    class Meta:
        model = ContextPreset
        fields = ['id', 'name', 'icon', 'options']

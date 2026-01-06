from rest_framework import serializers
from .models import StatusOption, ContextPreset

class StatusOptionSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_id = serializers.IntegerField(source='category.id', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)

    class Meta:
        model = StatusOption
        fields = ['id', 'name', 'icon', 'group', 'group_name', 'category', 'category_name', 'category_id']

class ContextPresetSerializer(serializers.ModelSerializer):
    # 'options' is a ManyToManyField. By default it expects a list of IDs, which is what we want for writing.
    # For reading, we might want details, but sticking to standard implementation for now.
    
    class Meta:
        model = ContextPreset
        fields = ['id', 'name', 'icon', 'options']

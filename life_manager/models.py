from django.db import models
from django.db.models import Q

# --- 1. Structure: Groups & Options ---

class StatusGroup(models.Model):
    """
    The 5 Main Groups: (Place, People, Time, Tools, Mood)
    Flexible to add more dimensions later.
    """
    name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.name

class OptionCategory(models.Model):
    """
    Sub-categories (e.g., Family within People, or Devices within Tools)
    """
    group = models.ForeignKey(StatusGroup, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.group.name} > {self.name}"

class StatusOption(models.Model):
    """
    The atomic building blocks: (Home, Laptop, Happy, Sunday, etc.)
    """
    group = models.ForeignKey(StatusGroup, on_delete=models.CASCADE)
    category = models.ForeignKey(OptionCategory, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, blank=True, help_text="FontAwesome icon name (e.g., 'fa-home')")

    def __str__(self):
        return f"{self.name} ({self.group.name})"

# --- 2. The Context Engine ---

class SituationContext(models.Model):
    """
    Represents a unique combination of 5 options.
    This is the core 'Situation' or 'State' of the user.
    """
    options = models.ManyToManyField(StatusOption, related_name='contexts')
    # Unique signature is a string of sorted IDs (e.g., "1-4-12-33-40")
    unique_signature = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Context: {self.unique_signature}"

# --- 3. Content & Goals ---

class Article(models.Model):
    """
    Knowledge or Notes linked to a specific unique context.
    """
    context = models.ForeignKey(SituationContext, on_delete=models.CASCADE, related_name='articles')
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class PersonalGoal(models.Model):
    """
    Goals can be linked to EITHER:
    1. A single Item (e.g., 'Drink Water' linked to 'Gym')
    2. A full Context (e.g., 'Focus Deeply' linked to 'Office + Morning + Coffee')
    """
    IMPORTANCE_CHOICES = [
        (1, 'Low'),
        (2, 'Medium'),
        (3, 'High'),
        (4, 'Critical'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    importance = models.IntegerField(choices=IMPORTANCE_CHOICES, default=2)
    is_completed = models.BooleanField(default=False)
    
    # Flexible Linking
    linked_option = models.ForeignKey(StatusOption, on_delete=models.CASCADE, null=True, blank=True, related_name='goals')
    context = models.ForeignKey(SituationContext, on_delete=models.CASCADE, null=True, blank=True, related_name='goals')
    
    deadline = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-importance', '-created_at']
    
    def __str__(self):
        return f"[{self.get_importance_display()}] {self.title}"

# --- 4. Gamification & UX ---

class Achievement(models.Model):
    """
    History of successes.
    """
    context = models.ForeignKey(SituationContext, on_delete=models.SET_NULL, null=True)
    goal = models.OneToOneField(PersonalGoal, on_delete=models.SET_NULL, null=True, blank=True)
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    reflection = models.TextField(blank=True, help_text="What did checking this off feel like?")
    
    points = models.IntegerField(default=0)
    date_achieved = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Achievement: {self.title}"

class ContextPreset(models.Model):
    """
    Quick-access presets (e.g., 'Focus Mode', 'Relax Mode', 'Commute')
    """
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, default="star")
    options = models.ManyToManyField(StatusOption)

    def __str__(self):
        return self.name

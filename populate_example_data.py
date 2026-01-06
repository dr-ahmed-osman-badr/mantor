import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mantor.settings')
django.setup()

from life_manager.models import StatusGroup, StatusOption, SituationContext, AiRecommendation

# 1. Create a Demo Group and Option
group, _ = StatusGroup.objects.get_or_create(name="Demo Mode")
option, _ = StatusOption.objects.get_or_create(
    group=group, 
    name="Showcase Example",
    defaults={'icon': 'fa-star'}
)

print(f"Created Option: {option.name} (ID: {option.id})")

# 2. Get/Create Context for this option
# We simulate the signature generation: sorted IDs joined by "-"
# For a single option, it's just the ID.
signature = str(option.id)
context, created = SituationContext.objects.get_or_create(unique_signature=signature)
context.options.add(option)

print(f"Context {'Created' if created else 'Retrieved'}: {context}")

# 3. Add a Sample Recommendation
rec, created = AiRecommendation.objects.get_or_create(
    context=context,
    title="Optimize Your Workflow",
    defaults={
        'summary': "You are in Demo Mode. Time to shine!",
        'recommendation': "This is a live example of an AI recommendation. Try completeing a goal or adding a note to see how the dashboard evolves.",
        'priority': 3 # High
    }
)

if not created:
    print("Recommendation already exists, updating...")
    rec.priority = 3
    rec.save()

print(f"Recommendation Ready: {rec.title}")
print("-" * 30)
print(f"To view this in the dashboard:")
print(f"1. Open the dashboard.")
print(f"2. Select 'Demo Mode' -> 'Showcase Example' in the filters (or use ID {option.id}).")
print(f"   URL: /?options={option.id}")

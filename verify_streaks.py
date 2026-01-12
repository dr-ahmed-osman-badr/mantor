
import os
import django
import datetime
from django.utils import timezone
from life_manager.models import StatusGroup, StatusOption, SituationContext
from life_manager.services import AnalyticsService

# python manage.py shell < verify_streaks.py

def verify_streaks():
    print("--- Verifying streaks calculation ---")
    
    # 1. Setup Data: Create a Place option "Gym Test"
    place_group, _ = StatusGroup.objects.get_or_create(name="Place")
    gym_option, _ = StatusOption.objects.get_or_create(group=place_group, name="Gym Test", defaults={'icon': 'fa-dumbbell'})
    
    # 2. Create Contexts for Today, Yesterday, and Day Before
    today = timezone.now()
    yesterday = today - datetime.timedelta(days=1)
    day_before = today - datetime.timedelta(days=2)
    
    # Create contexts (ensure unique signatures or just rely on IDs for linking)
    # We need to manually force created_at since auto_now_add=True prevents setting it on create
    
    c1 = SituationContext.objects.create(unique_signature=f"verify-streak-{today.timestamp()}")
    c1.options.add(gym_option)
    # c1.created_at is set to now automatically.
    
    c2 = SituationContext.objects.create(unique_signature=f"verify-streak-{yesterday.timestamp()}")
    c2.options.add(gym_option)
    # Hack to update created_at
    SituationContext.objects.filter(id=c2.id).update(created_at=yesterday)
    
    c3 = SituationContext.objects.create(unique_signature=f"verify-streak-{day_before.timestamp()}")
    c3.options.add(gym_option)
    SituationContext.objects.filter(id=c3.id).update(created_at=day_before)
    
    print("Created 3 consecutive days of 'Gym Test'.")
    
    # 3. Calculate Streaks
    streaks = AnalyticsService.calculate_streaks(None) # user passed as None
    print(f"Calculated Streaks: {streaks}")
    
    # 4. Verify
    gym_streak = next((s for s in streaks if s['name'] == "Gym Test"), None)
    if gym_streak:
        print(f"Found Gym Streak: {gym_streak['streak']} days")
        if gym_streak['streak'] >= 3:
            print("SUCCESS: Streak calculation correct (>=3).")
        else:
            print("FAILURE: Streak count too low.")
    else:
        print("FAILURE: Gym Streak not found.")

if __name__ == "__main__":
    verify_streaks()
elif 'django.core.management' in str(type(verify_streaks)):
    verify_streaks()

verify_streaks()

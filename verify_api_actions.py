
import os
import django
import json
from django.test import Client
from django.urls import reverse

# Setup Django (if running standalone)
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mantor.settings')
# django.setup()
# Note: running via manage.py shell makes the above unnecessary.

from life_manager.models import StatusGroup, StatusOption, PersonalGoal, Note, SituationContext, Achievement

def verify_api_actions():
    print("--- Verifying API Actions (ViewSet Model) ---")
    
    # Debug: Check reversed URLs
    try:
        print(f"DEBUG: Reversed 'life_manager:personalgoal-list': {reverse('life_manager:personalgoal-list')}")
    except Exception as e:
        print(f"DEBUG: Reverse 'life_manager:personalgoal-list' failed: {e}")

    try:
        print(f"DEBUG: Reversed 'life_manager:personalgoal-detail': {reverse('life_manager:personalgoal-detail', args=[1])}")
    except Exception as e:
        print(f"DEBUG: Reverse 'life_manager:personalgoal-detail' failed: {e}")

    client = Client()
    
    # Prerequisite: Create a Group
    group, _ = StatusGroup.objects.get_or_create(name="API Test Group")
    
    # 1. Test Add Option (POST /life_manager/options/)
    print("\n1. Testing Add Option API...")
    data = {
        'group': group.id,
        'name': 'API Option 123',
        'category_name': 'API Category' # Custom logic in Serializer
    }
    # Note: 'options' is the registered name in router.
    response = client.post('/life_manager/options/', data, content_type='application/json')
    
    if response.status_code == 201:
        print("SUCCESS: Option created via API.")
    else:
        print(f"FAILURE: Status code {response.status_code} - {response.content}")

    # 2. Test Add Goal (POST /life_manager/goals/)
    print("\n2. Testing Add Goal API...")
    data = {
        'title': 'API Goal 456',
        'importance': 3
    }
    response = client.post('/life_manager/goals/', data, content_type='application/json')
    
    if response.status_code == 201:
        print("SUCCESS: Goal created via API.")
    else:
        print(f"FAILURE: Status code {response.status_code} - {response.content}")

    # 3. Test Add Note (POST /life_manager/notes/)
    print("\n3. Testing Add Note API...")
    # Need a context first
    context, _ = SituationContext.objects.get_or_create(unique_signature="api-sig-789")
    
    data = {
        'context': context.id,
        'title': 'API Note 789',
        'content': 'Content via API.'
    }
    response = client.post('/life_manager/notes/', data, content_type='application/json')
    
    if response.status_code == 201:
        print("SUCCESS: Note created via API.")
    else:
        print(f"FAILURE: Status code {response.status_code} - {response.content}")

    # 4. Test Mark Goal Achieved (PATCH /life_manager/goals/{id}/)
    print("\n4. Testing Mark Goal Achieved API (Signal Check)...")
    goal = PersonalGoal.objects.create(title="API Goal to Achieve", context=context)
    
    data = {'is_completed': True}
    # Construct URL dynamically based on reverse if possible, or just hardcoded
    try:
        url = reverse('life_manager:personalgoal-detail', args=[goal.id])
        print(f"DEBUG: Using reversed URL for PATCH: {url}")
    except:
        url = f'/life_manager/goals/{goal.id}/'
        print(f"DEBUG: Fallback to hardcoded URL: {url}")
        
    response = client.patch(url, data, content_type='application/json')
    
    if response.status_code == 200:
        goal.refresh_from_db()
        if goal.is_completed:
            print("SUCCESS: Goal marked as completed.")
            # Verify Signal Created Achievement
            if Achievement.objects.filter(goal=goal).exists():
                 print("SUCCESS: Achievement created via Signal.")
            else:
                 print("FAILURE: Achievement NOT created (Signal failed?).")
        else:
            print("FAILURE: Goal.is_completed is False.")
    else:
        print(f"FAILURE: Status code {response.status_code} - {response.content}")

if __name__ == "__main__":
    verify_api_actions()
elif 'django.core.management' in str(type(verify_api_actions)): 
    # Just in case caller does something weird, but the main block handles direct execution 
    pass

# Execute immediately for shell redirection
verify_api_actions()

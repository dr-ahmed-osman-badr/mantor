
import os
import django
import time

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mantor.settings')
django.setup()

from life_manager.models import SituationContext, StatusOption, StatusGroup, Note

def test_home_trigger():
    print("--- Starting LIVE n8n Integration Test (Home Context - Debug) ---")
    print("Target URL: https://ahmedgarip.loca.lt/webhook/context-trigger")

    try:
        # 1. Ensure 'Place' group and 'Home' option exist
        group, _ = StatusGroup.objects.get_or_create(name="Place")
        option, _ = StatusOption.objects.get_or_create(name="Home", group=group)

        # 2. Trigger Signal by Creating Context with "Home"
        sig = f"home-debug-sig-{int(time.time())}"
        print(f"\nCreating Test Context '{sig}'...")
        
        context = SituationContext.objects.create(unique_signature=sig)
        context.options.add(option)
        context.save() 
        print("Context saved.")

        # 3. Trigger Signal by Creating Note
        print("\nCreating Test Note...")
        Note.objects.create(
            context=context, 
            title="Debug Connection", 
            content="Testing connection logging."
        )
        print("Note saved.")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    test_home_trigger()

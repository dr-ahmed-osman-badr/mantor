
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mantor.settings')
django.setup()

from life_manager.models import AiRecommendation, SituationContext

def check_latest_rec():
    print("--- Checking for New AI Recommendations ---")
    
    # Get the latest recommendation
    latest_rec = AiRecommendation.objects.order_by('-created_at').first()
    
    if latest_rec:
        print(f"FOUND Recommendation ID: {latest_rec.id}")
        print(f"Title: {latest_rec.title}")
        print(f"Summary: {latest_rec.summary}")
        print(f"Priority: {latest_rec.get_priority_display()}")
        print(f"Created At: {latest_rec.created_at}")
        print(f"Context ID: {latest_rec.context.id}")
        print("------------------------------------------------")
        print(f"Full Advice:\n{latest_rec.recommendation}")
    else:
        print("NO Recommendations found yet.")

if __name__ == "__main__":
    check_latest_rec()

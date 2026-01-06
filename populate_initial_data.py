import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mantor.settings')
django.setup()

from life_manager.models import StatusGroup, StatusOption, OptionCategory

def populate():
    print("--- Populating Initial Data ---")

    # 0. Clean up old schema
    StatusGroup.objects.filter(name__in=["Status", "Mood"]).delete()

    # 1. Define Groups and their Options
    data = {
        "Place": [
            ("Home", "fa-home", None),
            ("Office", "fa-building", None),
            ("Gym", "fa-dumbbell", None),
            ("Cafe", "fa-coffee", None),
            ("Car", "fa-car", None),
            ("Outdoors", "fa-tree", None),
            ("Library", "fa-book-open", None),
        ],
        "People": [
            ("Alone", "fa-user", None),
            ("Mom", "fa-user", "Family"),
            ("Dad", "fa-user", "Family"),
            ("Partner", "fa-heart", "Family"),
            ("Team Lead", "fa-user-tie", "Work"),
            ("Colleague", "fa-user-group", "Work"),
            ("Sarah", "fa-face-smile", "Friends"),
            ("Mike", "fa-face-grin", "Friends"),
            ("Amir", "fa-star", "Friends"), # Per user request
        ],
        "Time": [
            ("Morning", "fa-sun", None),
            ("Afternoon", "fa-cloud-sun", None),
            ("Evening", "fa-moon", None),
            ("Late Night", "fa-moon", None),
            ("Weekend", "fa-couch", None),
            ("Workday", "fa-calendar-day", None),
        ],
        "Myself": [ # Consolidated Status + Mood
            ("Busy", "fa-clock", "Status"),
            ("Free", "fa-mug-hot", "Status"),
            ("Focus", "fa-brain", "Mood"),
            ("Relax", "fa-spa", "Mood"),
            ("High Energy", "fa-bolt", "Mood"),
            ("Low Energy", "fa-battery-quarter", "Mood"),
            ("Creative", "fa-paint-brush", "Mood"),
            ("Tired", "fa-bed", "Mood"),
        ],
        "Tools": [
            ("Laptop", "fa-laptop", None),
            ("Phone", "fa-mobile", None),
            ("Tablet", "fa-tablet", None),
            ("Book", "fa-book", None),
            ("Notepad", "fa-pen", None),
            ("Headphones", "fa-headphones", None),
        ]
    }

    # 2. Iterate and Create
    for group_name, options in data.items():
        group, created = StatusGroup.objects.get_or_create(name=group_name)
        if created:
            print(f"Created Group: {group_name}")
        
        # Add Categories based on group
        # Add Categories based on group
        if group_name == "People":
             friends, _ = OptionCategory.objects.get_or_create(group=group, name="Friends")
             family, _ = OptionCategory.objects.get_or_create(group=group, name="Family")
             work, _ = OptionCategory.objects.get_or_create(group=group, name="Work")
             
             # Subcategories
             OptionCategory.objects.get_or_create(group=group, parent=friends, name="Besties")
             print("  + Categories: Friends, Family, Work")
        
        elif group_name == "Myself":
             OptionCategory.objects.get_or_create(group=group, name="Status")
             OptionCategory.objects.get_or_create(group=group, name="Mood")
             print("  + Categories: Status, Mood")

        for item in options:
            opt_name, icon, cat_name = item
            category = None
            
            if cat_name:
                # Try to find category 
                category = OptionCategory.objects.filter(group=group, name=cat_name).first()
                if not category:
                     # Create if missing (simple fallback)
                     category = OptionCategory.objects.create(group=group, name=cat_name)

            opt, created_opt = StatusOption.objects.get_or_create(
                group=group,
                category=category, 
                name=opt_name,
                defaults={'icon': icon}
            )
            if created_opt:
                print(f"  + Added Option: {opt_name}")
            else:
                print(f"  . Option exists: {opt_name}")

    print("--- Population Complete ---")

if __name__ == "__main__":
    populate()

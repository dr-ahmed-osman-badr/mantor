import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mantor.settings')
django.setup()

from life_manager.models import StatusGroup, StatusOption, SituationContext, PersonalGoal
from life_manager.services import get_situation_from_selection, get_all_relevant_goals

def run_test():
    print("--- Starting Verification ---")
    
    # 1. Setup Data
    print("[1] Creating Metadata...")
    place_group, _ = StatusGroup.objects.get_or_create(name="Place")
    mode_group, _ = StatusGroup.objects.get_or_create(name="Mode")
    
    home_opt, _ = StatusOption.objects.get_or_create(group=place_group, name="Home")
    work_opt, _ = StatusOption.objects.get_or_create(group=place_group, name="Work")
    happy_opt, _ = StatusOption.objects.get_or_create(group=mode_group, name="Happy")
    
    print(f"Created Options: {home_opt}, {work_opt}, {happy_opt}")
    
    # 2. Test Context Generation
    print("[2] Testing Context Generation...")
    # Context A: Home + Happy
    ctx_a, created_a = get_situation_from_selection([home_opt.id, happy_opt.id])
    print(f"Context A (Home+Happy): {ctx_a.unique_signature} (Created: {created_a})")
    
    # Context B: Home + Happy (Repeat)
    ctx_b, created_b = get_situation_from_selection([happy_opt.id, home_opt.id])
    print(f"Context B (Happy+Home REPEAT): {ctx_b.unique_signature} (Created: {created_b})")
    
    assert ctx_a.id == ctx_b.id, "Context Resolution Failed! A and B should be the same."
    print(">> Context Resolution PASSED")
    
    # 3. Test Goal Aggregation
    print("[3] Testing Goal Aggregation...")
    
    # Goal 1: Linked to 'Home' (Option)
    g1 = PersonalGoal.objects.create(title="Fix Sink", linked_option=home_opt, importance=2)
    
    # Goal 2: Linked to 'Work' (Option)
    g2 = PersonalGoal.objects.create(title="Finish Report", linked_option=work_opt, importance=3)
    
    # Goal 3: Linked to Context A (Home+Happy)
    g3 = PersonalGoal.objects.create(title="Smile more", context=ctx_a, importance=1)
    
    # Test Scenario: User is at HOME and HAPPY
    relevant_goals = get_all_relevant_goals(ctx_a)
    goal_titles = [g.title for g in relevant_goals]
    
    print(f"Goals found for Home+Happy: {goal_titles}")
    
    assert "Fix Sink" in goal_titles, "Missing Option-linked goal"
    assert "Smile more" in goal_titles, "Missing Context-linked goal"
    assert "Finish Report" not in goal_titles, "Incorrectly included Work goal"
    
    print(">> Goal Aggregation PASSED")
    print("--- Verification Complete ---")

if __name__ == "__main__":
    run_test()

import datetime
import requests
import json
from requests.adapters import HTTPAdapter, Retry
from django.conf import settings
from django.db.models import Count, Sum, Q
from .models import SituationContext, StatusOption, PersonalGoal, StatusGroup, Achievement, ContextPreset

# --- 1. Context Resolution Logic ---

def get_situation_from_selection(selected_option_ids):
    """
    Takes a list of StatusOption IDs and returns the SituationContext.
    If it doesn't exist, it creates it.
    """
    # 1. Filter out invalid IDs and ensure unique
    valid_ids = StatusOption.objects.filter(id__in=selected_option_ids).values_list('id', flat=True)
    sorted_ids = sorted([str(oid) for oid in valid_ids])
    
    # 2. Generate Signature
    signature = "-".join(sorted_ids)
    
    if not signature:
        return None, False

    # 3. Get or Create
    context, created = SituationContext.objects.get_or_create(unique_signature=signature)
    
    if created:
        options = StatusOption.objects.filter(id__in=valid_ids)
        context.options.add(*options)
        
    return context, created

# --- 2. Smart Defaults Logic ---

def get_smart_defaults(request):
    """
    Returns a list of Option IDs based on Time and Device.
    """
    defaults = []
    now = datetime.datetime.now()
    
    # A. Time Detection (Day of Week)
    # Assumes a group named "Time" exists
    day_name = now.strftime('%A') 
    day_option = StatusOption.objects.filter(group__name="Time", name=day_name).first()
    if day_option: 
        defaults.append(day_option.id)
    
    # B. Time Detection (Period of Day)
    hour = now.hour
    period = "Morning" if 5 <= hour < 12 else "Afternoon" if 12 <= hour < 17 else "Evening"
    period_option = StatusOption.objects.filter(group__name="Time", name=period).first()
    if period_option:
        defaults.append(period_option.id)
        
    # C. Device Detection
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    device_name = "Mobile" if "mobile" in user_agent else "Laptop"
    # Assumes a group named "Tools" exists
    device_option = StatusOption.objects.filter(group__name="Tools", name=device_name).first()
    if device_option:
        defaults.append(device_option.id)
        
    # D. Default Status (if available in Myself -> Status)
    # Optional: could auto-select 'Free' or 'Busy' based on time/calendar?
    # For now, let's leave internal state manual.
        
    return defaults

# --- 3. Goal Aggregation Logic ---

def get_all_relevant_goals(context):
    """
    Returns all uncompleted goals relevant to the given context.
    This includes goals linked to:
    1. The Context itself.
    2. ANY of the Options within the context.
    """
    if not context:
        return PersonalGoal.objects.none()

    option_ids = context.options.values_list('id', flat=True)
    
    relevant_goals = PersonalGoal.objects.filter(
        Q(linked_option_id__in=option_ids) | Q(context=context),
        is_completed=False
    ).distinct().order_by('-importance', '-created_at')
    
    return relevant_goals

# --- 4. Analytics Service ---

class AnalyticsService:
    @staticmethod
    def get_top_performing_locations():
        """Top places where achievements happened"""
        return StatusOption.objects.filter(group__name="Place") \
            .annotate(num_achievements=Count('contexts__achievement')) \
            .order_by('-num_achievements')

    @staticmethod
    def get_status_productivity_stats():
        """Status vs Points (Busy/Free) - Now under Myself group"""
        return StatusOption.objects.filter(group__name="Myself", category__name="Status") \
            .annotate(total_points=Sum('contexts__achievement__points')) \
            .order_by('-total_points')

    @staticmethod
    def get_mood_productivity_stats():
        """Mood vs Points (Happy/Focus) - Now under Myself group"""
        return StatusOption.objects.filter(group__name="Myself", category__name="Mood") \
            .annotate(total_points=Sum('contexts__achievement__points')) \
            .order_by('-total_points')
            
    @staticmethod
    def calculate_points(importance_level):
        points_map = {
            1: 5,   # Low
            2: 15,  # Medium
            3: 35,  # High
            4: 100, # Critical
        }
        return points_map.get(importance_level, 0)

    @staticmethod
    def calculate_streaks(user, days_back=30):
        """
        Calculates active streaks for 'Place' or 'Activity' options.
        Returns a list of dicts: [{'name': 'Gym', 'days': 3, 'icon': 'fa-dumbbell'}]
        """
        # 1. Get recent contexts for this user (assuming single user for now or filtering if needed)
        # Note: SituationContext doesn't have a direct user link in this simplistic model, 
        # but realistically we'd filter by user. For now, we take all.
        
        today = datetime.date.today()
        start_date = today - datetime.timedelta(days=days_back)
        
        # Get all contexts created in range
        active_options = StatusOption.objects.filter(
            group__name__in=["Place", "Activity"],
            contexts__created_at__date__gte=start_date
        ).distinct()
        
        streaks = []
        
        for option in active_options:
            # Get dates where this option was used
            dates_used = SituationContext.objects.filter(
                options=option,
                created_at__date__gte=start_date
            ).dates('created_at', 'day', order='DESC')
            
            # Simple Streak Logic: Count consecutive days going back from today/yesterday
            current_streak = 0
            check_date = today
            
            # Convert QuerySet of dates to list of string or actual date objs for comparison
            # dates_used returns list of date objects
            used_dates_set = set(dates_used)
            
            # Check if active today
            if check_date in used_dates_set:
                current_streak += 1
                check_date -= datetime.timedelta(days=1)
            elif (check_date - datetime.timedelta(days=1)) in used_dates_set:
                # If not today, but yesterday, streak is still alive
                check_date -= datetime.timedelta(days=1)
                current_streak += 1
                check_date -= datetime.timedelta(days=1)
            else:
                # Streak broken or not started recently
                continue
                
            # Count backwards
            while check_date in used_dates_set:
                current_streak += 1
                check_date -= datetime.timedelta(days=1)
                
            if current_streak > 1:
                streaks.append({
                    'name': option.name,
                    'icon': option.icon if option.icon else "fa-fire",
                    'streak': current_streak
                })
                
        return sorted(streaks, key=lambda x: x['streak'], reverse=True)

    @staticmethod
    def get_gamification_profile(user):
        """
        Returns simple badges/stats.
        """
        # Total Points
        total_points = Achievement.objects.aggregate(total=Sum('points'))['total'] or 0
        
        # Badges
        badges = []
        
        # 1. Newcomer
        if SituationContext.objects.exists():
            badges.append({'name': 'Started Journey', 'icon': 'fa-flag', 'color': 'text-green-500'})
            
        # 2. High Achiever
        if total_points > 500:
             badges.append({'name': 'High Achiever', 'icon': 'fa-trophy', 'color': 'text-yellow-500'})
             
        # 3. Night Owl (Contexts after 11 PM)
        # Filter logic is a bit complex for SQLite time extraction sometimes, doing python check for prototype
        night_contexts = SituationContext.objects.filter(created_at__hour__gte=23).count()
        if night_contexts > 5:
             badges.append({'name': 'Night Owl', 'icon': 'fa-moon', 'color': 'text-purple-500'})
             
        return {
            'total_points': total_points,
            'badges': badges
        }

# --- 5. N8n Integration Service ---

import threading
import logging

logger = logging.getLogger(__name__)

class N8nIntegrationService:
    # Centralized N8N Base URL
    N8N_BASE_URL = "http://localhost:5678"

    N8N_WEBHOOK_URL = f"{N8N_BASE_URL}/webhook/context-trigger"
    N8N_CHAT_WEBHOOK_URL = f"{N8N_BASE_URL}/webhook/chat-trigger"

    @staticmethod
    def post_with_retry(url, payload, description, timeout=30):
        """
        Sends a POST request with robust retry logic (Exponential Backoff).
        """
        session = requests.Session()
        retries = Retry(
            total=5,
            backoff_factor=1,  # Wait 1s, 2s, 4s, 8s, 16s...
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        session.mount('https://', HTTPAdapter(max_retries=retries))
        session.mount('http://', HTTPAdapter(max_retries=retries))

        try:
            logger.info(f"--- Sending {description} to n8n: {url} ---")
            response = session.post(url, json=payload, timeout=timeout)
            response.raise_for_status()
            logger.info(f"n8n Response for {description}: {response.status_code}")
            return response
        except requests.exceptions.RetryError:
            logger.error(f"Max retries exceeded for {description} to {url}")
            raise
        except Exception as e:
            logger.error(f"Error triggering n8n for {description}: {e}")
            raise

    @staticmethod
    def _send_payload(url, payload, description):
        """
        Internal worker to send payload synchronously.
        Meant to be run in a thread.
        """
        try:
           N8nIntegrationService.post_with_retry(url, payload, description)
        except Exception:
            pass # Error already logged in helper

    @staticmethod
    def trigger_chat_response(session_id, message_content):
        """
        Sends chat message to n8n for AI response (Async).
        Updated to handle response and save it as an assistant message.
        """
        # Fetch History
        from .models import ChatMessage # Import locally
        # Get last 10 messages (excluding the current one if it was just saved? 
        # Actually usually this triggers on post_save of the USER message.
        # So the user message IS in the DB.
        # We want everything leading up to this point. 
        # But wait, trigger_chat_message sends "message_content". 
        # If we include history, we should include the current message in history or separately?
        # Standard generic AI prompts usually take a list of messages.
        # Let's send history separately as 'history'.
        
        last_messages = ChatMessage.objects.filter(session_id=session_id).order_by('-timestamp')[:10]
        # Reverse to chronological order
        history = [
            {"role": msg.role, "content": msg.content} 
            for msg in reversed(last_messages)
        ]

        payload = {
            "session_id": session_id,
            "message": message_content,
            "history": history,
            "timestamp": datetime.datetime.now().isoformat()
        }

        def _send_and_save_reply():
            try:
                response = N8nIntegrationService.post_with_retry(
                    N8nIntegrationService.N8N_CHAT_WEBHOOK_URL, 
                    payload, 
                    "Chat",
                    timeout=60 # Long timeout for AI generation
                )
                
                # Parse Response
                data = response.json()

                # Robust check for "Workflow was started" or invalid responses
                if data.get("message") == "Workflow was started":
                    logger.warning(f"Session {session_id}: Received 'Workflow was started'. Webhook is not configured to wait for last node.")
                    return # Do not save this as a chat message

                ai_text = data.get('response', '') 
                
                if not ai_text:
                    # Fallback if raw text returned or different key
                    ai_text = data.get('output', '')
                
                if not ai_text and 'text' in data:
                     ai_text = data['text']

                if not ai_text:
                     # Final fallback: dump json if it's not the "Workflow started" message
                     ai_text = json.dumps(data)

                if ai_text:
                    from .models import ChatMessage # Import locally to avoid circular dependency
                    ChatMessage.objects.create(
                        session_id=session_id,
                        role='assistant',
                        content=ai_text
                    )
                    logger.info(f"Saved AI response for Session {session_id}")

            except Exception as e:
                logger.error(f"Error in Chat N8N flow: {e}")

        
        thread = threading.Thread(target=_send_and_save_reply)
        thread.start()

    @staticmethod
    def trigger_context_processing(context_id):
        """
        Sends context data to n8n for AI processing (Async).
        """
        try:
            context = SituationContext.objects.get(id=context_id)
        except SituationContext.DoesNotExist:
            logger.warning(f"Context {context_id} not found for n8n trigger.")
            return

        # 1. Prepare Data Payload
        options_data = [
            {
                "id": opt.id, 
                "name": opt.name, 
                "group": opt.group.name, 
                "category": opt.category.name if opt.category else None
            } 
            for opt in context.options.all()
        ]

        # Fetch related content for context (Notes & Goals)
        # We limit to recent or active ones to avoid huge payloads
        notes = context.notes.all().order_by('-created_at')[:5]
        goals = context.goals.filter(is_completed=False)[:5]

        payload = {
            "context_id": context.id,
            "unique_signature": context.unique_signature,
            "created_at": context.created_at.isoformat(),
            "options": options_data,
            "notes": [{"title": n.title, "content": n.content} for n in notes],
            "active_goals": [{"title": g.title, "importance": g.get_importance_display()} for g in goals],
            "timestamp": datetime.datetime.now().isoformat()
        }

        # 2. Send Webhook via Thread
        thread = threading.Thread(
            target=N8nIntegrationService._send_payload,
            args=(N8nIntegrationService.N8N_WEBHOOK_URL, payload, "Context")
        )
        thread.start()

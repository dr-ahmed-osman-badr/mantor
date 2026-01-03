# Context-Aware Life Manager

A Django-based intelligent system that manages your life's context, goals, and productivity. It acts as a "Second Brain" that knows *where* you are, *who* you are with, and *what* you need to do.

---

## 🌟 Detailed Features

### 1. The Context Engine (5-Dimensional Logic)
The core of the system is a sophisticated engine that resolves your current state into a **Unique Signature**.
-   **Multi-Dimensional**: Tracks 5 key dimensions:
    -   📍 **Place**: (Home, Office, Gym, Cafe)
    -   👥 **People**: (Alone, Family, Boss, Team, Friends)
    -   ⏳ **Time**: (Morning, Evening, Weekend, Specific Days)
    -   😊 **Mood**: (Focus, Relax, High Energy, Low Energy)
    -   💻 **Tools**: (Laptop, Phone, Car, Tablet)
-   **Signature Resolution**: Automatically generates a hash (e.g., `1-4-12-30`) representing the combination. `Home + Alone` is treated differently from `Home + Family`.
-   **Smart Defaults**: Uses heuristic logic to guess your context based on:
    -   *Time of Day*: Auto-selects "Morning" or "Evening".
    -   *Device*: Detects if you are on "Mobile" or "Desktop".

### 2. Context-Aware Goals
Goals are dynamic and context-sensitive. They are not static to-do lists.
-   **Flexible Linking**:
    -   *Option-Based*: Link a goal to "Office". It appears *whenever* you are at the office, regardless of other factors.
    -   *Context-Based*: Link a goal to "Office + Boss". It appears *only* when both conditions are met.
-   **Priority & Urgency**: Visual indicators (Red/Orange/Blue) for Critical, High, and Medium priority goals.
-   **Cross-Context Aggregation**: The dashboard intelligently merges goals from all your current active dimensions into one unified view.

### 3. Knowledge Base & Memory
-   **Contextual Articles**: Write notes or articles tagged to a specific context (e.g., "Server Debugging Guide" linked to "Work + Laptop").
-   **Auto-Surface**: The next time you enter that context, the system automatically retrieves these notes.

### 4. Productivity Analytics
-   **Gamified Achievements**: Completing a goal stores a snapshot of the context, awarding points based on difficulty.
-   **Heatmaps**: "Top Performing Places" shows you where you are most productive.
-   **Mood Correlation**: "Best Mood for Focus" analyzes which emotional state leads to the highest point yield.

### 5. Premium UX
-   **Dark Mode**: Sleek, modern TailwindCSS interface.
-   **Quick Presets**: Customizable "One-Click" buttons for common states (e.g., "Deep Work Mode", "Commute").

---

## 🛠️ How to Use

### Step 1: Initial Setup
1.  **Run Migrations**: `python manage.py migrate`
2.  **Create Superuser**: `python manage.py createsuperuser`
3.  **Run Server**: `python manage.py runserver`

### Step 2: Define Your World (Admin Panel)
Go to `http://localhost:8000/admin` and populate the basics:
1.  **Status Groups**: Create groups if they don't exist (Place, People, Time, Tools, Mood).
2.  **Status Options**: Add your real-life options:
    -   *Place*: Home, Office, Gym.
    -   *People*: Alone, Partner, Team.
    -   *Tools*: Laptop, Phone.

### Step 3: Create Presets (Optional but Recommended)
In the Admin panel, create **Context Presets** for accurate quick-switching:
-   **Name**: "Work Mode"
-   **Options**: Select [Office, Laptop, Team, Focus]
-   **Icon**: `fa-briefcase`

### Step 4: Daily Usage (The Dashboard)
Go to `http://localhost:8000/`.
1.  **Check In**: Click a Preset OR use the dropdowns to set your current state.
2.  **View Goals**: The system will fetch all relevant goals.
3.  **Work**: As you complete tasks, click "Complete".
4.  **Reflect**: The system logs this as an Achievement.
5.  **Analyze**: Visit the "Analytics" tab to see your progress over time.

---

## 💡 Real-World Use Cases

### Case A: The "Deep Work" Session
*   **Context**: Place: *Office* | Tool: *Laptop* | Mood: *Focus* | People: *Alone*
*   **System Action**:
    1.  Hides all "Home" chores.
    2.  Surfaces goals like "Finish API Documentation" (linked to Laptop) and "Review Q3 Strategy" (linked to Office).
    3.  Shows "Python Cheat Sheet" article.

### Case B: The "Gym Rat"
*   **Context**: Place: *Gym* | Tool: *Phone* | Mood: *High Energy*
*   **System Action**:
    1.  Shows goals: "Do 3 sets of Squats", "Drink 1L Water".
    2.  Hides all work-related texts/articles to prevent distraction.

### Case C: The "Commute"
*   **Context**: Place: *Car* | Tool: *Phone* | People: *Alone*
*   **System Action**:
    1.  Surfaces "Audiobook List" article.
    2.  Shows goal: "Listen to Podcast Ep. 45".
    3.  Negative Goal / Warning: "Don't Check Email".

### Case D: The "Social Weekend"
*   **Context**: Time: *Weekend* | People: *Friends* | Place: *Cafe*
*   **System Action**:
    1.  Surfaces "Restaurant Recommendations" article.
    2.  Shows goal: "Ask Ahmed about his new startup".

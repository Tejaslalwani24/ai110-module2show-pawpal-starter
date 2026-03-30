from pawpal_system import Owner, Pet, Task, TaskCategory, Scheduler

# --- Setup ---
owner = Owner(name="Alex", time_available=90)

dog = Pet(name="Buddy", species="Dog", breed="Labrador", age=3)
cat = Pet(name="Mochi", species="Cat", breed="Siamese", age=5)

dog.add_task(Task(name="Morning Walk",    category=TaskCategory.WALK,       duration=30, priority=1, frequency="daily",  scheduled_time="07:00"))
dog.add_task(Task(name="Breakfast",       category=TaskCategory.FEED,       duration=10, priority=1, frequency="daily",  scheduled_time="07:30"))
dog.add_task(Task(name="Flea Medication", category=TaskCategory.MEDS,       duration=5,  priority=1, frequency="weekly", scheduled_time="08:00"))
dog.add_task(Task(name="Fetch in Yard",   category=TaskCategory.ENRICHMENT, duration=20, priority=2, frequency="daily",  scheduled_time="16:00"))

# [STEP 4] Mochi's Breakfast deliberately clashes with Buddy's at 07:30
cat.add_task(Task(name="Breakfast",       category=TaskCategory.FEED,       duration=5,  priority=1, frequency="daily",  scheduled_time="07:30"))
cat.add_task(Task(name="Laser Play",      category=TaskCategory.ENRICHMENT, duration=10, priority=2, frequency="daily",  scheduled_time="19:00"))
cat.add_task(Task(name="Brushing",        category=TaskCategory.GROOMING,   duration=15, priority=3, frequency="weekly", scheduled_time=""))

owner.add_pet(dog)
owner.add_pet(cat)
scheduler = Scheduler(owner)

# ── Step 3: mark a task complete, then reschedule ───────────────────────────
print("=== Step 3: Recurring task automation ===")
buddy_walk = dog.tasks[0]
print(f"Before: '{buddy_walk.name}' completed={buddy_walk.completed}, last_done='{buddy_walk.last_done}'")

buddy_walk.mark_complete(on_date="2026-03-29")   # simulate it was done yesterday
messages = scheduler.reschedule_recurring()

print(f"Rescheduled: {messages}")
new_walk = dog.tasks[-1]   # newly appended task
print(f"After : '{new_walk.name}' completed={new_walk.completed}, last_done='{new_walk.last_done}'")

# ── Step 4: time-slot conflict detection ────────────────────────────────────
print("\n=== Step 4: Time-slot conflict detection ===")
time_conflicts = scheduler.detect_time_conflicts()
if time_conflicts:
    for warning in time_conflicts:
        print(f"  WARNING: {warning}")
else:
    print("  No time conflicts found.")

# ── Step 5: full plan (shows both conflict types + reasoning) ───────────────
print()
plan = scheduler.generate_plan()
print(plan.display())

# ── Tests: run pytest to confirm nothing broke ──────────────────────────────

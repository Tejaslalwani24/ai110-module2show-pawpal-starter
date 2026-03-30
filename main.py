from pawpal_system import Owner, Pet, Task, TaskCategory, Scheduler

# --- Setup owner ---
owner = Owner(name="Alex", time_available=90, preferences=["morning walks", "no loud grooming"])

# --- Setup pets ---
dog = Pet(name="Buddy", species="Dog", breed="Labrador", age=3)
cat = Pet(name="Mochi", species="Cat", breed="Siamese", age=5)

# --- Add tasks to Buddy (dog) ---
dog.add_task(Task(name="Morning Walk",    category=TaskCategory.WALK,       duration=30, priority=1, frequency="daily"))
dog.add_task(Task(name="Breakfast",       category=TaskCategory.FEED,       duration=10, priority=1, frequency="daily"))
dog.add_task(Task(name="Flea Medication", category=TaskCategory.MEDS,       duration=5,  priority=1, frequency="weekly"))
dog.add_task(Task(name="Fetch in Yard",   category=TaskCategory.ENRICHMENT, duration=20, priority=2, frequency="daily"))

# --- Add tasks to Mochi (cat) ---
cat.add_task(Task(name="Breakfast",       category=TaskCategory.FEED,       duration=5,  priority=1, frequency="daily"))
cat.add_task(Task(name="Brushing",        category=TaskCategory.GROOMING,   duration=15, priority=3, frequency="weekly"))
cat.add_task(Task(name="Laser Play",      category=TaskCategory.ENRICHMENT, duration=10, priority=2, frequency="daily"))

# --- Register pets with owner ---
owner.add_pet(dog)
owner.add_pet(cat)

# --- Generate plan ---
scheduler = Scheduler(owner)
plan = scheduler.generate_plan()

# --- Print results ---
print(f"Owner : {owner}")
print(f"Pets  : {', '.join(p.name for p in owner.pets)}")
print()
print(plan.display())

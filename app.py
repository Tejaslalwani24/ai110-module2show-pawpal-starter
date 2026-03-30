import streamlit as st
from pawpal_system import Owner, Pet, Task, TaskCategory, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = None

CATEGORY_MAP = {
    "Walk":       TaskCategory.WALK,
    "Feed":       TaskCategory.FEED,
    "Meds":       TaskCategory.MEDS,
    "Enrichment": TaskCategory.ENRICHMENT,
    "Grooming":   TaskCategory.GROOMING,
}
PRIORITY_MAP    = {"High": 1, "Medium": 2, "Low": 3}
PRIORITY_LABELS = {1: "High", 2: "Medium", 3: "Low"}

# ---------------------------------------------------------------------------
# Owner + Pet setup
# ---------------------------------------------------------------------------
st.subheader("Owner & Pet Info")

with st.form("owner_form"):
    col1, col2 = st.columns(2)
    with col1:
        owner_name     = st.text_input("Owner name", value="Jordan")
        time_available = st.number_input("Time available today (min)", min_value=10, max_value=480, value=90)
    with col2:
        pet_name = st.text_input("Pet name", value="Mochi")
        species  = st.selectbox("Species", ["Dog", "Cat", "Other"])
        breed    = st.text_input("Breed", value="Mixed")
        age      = st.number_input("Age (years)", min_value=0, max_value=30, value=2)

    if st.form_submit_button("Save Owner & Pet"):
        pet   = Pet(name=pet_name, species=species, breed=breed, age=int(age))
        owner = Owner(name=owner_name, time_available=int(time_available))
        owner.add_pet(pet)
        st.session_state.owner = owner
        st.success(f"Saved — Owner: {owner_name} | Pet: {pet_name} ({species})")

# ---------------------------------------------------------------------------
# Everything below only renders once an owner exists
# ---------------------------------------------------------------------------
if st.session_state.owner is None:
    st.info("Fill in the Owner & Pet form above to get started.")
    st.stop()

owner     = st.session_state.owner
pet       = owner.pets[0]
scheduler = Scheduler(owner)

# ---------------------------------------------------------------------------
# Add task
# ---------------------------------------------------------------------------
st.divider()
st.subheader(f"Tasks for {pet.name}")

with st.form("task_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        task_name      = st.text_input("Task name", value="Morning walk")
        category_label = st.selectbox("Category", list(CATEGORY_MAP.keys()))
    with col2:
        duration       = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
        priority_label = st.selectbox("Priority", ["High", "Medium", "Low"])
    with col3:
        frequency      = st.selectbox("Frequency", ["daily", "weekly", "as-needed"])
        scheduled_time = st.text_input("Start time (HH:MM, optional)", value="")
        notes          = st.text_input("Notes (optional)", value="")

    if st.form_submit_button("Add Task"):
        new_task = Task(
            name=task_name,
            category=CATEGORY_MAP[category_label],
            duration=int(duration),
            priority=PRIORITY_MAP[priority_label],
            frequency=frequency,
            scheduled_time=scheduled_time.strip(),
            notes=notes,
        )
        pet.add_task(new_task)
        st.success(f"Added: {task_name} ({duration} min, {priority_label} priority)")

# ---------------------------------------------------------------------------
# Task table — sorted by scheduled_time via Scheduler.sort_by_time()
# ---------------------------------------------------------------------------
if pet.tasks:
    sorted_tasks = scheduler.sort_by_time(pet.tasks)
    table_rows = [
        {
            "Name":     t.name,
            "Category": t.category.value,
            "Time":     t.scheduled_time or "—",
            "Duration": f"{t.duration} min",
            "Priority": PRIORITY_LABELS[t.priority],
            "Frequency": t.frequency,
            "Done":     "Yes" if t.completed else "No",
        }
        for t in sorted_tasks
    ]
    st.write("Current tasks (sorted by start time):")
    st.table(table_rows)

    # Per-pet filter controls
    with st.expander("Filter tasks"):
        filter_status = st.radio(
            "Show", ["All", "Pending only", "Completed only"], horizontal=True
        )
        status_map = {"All": None, "Pending only": False, "Completed only": True}
        filtered = scheduler.filter_tasks(
            pet_name=pet.name, completed=status_map[filter_status]
        )
        if filtered:
            st.table([
                {
                    "Name":     t.name,
                    "Category": t.category.value,
                    "Duration": f"{t.duration} min",
                    "Done":     "Yes" if t.completed else "No",
                }
                for t in filtered
            ])
        else:
            st.info("No tasks match the selected filter.")
else:
    st.info("No tasks yet. Add one above.")

# ---------------------------------------------------------------------------
# Generate schedule
# ---------------------------------------------------------------------------
st.divider()
st.subheader("Generate Today's Schedule")

if st.button("Generate Schedule"):
    if not pet.tasks:
        st.warning("Add at least one task before generating a schedule.")
    else:
        plan = scheduler.generate_plan()

        # -- Conflict warnings (shown first so the owner sees them immediately)
        if plan.conflicts:
            for warning in plan.conflicts:
                st.warning(f"Conflict detected: {warning}")
            st.caption(
                "Tip: fix conflicting tasks above before finalising your plan."
            )

        # -- Time budget summary
        budget_pct = int(plan.total_duration() / owner.time_available * 100)
        if plan.scheduled_tasks:
            st.success(
                f"Scheduled {len(plan.scheduled_tasks)} task(s) — "
                f"{plan.total_duration()} / {owner.time_available} min "
                f"({budget_pct}% of your day used)"
            )
        else:
            st.error("No tasks could be scheduled. Check time budget or task durations.")

        # -- Scheduled tasks table (priority-sorted by Scheduler)
        if plan.scheduled_tasks:
            st.markdown("**Scheduled tasks**")
            st.table([
                {
                    "Name":      t.name,
                    "Category":  t.category.value,
                    "Time":      t.scheduled_time or "—",
                    "Duration":  f"{t.duration} min",
                    "Priority":  PRIORITY_LABELS[t.priority],
                    "Frequency": t.frequency,
                }
                for t in plan.scheduled_tasks
            ])

        # -- Skipped tasks
        if plan.skipped_tasks:
            with st.expander(f"Skipped tasks ({len(plan.skipped_tasks)})"):
                for t in plan.skipped_tasks:
                    st.markdown(
                        f"- **{t.name}** ({t.category.value}) — "
                        f"{t.duration} min | {PRIORITY_LABELS[t.priority]} priority"
                    )

        # -- Reasoning
        st.info(f"Reasoning: {plan.reasoning}")

        # -- Reschedule recurring tasks after viewing the plan
        messages = scheduler.reschedule_recurring()
        if messages:
            with st.expander("Recurring tasks rescheduled"):
                for msg in messages:
                    st.markdown(f"- {msg}")

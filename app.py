import streamlit as st

# Step 1: Import backend classes
from pawpal_system import Owner, Pet, Task, TaskCategory, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ---------------------------------------------------------------------------
# Step 2: Session state — initialise once, persist across reruns
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = None   # set after owner form is submitted

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

    submitted = st.form_submit_button("Save Owner & Pet")
    if submitted:
        # Step 3: Wire form submission to backend classes
        pet   = Pet(name=pet_name, species=species, breed=breed, age=int(age))
        owner = Owner(name=owner_name, time_available=int(time_available))
        owner.add_pet(pet)
        st.session_state.owner = owner
        st.success(f"Saved! Owner: {owner_name} | Pet: {pet_name} ({species})")

# ---------------------------------------------------------------------------
# Task management (only shown once owner exists)
# ---------------------------------------------------------------------------
if st.session_state.owner is not None:
    owner = st.session_state.owner
    # Always use the first pet for simplicity
    pet = owner.pets[0]

    st.divider()
    st.subheader(f"Tasks for {pet.name}")

    CATEGORY_MAP = {
        "Walk":       TaskCategory.WALK,
        "Feed":       TaskCategory.FEED,
        "Meds":       TaskCategory.MEDS,
        "Enrichment": TaskCategory.ENRICHMENT,
        "Grooming":   TaskCategory.GROOMING,
    }
    PRIORITY_MAP = {"High": 1, "Medium": 2, "Low": 3}

    with st.form("task_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            task_name = st.text_input("Task name", value="Morning walk")
            category  = st.selectbox("Category", list(CATEGORY_MAP.keys()))
        with col2:
            duration  = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
            priority  = st.selectbox("Priority", ["High", "Medium", "Low"])
        with col3:
            frequency = st.selectbox("Frequency", ["daily", "weekly", "as-needed"])
            notes     = st.text_input("Notes (optional)", value="")

        add_task = st.form_submit_button("Add Task")
        if add_task:
            # Step 3: Wire to Pet.add_task()
            new_task = Task(
                name=task_name,
                category=CATEGORY_MAP[category],
                duration=int(duration),
                priority=PRIORITY_MAP[priority],
                frequency=frequency,
                notes=notes,
            )
            pet.add_task(new_task)
            st.success(f"Added: {task_name} ({duration} min, {priority} priority)")

    # Show current task list
    if pet.tasks:
        st.write("Current tasks:")
        st.table([t.to_dict() for t in pet.tasks])
    else:
        st.info("No tasks yet. Add one above.")

    # -----------------------------------------------------------------------
    # Schedule generation
    # -----------------------------------------------------------------------
    st.divider()
    st.subheader("Generate Today's Schedule")

    if st.button("Generate Schedule"):
        if not pet.tasks:
            st.warning("Add at least one task before generating a schedule.")
        else:
            # Step 3: Wire to Scheduler.generate_plan()
            scheduler = Scheduler(owner)
            plan      = scheduler.generate_plan()

            st.success(f"Scheduled {len(plan.scheduled_tasks)} task(s) "
                       f"({plan.total_duration()} / {owner.time_available} min used)")

            if plan.scheduled_tasks:
                st.markdown("**Scheduled tasks:**")
                for t in plan.scheduled_tasks:
                    st.markdown(f"- **{t.name}** ({t.category.value}) — {t.duration} min | priority {t.priority}")

            if plan.skipped_tasks:
                st.markdown("**Skipped (not enough time):**")
                for t in plan.skipped_tasks:
                    st.markdown(f"- {t.name} ({t.duration} min)")

            st.info(f"Reasoning: {plan.reasoning}")

else:
    st.info("Fill in the Owner & Pet form above to get started.")

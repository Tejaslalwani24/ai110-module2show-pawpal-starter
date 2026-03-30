# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

---

## Smarter Scheduling

Beyond the basic greedy planner, the scheduler includes four algorithmic improvements:

### 1. Priority + duration sort
Tasks are ordered by a four-level key: **priority → category rank → duration → name**.
Within the same priority tier, shorter tasks are scheduled first — a bin-packing heuristic that fits the maximum number of tasks into the owner's time budget.
Category rank enforces real-world urgency: MEDS → FEED → WALK → ENRICHMENT → GROOMING.

### 2. Per-pet and status filtering
`filter_tasks(pet_name, completed)` lets the UI or terminal show tasks scoped to a single pet or filtered by completion status (pending only, done only, or all).
`sort_by_time()` orders any task list chronologically by `scheduled_time` ("HH:MM"), placing tasks with no assigned time at the end.

### 3. Recurring task automation
Every `Task` has a `frequency` field (`"daily"`, `"weekly"`, `"as-needed"`) and a `last_done` date.
`Scheduler.is_due_today()` uses Python's `timedelta` to skip tasks not yet due (e.g. a weekly flea treatment done 2 days ago).
After completing a recurring task, `reschedule_recurring()` automatically replaces it with a fresh copy due on the correct next date — no manual re-entry needed.

### 4. Conflict detection
Two independent checks run before the greedy fill:
- **Category conflicts** — warns if the same pet has two tasks of the same category (e.g. two `FEED` entries), which likely indicates a data-entry mistake.
- **Time-slot conflicts** — warns if any two tasks (across any pet) share the same `scheduled_time`, so the owner knows they cannot be done simultaneously.

Both checks return plain warning strings that appear in the daily plan output and the Streamlit UI — the scheduler never crashes on a conflict.

from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field
from datetime import date as _date, timedelta
import uuid


class TaskCategory(Enum):
    WALK = "walk"
    FEED = "feed"
    MEDS = "meds"
    ENRICHMENT = "enrichment"
    GROOMING = "grooming"


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """A single pet-care activity."""
    name: str
    category: TaskCategory
    duration: int           # minutes
    priority: int           # 1 = high, 2 = medium, 3 = low
    frequency: str = "daily"        # "daily" | "weekly" | "as-needed"
    completed: bool = False
    notes: str = ""
    last_done: str = ""             # ISO date of last completion
    scheduled_time: str = ""        # optional start time in "HH:MM" format
    task_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    # -- mutation helpers ---------------------------------------------------

    def mark_complete(self, on_date: str | None = None) -> None:
        """Mark this task as done and record the completion date."""
        self.completed = True
        self.last_done = on_date or str(_date.today())

    def mark_incomplete(self) -> None:
        """Reset completion status (does not clear last_done)."""
        self.completed = False

    # [STEP 3] recurring task automation ------------------------------------

    def next_occurrence(self) -> Task | None:
        """
        Return a fresh copy of this task due on its next occurrence date,
        or None if the task is 'as-needed' (no automatic recurrence).

        Uses timedelta so the due date is always exact:
          daily  -> last_done + 1 day
          weekly -> last_done + 7 days
        """
        from dataclasses import replace  # local import avoids circular deps

        interval_days = {"daily": 1, "weekly": 7}.get(self.frequency)
        if interval_days is None:
            return None  # "as-needed" — no automatic next occurrence

        base = _date.fromisoformat(self.last_done) if self.last_done else _date.today()
        next_due = base + timedelta(days=interval_days)

        return replace(
            self,
            task_id=str(uuid.uuid4())[:8],   # new unique ID
            completed=False,
            last_done=str(next_due),          # tracks when it becomes due
        )

    # -- serialisation ------------------------------------------------------

    def to_dict(self) -> dict:
        """Serialize the task to a plain dictionary."""
        return {
            "task_id":   self.task_id,
            "name":      self.name,
            "category":  self.category.value,
            "duration":  self.duration,
            "priority":  self.priority,
            "frequency": self.frequency,
            "completed": self.completed,
            "last_done":      self.last_done,
            "scheduled_time": self.scheduled_time,
            "notes":          self.notes,
        }

    def __str__(self) -> str:
        """Return a compact one-line representation of the task."""
        status = "done" if self.completed else "todo"
        return (f"[{status}] {self.name} ({self.category.value}) "
                f"- {self.duration} min | priority {self.priority}")


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    """Stores pet profile and owns the list of care tasks."""
    name: str
    species: str
    breed: str
    age: int
    tasks: list[Task] = field(default_factory=list)

    # -- task management ----------------------------------------------------

    def add_task(self, task: Task) -> None:
        """Add a task to this pet's list (no duplicates by task_id)."""
        if any(t.task_id == task.task_id for t in self.tasks):
            raise ValueError(f"Task '{task.task_id}' already exists for {self.name}.")
        self.tasks.append(task)

    def remove_task(self, task_id: str) -> None:
        """Remove a task by its ID; raises KeyError if not found."""
        for i, t in enumerate(self.tasks):
            if t.task_id == task_id:
                self.tasks.pop(i)
                return
        raise KeyError(f"No task with id '{task_id}' found for {self.name}.")

    def get_task(self, task_id: str) -> Task:
        """Return a single task by ID."""
        for t in self.tasks:
            if t.task_id == task_id:
                return t
        raise KeyError(f"Task '{task_id}' not found.")

    def get_pending_tasks(self) -> list[Task]:
        """Return only tasks not yet completed."""
        return [t for t in self.tasks if not t.completed]

    # -- info ---------------------------------------------------------------

    def get_info(self) -> str:
        """Return a summary string of the pet's profile and task count."""
        return (f"{self.name} | {self.species} ({self.breed}), "
                f"age {self.age} | {len(self.tasks)} task(s) registered")

    def __str__(self) -> str:
        """Delegate to get_info() for the string representation."""
        return self.get_info()


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

@dataclass
class Owner:
    """Manages multiple pets and provides cross-pet task access."""
    name: str
    time_available: int          # total minutes available per day
    preferences: list[str] = field(default_factory=list)
    pets: list[Pet] = field(default_factory=list)

    # -- pet management -----------------------------------------------------

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        if any(p.name == pet.name for p in self.pets):
            raise ValueError(f"A pet named '{pet.name}' is already registered.")
        self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> None:
        """Remove a pet by name."""
        for i, p in enumerate(self.pets):
            if p.name == pet_name:
                self.pets.pop(i)
                return
        raise KeyError(f"No pet named '{pet_name}' found.")

    def get_pet(self, pet_name: str) -> Pet:
        """Return a pet by name."""
        for p in self.pets:
            if p.name == pet_name:
                return p
        raise KeyError(f"Pet '{pet_name}' not found.")

    # -- cross-pet task access ----------------------------------------------

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all pets."""
        return [task for pet in self.pets for task in pet.tasks]

    def get_all_pending_tasks(self) -> list[Task]:
        """Return all incomplete tasks across all pets."""
        return [task for pet in self.pets for task in pet.get_pending_tasks()]

    def __str__(self) -> str:
        """Return a summary string of the owner's profile."""
        return (f"Owner: {self.name} | {len(self.pets)} pet(s) | "
                f"{self.time_available} min/day available")


# ---------------------------------------------------------------------------
# DailyPlan
# ---------------------------------------------------------------------------

@dataclass
class DailyPlan:
    """Output of the Scheduler: what to do today and why."""
    date: str = field(default_factory=lambda: str(_date.today()))
    scheduled_tasks: list[Task] = field(default_factory=list)
    skipped_tasks: list[Task] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)   # [IMPROVEMENT 4]
    reasoning: str = ""

    def total_duration(self) -> int:
        """Sum of minutes for all scheduled tasks."""
        return sum(t.duration for t in self.scheduled_tasks)

    def display(self) -> str:
        """Human-readable plan summary."""
        lines = [f"=== Daily Plan for {self.date} ==="]

        if self.conflicts:
            lines.append("\nConflicts detected:")
            for c in self.conflicts:
                lines.append(f"  ! {c}")

        if self.scheduled_tasks:
            lines.append(f"\nScheduled ({self.total_duration()} min total):")
            for t in self.scheduled_tasks:
                lines.append(f"  {t}")
        else:
            lines.append("\nNo tasks scheduled.")

        if self.skipped_tasks:
            lines.append("\nSkipped (not enough time):")
            for t in self.skipped_tasks:
                lines.append(f"  {t}")

        if self.reasoning:
            lines.append(f"\nReasoning: {self.reasoning}")

        return "\n".join(lines)

    def __str__(self) -> str:
        """Delegate to display() for the string representation."""
        return self.display()


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    """
    The scheduling brain.
    Retrieves tasks from the owner's pets, filters by recurrence,
    sorts by priority + duration, detects conflicts, and greedily
    fits as many tasks as possible within the owner's time budget.
    """

    PRIORITY_CATEGORIES = [
        TaskCategory.MEDS,
        TaskCategory.FEED,
        TaskCategory.WALK,
        TaskCategory.ENRICHMENT,
        TaskCategory.GROOMING,
    ]

    # How many days must pass before a task is due again
    FREQUENCY_DAYS: dict[str, int] = {
        "daily":     1,
        "weekly":    7,
        "as-needed": 0,   # always include unless completed today
    }

    def __init__(self, owner: Owner):
        """Store the owner whose pets and time budget drive scheduling."""
        self.owner = owner

    # -- helpers ------------------------------------------------------------

    def get_all_tasks(self) -> list[Task]:
        """Pull all pending tasks from every pet the owner has."""
        return self.owner.get_all_pending_tasks()

    # [IMPROVEMENT 2] filter by pet name and/or completion status
    def get_tasks_for_pet(self, pet_name: str, pending_only: bool = True) -> list[Task]:
        """
        Return tasks belonging to a single named pet.

        Args:
            pet_name:    Name of the pet to look up (must match Pet.name exactly).
            pending_only: If True (default) return only incomplete tasks;
                          if False return all tasks regardless of status.
        Raises:
            KeyError: if no pet with that name exists under this owner.
        """
        pet = self.owner.get_pet(pet_name)
        return pet.get_pending_tasks() if pending_only else pet.tasks

    # [IMPROVEMENT 3] recurrence check
    def is_due_today(self, task: Task, today: str | None = None) -> bool:
        """
        Return True if the task should appear in today's schedule.

        Rules:
          - Never done before (last_done is empty) -> always due.
          - frequency="as-needed"                  -> always due.
          - frequency="daily"                      -> due if today >= last_done + 1 day.
          - frequency="weekly"                     -> due if today >= last_done + 7 days.

        Args:
            task:  The Task to evaluate.
            today: ISO date string to use as "today" (defaults to the real date).
        """
        today_str = today or str(_date.today())

        if not task.last_done:
            return True  # never done before — always due

        interval = self.FREQUENCY_DAYS.get(task.frequency, 1)
        if interval == 0:
            return True  # "as-needed" — always eligible

        last = _date.fromisoformat(task.last_done)
        due_on = last + timedelta(days=interval)
        return _date.fromisoformat(today_str) >= due_on

    def fits_in_time(self, tasks: list[Task]) -> bool:
        """Return True if the combined duration fits within available time."""
        return sum(t.duration for t in tasks) <= self.owner.time_available

    # [IMPROVEMENT 4] conflict detection
    def detect_conflicts(self, tasks: list[Task]) -> list[str]:
        """Return warning strings for any pet+category combination appearing more than once."""
        # Build a map: (pet_name, category) -> [task names]
        seen: dict[tuple, list[str]] = {}
        for task in tasks:
            # Find which pet owns this task
            owner_pet = next(
                (p.name for p in self.owner.pets if any(t.task_id == task.task_id for t in p.tasks)),
                "Unknown"
            )
            key = (owner_pet, task.category)
            seen.setdefault(key, []).append(task.name)

        warnings = []
        for (pet_name, category), names in seen.items():
            if len(names) > 1:
                warnings.append(
                    f"{pet_name} has {len(names)} '{category.value}' tasks scheduled: "
                    + ", ".join(f'"{n}"' for n in names)
                )
        return warnings

    # [STEP 2] sort by scheduled_time ("HH:MM") ----------------------------

    def sort_by_time(self, tasks: list[Task] | None = None) -> list[Task]:
        """
        Sort tasks chronologically by their scheduled_time field (format: "HH:MM").

        Tasks with an empty scheduled_time are placed at the end of the list.
        Sorting is done via a lambda that substitutes "99:99" for missing times,
        which compares greater than any valid HH:MM string without raising errors.

        Args:
            tasks: List to sort; defaults to all pending tasks across all pets.
        """
        if tasks is None:
            tasks = self.get_all_tasks()
        # Use a lambda with a tuple key: tasks without a time get "99:99" so
        # they sort after all real times rather than raising an error.
        return sorted(tasks, key=lambda t: t.scheduled_time if t.scheduled_time else "99:99")

    # [STEP 2] filter by pet name and/or completion status -----------------

    def filter_tasks(
        self,
        pet_name: str | None = None,
        completed: bool | None = None,
    ) -> list[Task]:
        """
        Return tasks matching the given filters.

        pet_name  – if provided, limit to tasks belonging to that pet.
        completed – if True return only done tasks; if False only pending;
                    if None return all regardless of status.
        """
        if pet_name is not None:
            source_tasks = self.get_tasks_for_pet(pet_name, pending_only=False)
        else:
            source_tasks = self.owner.get_all_tasks()

        if completed is None:
            return source_tasks
        return [t for t in source_tasks if t.completed == completed]

    # [STEP 3] automate recurring task reset --------------------------------

    def reschedule_recurring(self) -> list[str]:
        """
        For every completed recurring task across all pets, replace it with
        its next occurrence (via Task.next_occurrence()).

        Returns a list of human-readable messages describing what was rescheduled.
        """
        messages: list[str] = []
        for pet in self.owner.pets:
            for task in list(pet.tasks):          # copy so we can mutate safely
                if task.completed and task.frequency in ("daily", "weekly"):
                    next_task = task.next_occurrence()
                    if next_task:
                        pet.remove_task(task.task_id)
                        pet.add_task(next_task)
                        messages.append(
                            f"{pet.name}: '{task.name}' rescheduled "
                            f"(next due: {next_task.last_done})"
                        )
        return messages

    # [STEP 4] time-slot conflict detection ---------------------------------

    def detect_time_conflicts(self, tasks: list[Task] | None = None) -> list[str]:
        """
        Return a warning string for every group of tasks sharing the same
        non-empty scheduled_time slot (across any pet).

        Strategy: group tasks by scheduled_time using a dict, then flag any
        slot with more than one task — lightweight, no crash on overlap.
        """
        if tasks is None:
            tasks = self.owner.get_all_tasks()

        # Build: time_slot -> [(pet_name, task_name), ...]
        slots: dict[str, list[str]] = {}
        for task in tasks:
            if not task.scheduled_time:
                continue
            pet_name = next(
                (p.name for p in self.owner.pets
                 if any(t.task_id == task.task_id for t in p.tasks)),
                "Unknown"
            )
            slots.setdefault(task.scheduled_time, []).append(
                f"{task.name} ({pet_name})"
            )

        return [
            f"Time conflict at {slot}: " + " vs ".join(names)
            for slot, names in slots.items()
            if len(names) > 1
        ]

    # [STEP 5] refined filter_by_priority using a cleaner lambda -----------
    # Before: nested def sort_key with an if/else block inside.
    # After : single lambda + .get() with a default — same behaviour, fewer lines.

    def filter_by_priority(self, tasks: list[Task] | None = None) -> list[Task]:
        """
        Sort tasks using a four-level key: priority -> category rank -> duration -> name.

        Priority 1 (high) sorts before 3 (low). Within the same priority,
        category rank follows MEDS > FEED > WALK > ENRICHMENT > GROOMING.
        Within the same category, shorter tasks sort first (bin-packing heuristic)
        so more tasks fit within the time budget. Name breaks remaining ties.

        Args:
            tasks: List to sort; defaults to all pending tasks across all pets.
        """
        if tasks is None:
            tasks = self.get_all_tasks()
        cat_rank = {c: i for i, c in enumerate(self.PRIORITY_CATEGORIES)}
        return sorted(
            tasks,
            key=lambda t: (t.priority, cat_rank.get(t.category, len(self.PRIORITY_CATEGORIES)), t.duration, t.name),
        )

    # -- core ---------------------------------------------------------------

    def generate_plan(self, target_date: str | None = None) -> DailyPlan:
        """
        Build a DailyPlan for the given date (defaults to today).

        Strategy:
          1. Collect all pending tasks; filter out those not yet due (recurrence).
          2. Sort by priority -> category -> duration (shortest-first) -> name.
          3. Detect category conflicts before scheduling.
          4. Greedily add tasks until the time budget is exhausted.
          5. Return a DailyPlan with scheduled tasks, skipped tasks,
             conflicts, and plain-English reasoning.
        """
        date_str = today = target_date or str(_date.today())

        # Step 1: recurrence filter
        all_pending = self.get_all_tasks()
        due_tasks = [t for t in all_pending if self.is_due_today(t, today)]
        not_due   = [t for t in all_pending if not self.is_due_today(t, today)]

        # Step 2: sort
        ordered = self.filter_by_priority(due_tasks)

        # Step 3: conflict detection (category duplicates + time-slot overlaps)
        conflicts = self.detect_conflicts(ordered) + self.detect_time_conflicts(ordered)

        # Step 4: greedy fill
        scheduled: list[Task] = []
        skipped: list[Task] = []
        time_used = 0

        for task in ordered:
            if time_used + task.duration <= self.owner.time_available:
                scheduled.append(task)
                time_used += task.duration
            else:
                skipped.append(task)

        # Step 5: build reasoning
        reasons: list[str] = []
        if scheduled:
            reasons.append(
                f"Scheduled {len(scheduled)} task(s) using {time_used} of "
                f"{self.owner.time_available} available minutes."
            )
        if skipped:
            reasons.append(f"Skipped {len(skipped)} task(s) - not enough time remaining.")
        if not_due:
            reasons.append(f"{len(not_due)} task(s) skipped - not due today based on frequency.")
        if not all_pending:
            reasons.append("No pending tasks found for any pet.")
        if conflicts:
            reasons.append(f"{len(conflicts)} scheduling conflict(s) detected.")

        return DailyPlan(
            date=date_str,
            scheduled_tasks=scheduled,
            skipped_tasks=skipped,
            conflicts=conflicts,
            reasoning=" ".join(reasons),
        )

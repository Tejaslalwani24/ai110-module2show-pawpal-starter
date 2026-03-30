from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field
from datetime import date as _date
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
    frequency: str = "daily"   # e.g. "daily", "weekly", "as-needed"
    completed: bool = False
    notes: str = ""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    # -- mutation helpers ---------------------------------------------------

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

    def mark_incomplete(self) -> None:
        """Reset completion status."""
        self.completed = False

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
            "notes":     self.notes,
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
    reasoning: str = ""

    def total_duration(self) -> int:
        """Sum of minutes for all scheduled tasks."""
        return sum(t.duration for t in self.scheduled_tasks)

    def display(self) -> str:
        """Human-readable plan summary."""
        lines = [f"=== Daily Plan for {self.date} ==="]
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
    Retrieves tasks from the owner's pets, orders them by priority and
    category preference, then greedily fits as many as possible within
    the owner's available time budget.
    """

    # High-priority categories always attempted first
    PRIORITY_CATEGORIES = [
        TaskCategory.MEDS,
        TaskCategory.FEED,
        TaskCategory.WALK,
        TaskCategory.ENRICHMENT,
        TaskCategory.GROOMING,
    ]

    def __init__(self, owner: Owner):
        """Store the owner whose pets and time budget drive scheduling."""
        self.owner = owner

    # -- helpers ------------------------------------------------------------

    def get_all_tasks(self) -> list[Task]:
        """Pull all pending tasks from every pet the owner has."""
        return self.owner.get_all_pending_tasks()

    def filter_by_priority(self, tasks: list[Task] | None = None) -> list[Task]:
        """
        Sort tasks: first by numeric priority (1 highest), then by
        preferred category order, then alphabetically by name.
        """
        if tasks is None:
            tasks = self.get_all_tasks()

        def sort_key(t: Task):
            cat_rank = (
                self.PRIORITY_CATEGORIES.index(t.category)
                if t.category in self.PRIORITY_CATEGORIES
                else len(self.PRIORITY_CATEGORIES)
            )
            return (t.priority, cat_rank, t.name)

        return sorted(tasks, key=sort_key)

    def fits_in_time(self, tasks: list[Task]) -> bool:
        """Return True if the combined duration fits within available time."""
        return sum(t.duration for t in tasks) <= self.owner.time_available

    # -- core ---------------------------------------------------------------

    def generate_plan(self, target_date: str | None = None) -> DailyPlan:
        """
        Build a DailyPlan for the given date (defaults to today).

        Strategy:
          1. Collect all pending tasks across all pets.
          2. Sort by priority + preferred category order.
          3. Greedily add tasks until the time budget is exhausted.
          4. Record skipped tasks and a plain-English reasoning string.
        """
        date_str = target_date or str(_date.today())
        ordered = self.filter_by_priority()

        scheduled: list[Task] = []
        skipped: list[Task] = []
        time_used = 0
        reasons: list[str] = []

        for task in ordered:
            if time_used + task.duration <= self.owner.time_available:
                scheduled.append(task)
                time_used += task.duration
            else:
                skipped.append(task)

        # Build reasoning string
        if scheduled:
            reasons.append(
                f"Scheduled {len(scheduled)} task(s) using {time_used} of "
                f"{self.owner.time_available} available minutes."
            )
        if skipped:
            reasons.append(
                f"Skipped {len(skipped)} task(s) - not enough time remaining."
            )
        if not ordered:
            reasons.append("No pending tasks found for any pet.")

        return DailyPlan(
            date=date_str,
            scheduled_tasks=scheduled,
            skipped_tasks=skipped,
            reasoning=" ".join(reasons),
        )

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional


class TaskCategory(Enum):
    WALK = "walk"
    FEED = "feed"
    MEDS = "meds"
    ENRICHMENT = "enrichment"
    GROOMING = "grooming"


@dataclass
class Task:
    task_id: str
    name: str
    category: TaskCategory
    duration: int        # minutes
    priority: int        # 1 = high, 2 = medium, 3 = low
    notes: str = ""

    def to_dict(self) -> dict:
        pass


@dataclass
class Pet:
    name: str
    species: str
    breed: str
    age: int

    def get_info(self) -> str:
        pass


@dataclass
class Owner:
    name: str
    time_available: int              # minutes per day
    preferences: list[str] = field(default_factory=list)
    _tasks: list[Task] = field(default_factory=list, repr=False)

    def add_task(self, task: Task) -> None:
        pass

    def remove_task(self, task_id: str) -> None:
        pass

    def get_tasks(self) -> list[Task]:
        pass


@dataclass
class DailyPlan:
    date: str
    scheduled_tasks: list[Task] = field(default_factory=list)
    skipped_tasks: list[Task] = field(default_factory=list)
    reasoning: str = ""

    def total_duration(self) -> int:
        pass

    def display(self) -> str:
        pass


class Scheduler:
    def __init__(self, owner: Owner, pet: Pet):
        self.owner = owner
        self.pet = pet
        self.tasks: list[Task] = []

    def filter_by_priority(self) -> list[Task]:
        pass

    def fits_in_time(self, tasks: list[Task]) -> bool:
        pass

    def generate_plan(self) -> DailyPlan:
        pass

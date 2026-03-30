import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pawpal_system import Task, Pet, TaskCategory


def make_task(**kwargs):
    defaults = dict(
        name="Test Task",
        category=TaskCategory.WALK,
        duration=20,
        priority=2,
    )
    defaults.update(kwargs)
    return Task(**defaults)


# --- Test 1: Task completion ---

def test_mark_complete_changes_status():
    task = make_task()
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_mark_incomplete_resets_status():
    task = make_task()
    task.mark_complete()
    task.mark_incomplete()
    assert task.completed is False


# --- Test 2: Task addition ---

def test_add_task_increases_count():
    pet = Pet(name="Buddy", species="Dog", breed="Labrador", age=3)
    assert len(pet.tasks) == 0
    pet.add_task(make_task(name="Morning Walk"))
    assert len(pet.tasks) == 1
    pet.add_task(make_task(name="Feeding"))
    assert len(pet.tasks) == 2

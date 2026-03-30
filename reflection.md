# PawPal+ Project Reflection

## 1. System Design

Three core actions a user should be able to perform:
1. Enter Owner + Pet Info — populate Owner (name, time available, preferences) and Pet (name, species, breed, age)
2. Add / Edit Tasks — create or modify Task objects (name, category, duration, priority) attached to the pet
3. Generate & View the Daily Plan — call Scheduler.generate_plan() to produce a DailyPlan and display the scheduled tasks + reasoning

**a. Initial design**

The initial UML design consists of five classes:

- **Owner** — holds user-facing info (name, time available per day in minutes, preferences). Responsible for managing the pet list (add, remove, retrieve) and providing cross-pet task access.
- **Pet** — stores pet profile data (name, species, breed, age) and owns its task list. Provides add/remove/get helpers and filters pending tasks.
- **Task** — represents a single care activity with a category (walk, feed, meds, enrichment, grooming), duration in minutes, integer priority (1 = high, 3 = low), frequency, and completion status. Serializable via `to_dict()`.
- **Scheduler** — the core engine. Takes an Owner as context and exposes `generate_plan()` which filters, sorts, and greedily fits tasks within the owner's time budget. Also provides `filter_by_priority()`, `fits_in_time()`, `sort_by_time()`, `filter_tasks()`, `detect_conflicts()`, and `detect_time_conflicts()`.
- **DailyPlan** — the output object produced by the Scheduler. Stores scheduled tasks, skipped tasks, conflict warnings, and a `reasoning` string. `display()` formats everything for the UI and `total_duration()` sums scheduled minutes.

**b. Design changes**

Yes, the design evolved in several ways during implementation:

1. **Owner became multi-pet.** The original UML had Owner managing a single Pet directly. During implementation it made more sense for Owner to hold a `pets: list[Pet]` so tasks could be aggregated across all pets — which is realistic for households with more than one animal.
2. **Task gained new fields.** `frequency`, `last_done`, and `scheduled_time` were all added after the initial skeleton. These were needed to support recurring task logic and time-slot conflict detection, neither of which was in the first draft.
3. **Scheduler gained more methods.** The initial design only had `generate_plan()`, `filter_by_priority()`, and `fits_in_time()`. During Phase 3 we added `sort_by_time()`, `filter_tasks()`, `reschedule_recurring()`, `detect_time_conflicts()`, and `is_due_today()` as the scheduling requirements became clearer.
4. **DailyPlan gained a `conflicts` field.** Originally it only stored scheduled and skipped tasks. Once conflict detection was added, a `conflicts: list[str]` field was needed so warnings could be surfaced in the UI without crashing.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers three constraints:

- **Time budget** — the owner's `time_available` (minutes/day) is the hard cap. No task is added to the plan if it would exceed this limit.
- **Priority** — tasks are sorted by their numeric priority (1 = high, 2 = medium, 3 = low) before the greedy fill begins, so critical tasks like meds and feeding are always attempted first.
- **Recurrence / frequency** — tasks with `frequency="daily"` are only scheduled if at least 1 day has passed since `last_done`; `frequency="weekly"` requires 7 days. This prevents the same task from showing up every run.

Category order also acts as a soft constraint: within the same priority tier, the scheduler always attempts MEDS → FEED → WALK → ENRICHMENT → GROOMING, reflecting real-world urgency for a pet owner.

Time was chosen as the primary hard constraint because it is the one resource that cannot be negotiated — unlike priority, which can be overridden. Category order was chosen based on what would cause harm if skipped: missing medication is more serious than skipping grooming.

**b. Tradeoffs**

The scheduler uses a **greedy algorithm**: it adds tasks one by one in sorted order and stops when the time budget is full. This is fast and simple but not optimal — it can miss a combination of smaller tasks that would collectively fit when a single large task is skipped.

For example: if 30 minutes remain and a 35-minute walk is next in priority, the walk is skipped even if two 15-minute tasks that follow it would both fit. A proper bin-packing solution would find those two tasks, but it is NP-hard and overkill for a daily pet care app where the task list is always short (under 20 items). The greedy approach is transparent, predictable, and easy for a pet owner to understand — which matters more here than mathematical optimality.

---

## 3. AI Collaboration

**a. How you used AI**

AI was used at every stage of the project:

- **Design brainstorming** — asked AI to draft the initial UML from the README scenario, identify the three core user actions, and suggest algorithm improvements (sorting, filtering, recurrence, conflict detection).
- **Implementation** — used AI to generate class skeletons, flesh out method bodies, and implement specific algorithms like `next_occurrence()` using `timedelta` and the greedy scheduling loop.
- **Refactoring** — asked AI to evaluate `filter_by_priority()` for readability; it suggested replacing the nested `sort_key` function with a pre-built dict lookup and a single lambda, which was cleaner.
- **Documentation** — used AI to generate 1-line and expanded docstrings for all methods.
- **Testing** — used AI to draft the initial pytest cases for task completion and task addition.

The most helpful prompt style was specific and constrained: *"Add a method to Scheduler that detects two tasks sharing the same HH:MM time slot and returns a warning string rather than raising an exception."* Vague prompts like *"improve the scheduler"* produced too many unrelated suggestions.

**b. Judgment and verification**

During the `reschedule_recurring()` implementation, AI initially suggested mutating `pet.tasks` in-place while iterating over it — a classic bug that causes tasks to be silently skipped. The fix was to iterate over `list(pet.tasks)` (a copy) instead. This was caught by reading the generated code carefully before running it, then verified by writing a manual trace: if a list shrinks while you iterate it, the index advances past the next element. Running `main.py` with a print statement before and after confirmed the copy-based version processed all tasks correctly.

**c. Copilot strategy reflection**

*Which Copilot features were most effective for building the scheduler?*

The most effective features were **inline chat on specific methods** and **context-aware code completion**. Inline chat worked best when scoped to a single function — for example, opening chat directly on `filter_by_priority()` and asking "simplify this sort key for readability" produced a tight, targeted refactor. Completions were valuable for repetitive boilerplate like `to_dict()` and the `__str__` methods, where the pattern was obvious and AI filled it correctly without guidance. The `#file:` context tag was also useful when asking for UML updates — pointing AI at the actual source file meant suggestions matched the real method signatures rather than invented ones.

*One example of rejecting or modifying an AI suggestion:*

When asking AI to implement `detect_time_conflicts()`, the first suggestion used a nested loop (`O(n²)`) that compared every task against every other task. This was functionally correct but unnecessary — a single-pass dict grouping tasks by `scheduled_time` achieves the same result in `O(n)` and is easier to read. The nested loop was rejected and replaced with `slots.setdefault(task.scheduled_time, []).append(...)`, which groups all tasks in one pass and flags any slot with more than one entry. The rule applied: if a simpler data structure solves the problem, prefer it over clever control flow.

*How did using separate chat sessions for different phases help?*

Keeping Phase 1 (UML design), Phase 2 (class implementation), Phase 3 (algorithms), and Phase 4 (UI) in separate sessions prevented context bleed — early design decisions and half-finished stubs from one phase never polluted suggestions in the next. Each session started with a clean mental model of only what that phase needed. It also made it easier to evaluate suggestions: if a Phase 3 chat recommended changing a class interface, that was a signal the design needed revisiting rather than a reason to blindly accept the change.

*What it means to be the "lead architect" when working with AI:*

AI is a fast, knowledgeable junior developer — it can produce code quickly but does not understand the system's goals, constraints, or long-term design unless told explicitly. Being the lead architect meant making every structural decision before asking AI to implement it: deciding that `Scheduler` owns conflict detection (not `Pet`), that `DailyPlan` is a pure output object with no side effects, that `Owner` holds a list of pets instead of a single one. AI filled in the bodies of those decisions correctly once the skeleton was clear. When AI suggested changes that would have blurred those boundaries — like putting scheduling logic directly in `Pet` — those suggestions were rejected not because the code was wrong, but because it violated the single-responsibility principle the architecture was built on. The key lesson: AI accelerates execution; the architect's job is to make sure there is a clear design to execute against.

---

## 4. Testing and Verification

**a. What you tested**

Two behaviors were tested in `tests/test_pawpal.py`:

1. **Task completion** — `test_mark_complete_changes_status` verifies that `task.completed` starts as `False` and becomes `True` after calling `mark_complete()`. A second test, `test_mark_incomplete_resets_status`, confirms the reverse. These matter because the entire recurrence and filtering system depends on the `completed` flag being accurate — if it never flips, no tasks are ever rescheduled or filtered out.

2. **Task addition** — `test_add_task_increases_count` verifies that `pet.tasks` grows from 0 to 1 to 2 as tasks are added. This is important because `Scheduler` pulls all tasks through the pet's list; if `add_task()` silently failed, the schedule would always be empty with no error.

**b. Confidence**

Confidence is moderate-to-high for the core happy path (add tasks, generate plan, display output). The greedy fill, priority sort, and time-slot conflict detection all produce correct output verified manually via `main.py`.

Edge cases that would be tested next with more time:
- **Zero time available** — `Owner(time_available=0)` should produce a plan with all tasks skipped.
- **All tasks already completed** — `generate_plan()` should return an empty scheduled list and a clear reasoning message.
- **Duplicate task_id** — `pet.add_task()` should raise `ValueError`; currently only tested implicitly.
- **Invalid `scheduled_time` format** — a value like `"8:5"` or `"25:00"` would sort incorrectly; input validation is not yet enforced.
- **`next_occurrence()` on an `as-needed` task** — should return `None`; not yet covered by a test.

---

## 5. Reflection

**a. What went well**

The layered architecture worked well. Because `Task`, `Pet`, `Owner`, `Scheduler`, and `DailyPlan` each had a single clear responsibility, adding new features (recurrence, time-slot conflicts, per-pet filtering) never required changing more than one or two classes. The `DailyPlan.display()` method also made it easy to connect the backend to both the terminal (`main.py`) and the Streamlit UI (`app.py`) without duplicating formatting logic.

**b. What you would improve**

The recurrence model is too simple. Currently `last_done` is a plain string and the "next due" date is calculated lazily at schedule time. A better design would store an explicit `next_due: str` field on each Task, updated whenever `mark_complete()` is called. This would make `is_due_today()` a single date comparison instead of a calculation, and would make the due date visible in the UI without running the scheduler first.

The Streamlit UI also only supports one pet per owner. The backend supports multiple pets, but the form in `app.py` always works with `owner.pets[0]`. A dropdown to select or add a second pet would make the UI match the backend's capability.

**c. Key takeaway**

The most important lesson was that **designing the data model first makes everything else easier**. Because the UML was drafted before any code was written, every subsequent feature — recurrence, conflict detection, per-pet filtering — had a natural home in an existing class. When AI suggested a new feature, the first question was always "which class owns this?" rather than "where do I put this?" That discipline prevented the codebase from becoming a pile of unrelated functions and made the Streamlit integration straightforward: the UI just calls methods that already exist.

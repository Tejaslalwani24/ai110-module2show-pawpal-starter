# PawPal+ Project Reflection

## 1. System Design
 three core actions a user should be able to perform : 
  1. Enter Owner + Pet Info — populate Owner (name, time available, preferences) and Pet (name,  1. Enter Owner + Pet Info — populate Owner (name, time available, preferences) and Pet (name, species,    breed, age) 
  2. Add / Edit Tasks — create or modify Task objects (name, category, duration, priority) attached to the   pet                                                                     
  3. Generate & View the Daily Plan — call Scheduler.generate_plan() to produce a DailyPlan and display the scheduled tasks + reasoning          
**a. Initial design**

The initial UML design consists of five classes:

- **Owner** — holds user-facing info (name, time available per day in minutes, preferences). Responsible for managing the task list (add, remove, retrieve).
- **Pet** — stores pet profile data (name, species, breed, age). Purely a data container with a `get_info()` helper.
- **Task** — represents a single care activity with a category (walk, feed, meds, enrichment, grooming), duration in minutes, and an integer priority (1 = high, 3 = low). Serializable via `to_dict()`.
- **Scheduler** — the core engine. Takes an Owner and Pet as context, holds the task list, and exposes `generate_plan()` which filters and orders tasks to fit within the owner's available time. Also provides `filter_by_priority()` and `fits_in_time()` as helper methods.
- **DailyPlan** — the output object produced by the Scheduler. Stores the chosen tasks, the skipped tasks, and a `reasoning` string explaining the selections. `display()` formats the plan for the UI and `total_duration()` sums scheduled minutes.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

```mermaid
classDiagram

class Owner {
    - String name
    - int time_available
    - List<string> preferences
    + add_task(task: Task) void
    + remove_task(task_id: string) void
    + get_tasks() List<Task>
}

class Pet {
    - String name
    - String species
    - String breed
    - int age
    + get_info() string
}

class Task {
    - String task_id
    - String name
    - String category
    - int duration
    - int priority
    - String notes
    + to_dict() dict
}

class Scheduler {
    - Owner owner
    - Pet pet
    - List<Task> tasks
    + generate_plan() DailyPlan
    + filter_by_priority() List<Task>
    + fits_in_time(tasks: List<Task>) bool
}

class DailyPlan {
    - String date
    - List<Task> scheduled_tasks
    - List<Task> skipped_tasks
    - String reasoning
    + display() string
    + total_duration() int
}

Owner "1" --> "1" Pet : owns
Pet "1" --> "1..*" Task : has
Scheduler "1" --> "1" Owner : uses
Scheduler "1" --> "1" Pet : uses
Scheduler "1" o-- "0..*" Task : schedules
Scheduler "1" --> "1" DailyPlan : produces
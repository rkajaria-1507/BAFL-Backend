# Exercise Level Mapping and Student Averages

This document describes the exercise level mapping and student average tracking features for physical assessments.

## Overview

The system tracks student performance across physical assessment sessions and automatically:
1. Calculates average scores for each exercise for each student in each batch
2. Maps these averages to fitness levels (L1-L7) based on predefined criteria
3. Updates levels automatically whenever new assessment sessions are created or updated

## Database Tables

### 1. `exercise_level_mappings`
Stores the criteria for determining fitness levels for each exercise.

**Columns:**
- `id`: Primary key
- `exercise_name`: Name of the exercise (e.g., curl_up, push_up, etc.)
- `level`: Fitness level (1-7)
- `min_score`: Minimum score for this level (inclusive)
- `max_score`: Maximum score for this level (inclusive)
- `level_score`: Points awarded for this level (2, 4, 6, 7, 8, 9, 10)
- `level_description`: Description of the level (e.g., "work harder", "must improve", etc.)
- `is_higher_better`: 1 if higher scores are better, 0 if lower is better
- `unit`: Unit of measurement (count, cm, min, sec)

**Exercises with Level Mappings:**
- `curl_up` (count) - Higher is better
- `push_up` (count) - Higher is better
- `sit_and_reach` (cm) - Higher is better
- `walk_600m` (minutes) - Lower is better
- `dash_50m` (seconds) - Lower is better
- `bow_hold` (seconds) - Higher is better
- `plank` (seconds) - Higher is better

### 2. `student_exercise_averages`
Stores the calculated average and current level for each student-batch-exercise combination.

**Columns:**
- `id`: Primary key
- `student_id`: Foreign key to students table
- `batch_id`: Foreign key to batches table
- `school_id`: Foreign key to schools table
- `exercise_name`: Name of the exercise
- `average_score`: Calculated average score across all sessions
- `current_level`: Current fitness level (1-7) based on average
- `level_score`: Points for the current level
- `level_description`: Description of the current level
- `session_count`: Number of sessions included in the average
- `last_updated_session_id`: ID of the last session that updated this record

**Unique Constraint:** One row per student-batch-exercise combination

## Level Criteria

### Regular Exercises (L1-L7)

| Level | Score | Description   |
|-------|-------|---------------|
| L1    | 2     | work harder   |
| L2    | 4     | must improve  |
| L3    | 6     | can do better |
| L4    | 7     | good          |
| L5    | 8     | very good     |
| L6    | 9     | athletic      |
| L7    | 10    | sport fit     |

### Detailed Level Ranges by Exercise

#### Curl Up (count)
- L1: 0-14
- L2: 15
- L3: 16-20
- L4: 21
- L5: 22-23
- L6: 24
- L7: 25+

#### Push Up (count)
- L1: 0-7
- L2: 8
- L3: 8
- L4: 9
- L5: 10
- L6: 11-12
- L7: 13+

#### Sit and Reach (cm)
- L1: 0-15.8
- L2: 15.81-19.7
- L3: 19.71-23.1
- L4: 23.11-24.9
- L5: 24.91-27.1
- L6: 27.11-32.5
- L7: 32.51+

#### 600m Walk (minutes) - Lower is better
- L1: 3.24+
- L2: 3.14-3.23
- L3: 3.07-3.13
- L4: 3.04-3.06
- L5: 3.01-3.03
- L6: 3.00
- L7: <3.00

#### 50m Dash (seconds) - Lower is better
- L1: 9.5+
- L2: 9.0-9.49
- L3: 8.6-8.99
- L4: 8.4-8.59
- L5: 8.2-8.39
- L6: 8.0-8.19
- L7: <8.00

#### Bow Hold (seconds)
- L1: 0-40
- L2: 41-50
- L3: 51-60
- L4: 61-70
- L5: 71-80
- L6: 81-90
- L7: 91+

#### Plank (seconds)
- L1: 0-40
- L2: 41-80
- L3: 81-120
- L4: 121-160
- L5: 161-200
- L6: 201-240
- L7: 241+

## Setup Instructions

### 1. Create Database Tables

Run migrations or create tables:
```bash
# This will create the new tables
python -m src.utils.db_init
```

### 2. Seed Level Mapping Data

Populate the `exercise_level_mappings` table:
```bash
python -m src.utils.seed_level_mappings
```

This will insert 49 rows (7 exercises × 7 levels) with the predefined criteria.

## How It Works

### Automatic Average Calculation

When a physical assessment session is created or updated:

1. **Session Creation** (`create_session_with_results`):
   - New session is created with student results
   - System automatically calculates averages for each student-exercise combination
   - Averages include ALL previous sessions for that batch where the student was present
   - Appropriate fitness levels are assigned based on the calculated averages

2. **Session Update** (`update_session`):
   - When results are modified, averages are recalculated
   - Levels are automatically updated based on new averages

3. **Individual Result Update** (`update_result`):
   - When a single student's result is updated, their exercise averages are recalculated
   - Levels are updated accordingly

### Average Calculation Logic

- **Inclusion Criteria**: Only sessions where the student was present (`is_present = True`) and the exercise value is non-zero
- **Rounding**: 
  - Count exercises (curl_up, push_up): Rounded to nearest integer
  - Distance/time exercises (sit_and_reach, walk_600m, dash_50m, bow_hold, plank): Kept as decimal values
- **Level Assignment**: Automatically determined by comparing the average score to the level mapping ranges

### Repository Methods

The `StudentExerciseAverageRepository` provides:

- `calculate_average_for_student_batch_exercise()` - Calculate average for a specific combination
- `get_level_for_score()` - Determine level based on score
- `update_or_create_average()` - Update or create an average record
- `update_averages_for_session()` - Update all averages for a session
- `get_student_averages_for_batch()` - Retrieve all exercises for a student in a batch
- `get_batch_averages()` - Retrieve all averages for a batch
- `get_school_averages()` - Retrieve all averages for a school

## Future Extensions

### Adding New Exercises

To add a new exercise:

1. Add the column to `physical_assessment_details` table
2. Add level mappings to `exercise_level_mappings` table
3. Update `EXERCISE_COLUMNS` in `StudentExerciseAverageRepository`
4. Add to schemas if needed

### Removing Exercises

To remove an exercise:

1. Set the exercise column to not collect data anymore
2. Existing level mappings can remain in the database for historical reference
3. Average records will remain for historical data

### Modifying Level Criteria

To modify level ranges:

1. Update the `exercise_level_mappings` table directly or via a migration
2. Run a script to recalculate all existing average levels
3. Future sessions will automatically use the new criteria

## API Integration

The average calculation is integrated into the existing physical assessment API endpoints:

- `POST /api/v1/physical-assessments/sessions/with-results` - Creates session and calculates averages
- `PUT /api/v1/physical-assessments/sessions/{session_id}` - Updates session and recalculates averages
- `PUT /api/v1/physical-assessments/results/{result_id}` - Updates individual result and recalculates averages

No additional API calls are needed - the system works automatically in the background.

## Querying Averages

To query student averages programmatically:

```python
from src.db.repositories.student_exercise_average_repository import StudentExerciseAverageRepository

# Get all averages for a student in a batch
avg_repo = StudentExerciseAverageRepository(db)
student_averages = avg_repo.get_student_averages_for_batch(
    student_id=123,
    batch_id=456
)

for avg in student_averages:
    print(f"Exercise: {avg.exercise_name}")
    print(f"Average: {avg.average_score}")
    print(f"Level: L{avg.current_level} - {avg.level_description}")
    print(f"Sessions: {avg.session_count}")
```

## Notes

- The system is designed to be extensible for future exercises
- All calculations happen automatically - no manual intervention needed
- Historical data is preserved even if exercises are removed or criteria change
- The unique constraint ensures one row per student-batch-exercise, preventing duplicates

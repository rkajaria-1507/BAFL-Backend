"""
Database migration script for Attendance feature.

This script creates the necessary tables for the Attendance feature:
- attendance_sessions: Stores attendance sessions per school per date
- attendance_records: Stores individual student attendance records per session
- coach_attendance: Stores coach attendance records

Run this script to add the attendance tables to your database.

For Supabase, you can either:
1. Run this Python script with your database connection
2. Copy the SQL statements and run them in the Supabase SQL editor
"""

# SQL statements for Supabase (PostgreSQL)
MIGRATION_SQL = """
-- Create attendance_sessions table
CREATE TABLE IF NOT EXISTS attendance_sessions (
    id SERIAL PRIMARY KEY,
    school_id INTEGER NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    taken_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT uix_school_date UNIQUE (school_id, date)
);

-- Create index on date for faster queries
CREATE INDEX IF NOT EXISTS idx_attendance_sessions_date ON attendance_sessions(date);

-- Create attendance_records table
CREATE TABLE IF NOT EXISTS attendance_records (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES attendance_sessions(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    status VARCHAR(10) NOT NULL CHECK (status IN ('Present', 'Absent')),
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT uix_session_student UNIQUE (session_id, student_id)
);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_attendance_records_session ON attendance_records(session_id);
CREATE INDEX IF NOT EXISTS idx_attendance_records_student ON attendance_records(student_id);

-- Create coach_attendance table
CREATE TABLE IF NOT EXISTS coach_attendance (
    id SERIAL PRIMARY KEY,
    coach_id INTEGER REFERENCES coaches(id) ON DELETE SET NULL,
    coach_name VARCHAR(150) NOT NULL,
    school_id INTEGER NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    school_name VARCHAR(150) NOT NULL,
    date DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_coach_attendance_coach ON coach_attendance(coach_id);
CREATE INDEX IF NOT EXISTS idx_coach_attendance_school ON coach_attendance(school_id);
CREATE INDEX IF NOT EXISTS idx_coach_attendance_date ON coach_attendance(date);

-- Enable Row Level Security (RLS) for Supabase (optional but recommended)
-- ALTER TABLE attendance_sessions ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE attendance_records ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE coach_attendance ENABLE ROW LEVEL SECURITY;
"""


def run_migration():
    """Run the migration using SQLAlchemy."""
    from src.db.database import engine, Base
    # Import the attendance models to register them with SQLAlchemy
    from src.db.models.attendance import AttendanceSession, AttendanceRecord, CoachAttendance
    
    print("Creating attendance tables...")
    
    # Create only the attendance tables (not all tables)
    Base.metadata.create_all(bind=engine, tables=[
        AttendanceSession.__table__,
        AttendanceRecord.__table__,
        CoachAttendance.__table__,
    ])
    
    print("Attendance tables created successfully!")


if __name__ == "__main__":
    import sys
    
    if "--sql" in sys.argv:
        # Just print the SQL for manual execution
        print("SQL Migration for Attendance Feature")
        print("=" * 50)
        print(MIGRATION_SQL)
    else:
        # Run the migration
        run_migration()

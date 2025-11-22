import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

# Database path
DB_PATH = Path(__file__).parent / "tutorials.db"

def init_db():
    """Initialize the database with required tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tutorials table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tutorials (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            date_created TEXT NOT NULL,
            date_modified TEXT NOT NULL
        )
    """)
    
    # Create steps table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS steps (
            id TEXT PRIMARY KEY,
            tutorial_id TEXT NOT NULL,
            step_order INTEGER NOT NULL,
            element_name TEXT,
            description TEXT,
            screenshot_base64 TEXT,
            element_type TEXT,
            is_manual INTEGER DEFAULT 0,
            bounding_box TEXT,
            FOREIGN KEY (tutorial_id) REFERENCES tutorials(id) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    conn.close()

def create_tutorial(title: str, steps: List[Dict]) -> str:
    """Create a new tutorial with steps."""
    import uuid
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    tutorial_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    # Insert tutorial
    cursor.execute(
        "INSERT INTO tutorials (id, title, date_created, date_modified) VALUES (?, ?, ?, ?)",
        (tutorial_id, title, now, now)
    )
    
    # Insert steps
    for idx, step in enumerate(steps):
        cursor.execute("""
            INSERT INTO steps (id, tutorial_id, step_order, element_name, description, 
                             screenshot_base64, element_type, is_manual, bounding_box)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            step.get('id', str(uuid.uuid4())),
            tutorial_id,
            idx,
            step.get('element_name', ''),
            step.get('description', ''),
            step.get('screenshot_base64', ''),
            step.get('element_type', ''),
            1 if step.get('is_manual', False) else 0,
            json.dumps(step.get('bounding_box'))
        ))
    
    conn.commit()
    conn.close()
    
    return tutorial_id

def get_recent_tutorials(limit: int = 10) -> List[Dict]:
    """Get recent tutorials (without steps)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, title, date_created, date_modified 
        FROM tutorials 
        ORDER BY date_modified DESC 
        LIMIT ?
    """, (limit,))
    
    tutorials = []
    for row in cursor.fetchall():
        tutorials.append({
            'id': row[0],
            'title': row[1],
            'date_created': row[2],
            'date_modified': row[3]
        })
    
    conn.close()
    return tutorials

def get_tutorial(tutorial_id: str) -> Optional[Dict]:
    """Get a specific tutorial with all its steps."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get tutorial info
    cursor.execute(
        "SELECT id, title, date_created, date_modified FROM tutorials WHERE id = ?",
        (tutorial_id,)
    )
    
    tutorial_row = cursor.fetchone()
    if not tutorial_row:
        conn.close()
        return None
    
    # Get steps
    cursor.execute("""
        SELECT id, element_name, description, screenshot_base64, element_type, 
               is_manual, bounding_box
        FROM steps 
        WHERE tutorial_id = ? 
        ORDER BY step_order
    """, (tutorial_id,))
    
    steps = []
    for row in cursor.fetchall():
        steps.append({
            'id': row[0],
            'element_name': row[1],
            'description': row[2],
            'screenshot_base64': row[3],
            'element_type': row[4],
            'is_manual': bool(row[5]),
            'bounding_box': json.loads(row[6]) if row[6] else None
        })
    
    conn.close()
    
    return {
        'id': tutorial_row[0],
        'title': tutorial_row[1],
        'date_created': tutorial_row[2],
        'date_modified': tutorial_row[3],
        'steps': steps
    }

def update_tutorial(tutorial_id: str, title: str, steps: List[Dict]) -> bool:
    """Update an existing tutorial."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    # Update tutorial
    cursor.execute(
        "UPDATE tutorials SET title = ?, date_modified = ? WHERE id = ?",
        (title, now, tutorial_id)
    )
    
    # Delete old steps
    cursor.execute("DELETE FROM steps WHERE tutorial_id = ?", (tutorial_id,))
    
    # Insert new steps
    for idx, step in enumerate(steps):
        cursor.execute("""
            INSERT INTO steps (id, tutorial_id, step_order, element_name, description, 
                             screenshot_base64, element_type, is_manual, bounding_box)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            step.get('id'),
            tutorial_id,
            idx,
            step.get('element_name', ''),
            step.get('description', ''),
            step.get('screenshot_base64', ''),
            step.get('element_type', ''),
            1 if step.get('is_manual', False) else 0,
            json.dumps(step.get('bounding_box'))
        ))
    
    conn.commit()
    conn.close()
    
    return True

def delete_tutorial(tutorial_id: str) -> bool:
    """Delete a tutorial and all its steps."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM tutorials WHERE id = ?", (tutorial_id,))
    
    conn.commit()
    conn.close()
    
    return True

# Initialize database on module import
init_db()

from fastapi import FastAPI
import sqlite3
import pandas as pd
from pathlib import Path
import os

app = FastAPI()

def get_db_connection():
    # Since we moved the DB to the same folder as this script, 
    # it's guaranteed to be included in the serverless function.
    db_path = Path(__file__).resolve().parent / "races.db"
    
    if not db_path.exists():
        # Fallback for Vercel's flat deployment structure
        db_path = Path.cwd() / "api" / "races.db"
        if not db_path.exists():
             db_path = Path.cwd() / "races.db"

    if not db_path.exists():
        raise FileNotFoundError(f"Database not found at {db_path}. Current dir: {os.listdir('.')}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/api/debug")
def debug():
    import os
    base_dir = Path(__file__).resolve().parent.parent
    
    # List files in some key directories to see where we are
    try:
        var_task_files = os.listdir("/var/task")
    except:
        var_task_files = ["Could not access /var/task"]
        
    try:
        cwd_files = os.listdir(".")
    except:
        cwd_files = ["Could not access ."]

    return {
        "file": __file__,
        "cwd": os.getcwd(),
        "var_task_files": var_task_files,
        "cwd_files": cwd_files,
        "env": dict(os.environ),
        "db_searched_paths": [
            str(Path(__file__).resolve().parent.parent / "database" / "races.db"),
            str(Path.cwd() / "database" / "races.db"),
            "/var/task/database/races.db"
        ]
    }

@app.get("/api/ping")
def ping():
    return {"status": "ok"}

@app.get("/api/events")
def get_events():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT DISTINCT event_slug, distance FROM runners", conn)
    conn.close()
    return df.to_dict(orient="records")

@app.get("/api/stats")
def get_stats(event_slug: str, distance: str):
    conn = get_db_connection()

    query = """
    SELECT finish_time_seconds, age, gender, pace_seconds
    FROM runners
    WHERE event_slug = ? AND distance = ? AND finish_time_seconds IS NOT NULL
    """
    df = pd.read_sql_query(query, conn, params=(event_slug, distance))
    conn.close()

    if df.empty:
        return {"error": "No data found"}

    # Gender split — computed from the full df (gender is always present)
    gender_counts = df['gender'].value_counts().to_dict()

    # Finish-time records — only requires finish_time_seconds (always present here)
    finish_records = df[['finish_time_seconds']].dropna().to_dict(orient="records")

    # Age records — only rows where age is not null
    age_records = df[['age']].dropna().to_dict(orient="records")

    # Pace-vs-age scatter — only rows where both age AND pace_seconds are not null
    scatter_records = df[['age', 'pace_seconds']].dropna().to_dict(orient="records")

    return {
        "gender_counts": gender_counts,
        "finish_records": finish_records,
        "age_records": age_records,
        "scatter_records": scatter_records,
    }

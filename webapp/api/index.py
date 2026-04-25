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

@app.get("/api/overview")
def get_overview():
    conn = get_db_connection()
    query = """
    SELECT distance, gender, finish_time_seconds, event_slug 
    FROM runners 
    WHERE finish_time_seconds IS NOT NULL AND gender IS NOT NULL
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        return {}

    # Normalize gender
    df['gender'] = df['gender'].str[0].str.upper()
    df = df[df['gender'].isin(['M', 'F'])]

    # Normalize distance groups
    def normalize_dist(d):
        d = str(d).upper()
        if '21' in d: return '21K'
        if '10' in d: return '10K'
        if '5' in d: return '5K'
        if '3' in d: return '3K'
        return None

    df['dist_group'] = df['distance'].apply(normalize_dist)
    df = df.dropna(subset=['dist_group'])

    results = {}
    for dist in ['3K', '5K', '10K', '21K']:
        dist_df = df[df['dist_group'] == dist].copy()
        if dist_df.empty:
            continue
        
        # Bin by minute for high-resolution pyramids
        dist_df['mins'] = (dist_df['finish_time_seconds'] / 60).astype(int)
        
        # Pyramid Data (Aggregated)
        total_male_counts = dist_df[dist_df['gender'] == 'M']['mins'].value_counts().sort_index().to_dict()
        total_female_counts = dist_df[dist_df['gender'] == 'F']['mins'].value_counts().sort_index().to_dict()
        all_mins = sorted(list(set(total_male_counts.keys()) | set(total_female_counts.keys())))
        
        # Individual Race Data (for overlay line plots)
        races_data = []
        for slug, group in dist_df.groupby('event_slug'):
            r_male_group = group[group['gender'] == 'M']
            r_female_group = group[group['gender'] == 'F']
            
            r_male_counts = r_male_group['mins'].value_counts().sort_index().to_dict()
            r_female_counts = r_female_group['mins'].value_counts().sort_index().to_dict()
            
            races_data.append({
                "event_slug": slug,
                "male_counts": {str(m): count for m, count in r_male_counts.items()},
                "female_counts": {str(m): count for m, count in r_female_counts.items()}
            })

        # Statistics
        m_mins = dist_df[dist_df['gender'] == 'M']['mins']
        f_mins = dist_df[dist_df['gender'] == 'F']['mins']

        def get_stat(series, func):
            if series.empty: return None
            val = func(series)
            return int(val) if pd.notna(val) else None

        results[dist] = {
            "labels": [f"{m}m" for m in all_mins],
            "male": [total_male_counts.get(m, 0) for m in all_mins],
            "female": [total_female_counts.get(m, 0) for m in all_mins],
            "total_participants": len(dist_df),
            "races": races_data,
            "stats": {
                "fastest_male": get_stat(m_mins, min),
                "fastest_female": get_stat(f_mins, min),
                "median_male": get_stat(m_mins, lambda x: x.median()),
                "median_female": get_stat(f_mins, lambda x: x.median()),
            }
        }
        
    return results

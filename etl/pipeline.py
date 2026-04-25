import os
import json
import sqlite3
import re
from pathlib import Path

# Connect to SQLite inside the webapp for easy deployment bounding
DB_PATH = Path("webapp/api/races.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

# Create table
cursor.execute('''
CREATE TABLE IF NOT EXISTS runners (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site TEXT,
    event_slug TEXT,
    distance TEXT,
    distance_km REAL,
    athlete TEXT,
    gender TEXT,
    age INTEGER,
    category TEXT,
    finish_time_str TEXT,
    finish_time_seconds INTEGER,
    pace_seconds INTEGER
)
''')
# Clear all previous to be idempotent
cursor.execute('DELETE FROM runners')
conn.commit()

def extract_km(distance_str):
    match = re.search(r'([0-9\.]+)\+?K', distance_str, re.IGNORECASE)
    if not match:
        match = re.search(r'([0-9\.]+)\+?Kilometros', distance_str, re.IGNORECASE)
    if match:
        return float(match.group(1))
    return None

def time_to_seconds(time_str):
    if not time_str:
        return None
    parts = str(time_str).split(":")
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + int(float(s))
    elif len(parts) == 2:
        m, s = parts
        return int(m) * 60 + int(float(s))
    return None

data_dir = Path("data")

print("Starting ETL Process...")
count = 0

for site_dir in data_dir.iterdir():
    if not site_dir.is_dir():
        continue
    site = site_dir.name
    
    for event_dir in site_dir.iterdir():
        if not event_dir.is_dir():
            continue
        event_slug = event_dir.name
        
        for distance_dir in event_dir.iterdir():
            if not distance_dir.is_dir():
                continue
            distance_raw = distance_dir.name
            distance_km = extract_km(distance_raw)
            
            pages_dir = distance_dir / "pages"
            if not pages_dir.exists():
                continue
                
            for page_file in pages_dir.glob("*.json"):
                with open(page_file, "r", encoding="utf-8") as f:
                    try:
                        records = json.load(f)
                    except json.JSONDecodeError:
                        continue
                        
                    for rec in records:
                        # Shared fields
                        athlete = None
                        gender = None
                        age = None
                        category = None
                        finish_time_str = None
                        
                        if site == "asdeporte":
                            athlete = rec.get("runnername")
                            gender = rec.get("branchename", "")
                            if gender:
                                gender = gender[0].upper()
                            age = rec.get("age")
                            category = rec.get("categoryname")
                            finish_time_str = rec.get("totaltime")
                            
                        elif site == "cronocom":
                            athlete = rec.get("Athlete")
                            gender = rec.get("Gender")
                            category = rec.get("Category")
                            finish_time_str = rec.get("FinishTime")
                            # Age is usually not provided clearly, but sometimes it is mapped. Default None.
                            age = None 
                        
                        elif site == "metamx":
                            data_dict = {item['key']: item['value'] for item in rec['data']}
                            athlete = data_dict.get("name")
                            gender = data_dict.get("gender", "")
                            if gender:
                                gender = gender[0].upper()
                            age = data_dict.get("age")
                            category = data_dict.get("category")
                            finish_time_str = data_dict.get("time")
                            
                        elif site == "marcate":
                            athlete = rec.get("nombre")
                            gender = rec.get("sexo", "")
                            if gender:
                                gender = gender[0].upper()
                            age = rec.get("edad")
                            category = rec.get("categoria")
                            finish_time_str = rec.get("tiempoChip")
                            
                        if not finish_time_str or finish_time_str == "00:00:00":
                            continue # Didn't finish
                            
                        finish_time_seconds = time_to_seconds(finish_time_str)
                        if not finish_time_seconds:
                            continue
                            
                        # Compute Pace
                        pace_seconds = None
                        if distance_km and distance_km > 0:
                            pace_seconds = int(finish_time_seconds / distance_km)
                            
                        cursor.execute('''
                            INSERT INTO runners (
                                site, event_slug, distance, distance_km, athlete, gender, age, category, finish_time_str, finish_time_seconds, pace_seconds
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (site, event_slug, distance_raw, distance_km, athlete, gender, age, category, finish_time_str, finish_time_seconds, pace_seconds))
                        
                        count += 1

conn.commit()
print(f"ETL Complete! Processed {count} finisher records into SQLite.")

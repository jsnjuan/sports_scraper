import os
import json
import sqlite3
import re
from pathlib import Path

# Connect to SQLite inside the webapp for easy deployment bounding
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "webapp" / "api" / "races.db"
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
    pace_seconds INTEGER, 
    pace_minutes INTEGER
)
''')
# Clear all previous to be idempotent
cursor.execute('DELETE FROM runners')
conn.commit()

def extract_km(distance_str):
    # match = re.search(r'([0-9\.]+)\+?K', distance_str, re.IGNORECASE)
    
    cleaned = distance_str.lower().strip()
    
    # The cdp race (carrera del dia del padre) has a special/preference 
    # group that is identified as zone. Lets parse this specific case 
    if cleaned == 'zone':
        return 21.0
    
    # Also the XL MEDIO MARATÓN INTERNACIONAL GUADALAJARA ELECTROLIT ® 2026 
    # has the catefory named different as the kilometers convention 3K, 5K, etc.
    # We are handling this specific case
    if cleaned == 'medio maraton':
        return 21.0
    
    match = re.search(r'(\d+(?:[.,]\d+)?)\s*k', 
    cleaned,
    re.IGNORECASE)
    
    if not match:
        match = re.search(r'([0-9\.]+)\+?Kilometros', 
        cleaned, 
        re.IGNORECASE)
        
    if match:
        return float(match.group(1).replace(',', '.'))
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

def parse_age(age_val):
    if age_val is None or str(age_val).strip() == "":
        return None
    try:
        return int(float(age_val))
    except:
        return None

def parse_gender(gender_raw, category_raw=None):
    if gender_raw: # Cases where we have gender value
        if gender_raw.strip().upper() in ('VARONIL', 'M', 'MASCULINO', 'MALE'):
            return 'M'
        elif gender_raw.strip().upper() in ('FEMENIL', 'F', 'FEMENINO', 'FEMALE'):
            return 'F'
        else:
            return gender_raw.strip().upper()
    else: # Cases where we do not have gender value (mostly from metamx)
        if 'VARONIL' in category_raw:
            return 'M'
        elif 'FEMENIL' in category_raw:
            return 'F'
    return None

data_dir = PROJECT_ROOT / "data"

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
                            category = rec.get("categoryname")
                            gender_raw = rec.get("branchename")
                            gender = parse_gender(gender_raw, category)
                            age = parse_age(rec.get("age"))
                            finish_time_str = rec.get("totaltime")
                            
                        elif site == "cronocom":
                            athlete = rec.get("Athlete")
                            if not athlete:
                                athlete = rec.get("Name")
                            category = rec.get("Category")
                            if not category:
                                category = rec.get("Class")
                            gender_raw = rec.get("Gender")
                            gender = parse_gender(gender_raw, category)
                            finish_time_str = rec.get("FinishTime")
                            # Age is usually not provided clearly, but sometimes it is mapped. Default None.
                            age = None 
                        
                        elif site == "metamx":
                            data_dict = {item['key']: item['value'] for item in rec['data']}
                            athlete = data_dict.get("name")
                            if not athlete:
                                athlete = data_dict.get("fullName")
                            category = data_dict.get("category")
                            gender_raw = data_dict.get("gender")
                            gender = parse_gender(gender_raw, category)
                            age = parse_age(data_dict.get("age"))
                            finish_time_str = data_dict.get("time")
                            
                        elif site == "marcate":
                            athlete = rec.get("nombre")
                            category = rec.get("categoria")
                            gender_raw = rec.get("sexo")
                            gender = parse_gender(gender_raw, category)
                            age = parse_age(rec.get("edad"))
                            finish_time_str = rec.get("tiempoChip")
                            
                        if not finish_time_str or finish_time_str == "00:00:00":
                            continue # Didn't finish
                            
                        finish_time_seconds = time_to_seconds(finish_time_str)
                        if not finish_time_seconds:
                            continue
                            
                        # Compute Pace
                        pace_seconds = None
                        pace_minutes = None
                        if distance_km and distance_km > 0:
                            pace_seconds = finish_time_seconds // distance_km
                            pace_minutes = (finish_time_seconds // 60) / distance_km
                            
                        cursor.execute('''
                            INSERT INTO runners (
                                site, event_slug, distance, distance_km, athlete, gender, age, category, finish_time_str, finish_time_seconds, pace_seconds, pace_minutes
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (site, event_slug, distance_raw, distance_km, athlete, gender, age, category, finish_time_str, finish_time_seconds, pace_seconds, pace_minutes))
                        
                        count += 1

conn.commit()
print(f"ETL Complete! Processed {count} finisher records into SQLite.")

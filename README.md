# 🏎️ Sports Analytics Pipeline & Dashboard

[![Vercel Deployment](https://img.shields.io/badge/Deployment-Vercel-black?style=flat-square&logo=vercel)](https://vercel.com)
[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/Next.js-15-black?style=flat-square&logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)

An end-to-end Data Engineering and Analytics project that scrapes race results from multiple sports platforms, normalizes the data through a robust ETL pipeline, and visualizes athlete performance metrics via a modern web dashboard.

## 🚀 Overview

This project transforms fragmented, semi-structured sports data into actionable insights.

### Key Features
- **Scalable Scraper Engine**: Modular driver-based architecture (`AsDeporte`, `CronoCom`, `MetaMX`) capable of handling diverse web structures and anti-bot measures.
- **Robust ETL Pipeline**: Automated data extraction, cleaning (normalization of times, age groups, and categories), and loading into a relational database.
- **Advanced Analytics**: Visual analysis of finish time distributions, age demographics, and pace-to-age correlations.
- **Serverless Deployment**: Full-stack integration with a FastAPI backend and Next.js frontend, optimized for Vercel.

---

## 🏗️ Architecture

```mermaid
graph TD
    A[Sports Sites: AsDeporte, Cronocom, Metamx] -->|Scraping| B(Python Scraper Engine)
    B -->|JSON/Raw Data| C[Data Lake / Temporary Storage]
    C -->|ETL Processing| D{Normalization Logic}
    D -->|Structured Data| E[(SQLite / Relational DB)]
    E -->|FastAPI| F[Python Backend API]
    F -->|REST / JSON| G[Next.js Dashboard]
    G -->|Visualization| H[Chart.js / Interactive Insights]
```

### 🛠️ Tech Stack
- **Engine**: Python (Asyncio), Playwright (for dynamic content).
- **Backend**: FastAPI, SQLAlchemy/SQLite, Pandas.
- **Frontend**: Next.js 15, Tailwind CSS, Chart.js.
- **Deployment**: Vercel (Frontend + Serverless Python Functions).

---

## 📊 Data Engineering & Analytics Depth

### 1. Data Normalization (The "T" in ETL)
Sports data often arrives in inconsistent formats (e.g., `1h 20m`, `01:20:00`, or total seconds). Our pipeline includes:
- **Time Parsing**: Unified conversion of diverse string formats into `finish_time_seconds`.
- **Deduplication**: Ensuring athlete records are unique across multi-day events.
- **Feature Engineering**: Calculating `pace_seconds` (min/km) from distance and time to enable cross-race comparison.

### 2. Analytical Insights
The dashboard provides three core analytical views:
- **Performance Distribution**: A histogram showing the density of runners at different time intervals, identifying "peaks" where most runners finish.
- **Demographic Split**: Breakdown of participation by Age and Gender.
- **Correlation Analysis**: A scatter plot mapping Pace vs. Age to visualize how athletic performance degrades or sustains across different age groups.

---

## 💻 Installation & Usage

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm/yarn

### 1. Scraper & ETL
```bash
# Install dependencies
pip install -r requirements.txt

# Run the scraper
python main.py

# Run the ETL pipeline to process data into the webapp database
python etl/pipeline.py
```

### 2. Web Dashboard
```bash
cd webapp
npm install
npm run dev
```

---

## 🌐 Deployment

The project is configured for **Vercel**. 
- **Root Directory**: `webapp`
- **Framework**: Next.js
- **API**: The Python backend is automatically served via Vercel's `@vercel/python` runtime (defined in `webapp/vercel.json`).

---

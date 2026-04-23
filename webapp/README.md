# Sports Analytics Web Dashboard

This is the frontend and API layer of the **Sports Analytics Pipeline**.

## Tech Stack
- **Frontend**: Next.js (App Router)
- **API**: FastAPI (Python)
- **Charts**: Chart.js
- **Styling**: Tailwind CSS

## Deployment
This folder is the **Root Directory** for the Vercel deployment. It contains the `vercel.json` configuration required to run both the Next.js frontend and the Python FastAPI backend as serverless functions.

## Local Development
1. Install Node dependencies: `npm install`
2. Install Python dependencies: `pip install -r requirements.txt`
3. Run the development server: `npm run dev`

For the full project documentation (including the Scraper and ETL logic), please see the [main README in the project root](../README.md).

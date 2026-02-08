# Odds API Data Pipeline - Complete Setup Guide

## Overview

This document provides complete setup instructions for running the Odds API data pipeline with Apache Airflow, Databricks, and dbt.

**Pipeline Architecture:**
```
The Odds API → Python Extraction → CSV → Databricks Bronze
                                            ↓
                                    dbt Transformation
                                            ↓
                              Silver (Staging/Intermediate)
                                            ↓
                              Gold (Analytics-Ready Marts)
                                            ↓
                                    Email Alerts
```

**Schedule:** Every 3 hours (0:00, 3:00, 6:00, ...) UTC to capture all matches 6+ hours before kickoff.

---

## Prerequisites

- Python 3.14.2 (or compatible version)
- Virtual environment with packages installed: `pip install -r requirements.txt`
- Docker Desktop (for running Airflow locally)
- Databricks workspace account with:
  - Workspace URL
  - Compute warehouse or cluster
  - Personal Access Token (PAT)
- The Odds API key (obtain from https://the-odds-api.com/)
- GitHub repository (for version control)

---

## Step 1: Configure Databricks Credentials

### Get Your Databricks Connection Details

1. **Log into your Databricks workspace**
2. **Get workspace hostname:**
   - Copy your workspace URL from the browser: `https://dbc-xxxxx.cloud.databricks.com`
   - Extract the hostname part: `dbc-xxxxx.cloud.databricks.com`

3. **Create or Get SQL Warehouse:**
   - Go to Compute → SQL Warehouses
   - Click on a warehouse (or create new)
   - Copy the HTTP Path: `/sql/1.0/warehouses/abc123def456`

4. **Generate Personal Access Token:**
   - User Settings (top right) → Developer → Access tokens
   - Generate new token
   - Copy the token (long string starting with `dapi...`)

### Update .env File

Edit your `.env` file with correct values:

```env
# Databricks Configuration
DATABRICKS_HOST=dbc-xxxxx.cloud.databricks.com
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/abc123def456
DATABRICKS_TOKEN=dapixxx...xxx
```

**Important:**
- `DATABRICKS_HOST` should NOT include `https://` prefix
- `DATABRICKS_HTTP_PATH` must be the SQL warehouse or compute endpoint path
- Never commit `.env` to Git (it's in `.gitignore`)

---

## Step 2: Verify Environment Setup

### Check All Python Packages

```powershell
# List installed packages
pip show pandas requests databricks-sql-connector apache-airflow python-dotenv
```

### Test Databricks Connection

```python
# Test script: test_databricks_connection.py
from scripts.databricks_upload import DatabricksLoader
import os
from dotenv import load_dotenv

load_dotenv()

loader = DatabricksLoader(
    server_hostname=os.getenv('DATABRICKS_HOST'),
    http_path=os.getenv('DATABRICKS_HTTP_PATH'),
    access_token=os.getenv('DATABRICKS_TOKEN')
)

if loader.connect():
    loader.create_bronze_table()
    stats = loader.get_table_stats()
    print(f"Connection successful! Stats: {stats}")
    loader.close()
```

Run:
```powershell
python test_databricks_connection.py
```

---

## Step 3: Run Airflow Locally (Development)

### Initialize Airflow

```powershell
cd docker
docker-compose up airflow-init
```

This creates the Airflow database and default admin user (airflow/airflow).

### Start Airflow Services

```powershell
docker-compose up -d
```

This starts:
- PostgreSQL database (port 5432)
- Airflow WebServer (port 8080)
- Airflow Scheduler (runs DAGs on schedule)

### Access Airflow UI

1. Open browser: http://localhost:8080
2. Login: `airflow` / `airflow`
3. Find DAG: `odds_api_pipeline`
4. Click to view details and manual trigger

### Check Logs

```powershell
# View scheduler logs
docker-compose logs airflow-scheduler -f

# View webserver logs
docker-compose logs airflow-webserver -f

# View specific task logs
docker-compose logs airflow-scheduler | grep odds_api_pipeline
```

### Stop Airflow

```powershell
docker-compose down
```

---

## Step 4: Manual DAG Execution (Testing)

### Trigger DAG From Command Line

```powershell
# Inside Docker container
docker-compose exec airflow-scheduler \
  airflow dags trigger odds_api_pipeline
```

### Monitor Execution

```powershell
# Check DAG status
docker-compose exec airflow-scheduler \
  airflow dags list-runs -d odds_api_pipeline

# Check task status
docker-compose exec airflow-scheduler \
  airflow tasks list odds_api_pipeline
```

---

## Step 5: Extract Data (Without Airflow)

### Run Extraction Manually

If you want to extract data without Airflow:

```powershell
python scripts/api_extraction/odds_extractor.py
```

This will:
- Extract odds for all configured soccer leagues
- Save to `data/raw/odds_extracted_YYYYMMDD_HHMMSS.csv`
- Print summary to console

### Output Example

```
[OK] Extractor initialized successfully

======================================================================
EXTRACTING ODDS FOR 4 SOCCER LEAGUES
======================================================================

[LEAGUE] Extracting: English Premier League (EPL)
         Sport Key: soccer_epl
   [OK] 21 matches found
        Markets requested: h2h, spreads, totals
        Requests remaining: 485
   [OK] Transformed 63 records

...

[OK] Saved 87 records to data/raw/odds_extracted_20260208_170810.csv
```

---

## Step 6: Load Data to Databricks (Without Airflow)

### Upload CSV to Bronze Layer

```powershell
python scripts/databricks_upload.py
```

This will:
- Read the latest CSV from `data/raw/`
- Create bronze table (if not exists)
- Insert data to Databricks
- Print statistics

### Output Example

```
[INFO] Inserting 87 rows into bronze.odds_raw...
[INFO]   Inserted 87/87 rows

======================================================================
DATABRICKS LOAD SUMMARY
======================================================================
Rows Loaded: 87
Total Rows in Bronze: 87
Sports Covered: 2
Total Matches: 31
Market Types: 3
Latest Data Date: 2026-02-08
======================================================================
```

---

## Step 7: Transform Data with dbt

### Install dbt and Dependencies

```powershell
pip install dbt-core dbt-databricks dbt-expectations
```

### Test dbt Connection

```powershell
cd dbt/odds_transform

# List available models
dbt ls

# Test connection
dbt debug
```

### Run dbt Models

```powershell
# Run all models
dbt run

# Run specific model
dbt run --select stg_odds_raw

# Run models by tag
dbt run --select tag:marts
```

### Run dbt Tests

```powershell
# Run all tests
dbt test

# Run only data quality tests
dbt test --select tag:staging
```

### Generate Documentation

```powershell
# Generate dbt documentation
dbt docs generate

# Serve documentation (opens in browser)
dbt docs serve
```

---

## Step 8: Query Results in Databricks

### Connect in Databricks SQL Editor

1. Open Databricks workspace
2. SQL → Create new SQL notebook
3. Query the data layers:

```sql
-- Bronze Layer (Raw Data)
SELECT * FROM bronze.odds_raw LIMIT 100;

-- Silver Layer - Staging
SELECT * FROM silver.stg_odds_raw LIMIT 100;

-- Silver Layer - Intermediate (With Calculations)
SELECT 
    game_id,
    home_team,
    away_team,
    home_win_odds,
    home_win_implied_prob,
    bookmaker_margin_h2h
FROM silver.int_odds_with_margins
LIMIT 100;

-- Gold Layer - Daily Summary
SELECT * FROM gold.fct_daily_odds_summary ORDER BY match_date DESC;

-- Gold Layer - Match Details
SELECT * FROM gold.fct_match_odds
WHERE match_date >= CURRENT_DATE()
ORDER BY commence_time;
```

---

## Step 9: Email Alerts

### Alert Configuration

The Airflow DAG sends emails to: **nomatyel@gmail.com**

**Success Email Includes:**
- Execution date and time
- Rows extracted and loaded
- Total records in bronze table
- Sports covered and match count
- Links to Databricks views

**Failure Email Includes:**
- Error summary
- Run ID and execution date
- Link to Airflow logs

### Configure SMTP (Optional)

To enable email in Airflow, update `docker-compose.yml`:

```yaml
environment:
  AIRFLOW__SMTP__SMTP_HOST: smtp.gmail.com
  AIRFLOW__SMTP__SMTP_PORT: 587
  AIRFLOW__SMTP__SMTP_USER: your-email@gmail.com
  AIRFLOW__SMTP__SMTP_PASSWORD: your-app-password
  AIRFLOW__SMTP__SMTP_MAIL_FROM: airflow@odds-api.com
```

---

## Step 10: Production Deployment

### Docker Image for Production

Build custom image with dbt:

```dockerfile
# Dockerfile.airflow
FROM apache/airflow:2.7.0

RUN pip install dbt-core dbt-databricks dbt-expectations \
                databricks-sql-connector
```

Build and push to registry:

```powershell
docker build -f Dockerfile.airflow -t your-registry/airflow-odds:latest .
docker push your-registry/airflow-odds:latest
```

### Deploy to Cloud

For AWS, Azure, or GCP:

1. **AWS MWAA:**
   - Create managed airflow environment
   - Upload DAGs and plugins
   - Configure S3 for logs

2. **Azure Container Instances:**
   - Deploy Docker image
   - Set environment variables
   - Configure networking

3. **GCP Cloud Composer:**
   - Create Composer environment
   - Upload Python dependencies
   - Configure Cloud Storage

---

## Troubleshooting

### Issue: "ODDS_API_KEY not found"

**Solution:** Set environment variable:
```powershell
$env:ODDS_API_KEY="your-key-here"
```

If still failing, check `.env` file location and use absolute path in code.

### Issue: "Failed to connect to Databricks"

**Checklist:**
```
✓ DATABRICKS_HOST without https:// prefix
✓ DATABRICKS_HTTP_PATH includes /sql/1.0/warehouses/...
✓ DATABRICKS_TOKEN is valid (not expired)
✓ Warehouse is running (not suspended)
✓ Network access allows outbound HTTPS to Databricks
```

### Issue: Airflow DAG not running on schedule

**Check:**
```powershell
# Verify scheduler is running
docker-compose ps

# Check DAG parsing errors
docker-compose logs airflow-scheduler | grep odds_api_pipeline

# Trigger manually to test
docker-compose exec airflow-scheduler \
  airflow dags trigger odds_api_pipeline
```

### Issue: dbt model fails

**Check:**
```powershell
cd dbt/odds_transform

# Validate SQL syntax
dbt parse

# Run with verbose output
dbt run --debug

# Check for missing sources
dbt run --select stg_odds_raw --debug
```

---

## Architecture Details

### Data Flow

```
┌─────────────────────┐
│  The Odds API       │
│  (Betway Odds)      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Python Extractor   │
│  (Every 3 hours)    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  CSV File           │
│  (data/raw/)        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Databricks Bronze  │
│  (Raw Delta Table)  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────┐
│  dbt Transformation Layer       │
│  ┌───────────────────────────┐  │
│  │ Silver: Staging/Transform │  │
│  │ - stg_odds_raw            │  │
│  │ - int_odds_with_margins   │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │ Gold: Analytics Marts     │  │
│  │ - fct_daily_odds_summary  │  │
│  │ - fct_match_odds          │  │
│  └───────────────────────────┘  │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────┐
│  Email Alerts       │
│  (nomatyel@gmail.com)
└─────────────────────┘
```

### Data Quality

dbt tests include:
- **Uniqueness:** game_id unique in staging
- **Not Null:** All critical fields required
- **Range:** Odds between 1.0-10000, margins 0-50%
- **Accepted Values:** Bookmaker = 'betway', markets in predefined list
- **Row Count:** At least some data loaded

---

## Monitoring & Observability

### Airflow UI Checks

1. **DAG Overview:** http://localhost:8080/dags/odds_api_pipeline
   - Last run status
   - Next scheduled run
   - Historical runs

2. **Task Details:**
   - Click on task to see logs
   - View XCom (task communication)
   - Retry failed tasks

3. **Metrics:**
   - Success rate
   - Execution duration
   - Resource usage

### Databricks Monitoring

1. **Query History:** Compute → Query History
2. **Table Sizes:** Data Explorer → Database sizes
3. **Gold Tables:** Check data freshness

```sql
-- Check latest data
SELECT MAX(ingestion_date) as latest_date, 
       COUNT(*) as record_count
FROM bronze.odds_raw
GROUP BY DATE(ingestion_date);
```

### Email Monitoring

Check email alerts:
- **Success:** Data loaded successfully (daily summary)
- **Failure:** Check logs in Airflow UI
- **Metrics:** Rows loaded, sports covered, match count

---

## Next Steps

1. **Enable Scheduling:** Start Airflow scheduler to run DAG every 3 hours
2. **Add Dashboards:** Create Databricks SQL dashboards on gold tables
3. **Expand Sports:** Add more sports beyond soccer in SOCCER_LEAGUES
4. **Implement CI/CD:** GitHub Actions for dbt test runs
5. **Scale Up:** Deploy to production environment (AWS/Azure/GCP)
6. **Advanced Analytics:** Build ML models on historical odds data

---

## Support & Documentation

- **The Odds API:** https://the-odds-api.com/
- **Databricks Docs:** https://docs.databricks.com/
- **Airflow Docs:** https://airflow.apache.org/docs/
- **dbt Docs:** https://docs.getdbt.com/
- **Project GitHub:** https://github.com/lu-nomatye-profile/Odds-api-project

---

**Last Updated:** February 8, 2026
**Maintainer:** Data Engineering Team
**Environment:** Python 3.14.2, Apache Airflow 2.7.0, dbt-databricks

# Odds API Pipeline - Quick Reference

## Project Structure

```
odds-api-project/
├── airflow/
│   ├── dags/
│   │   └── odds_api_pipeline.py ............... Main orchestration (3-hour schedule)
│   ├── logs/
│   └── plugins/
├── dbt/
│   └── odds_transform/
│       ├── profiles.yml ....................... Databricks connection config
│       ├── schema.yml ......................... Data lineage & tests
│       └── models/
│           ├── staging/
│           │   └── stg_odds_raw.sql ......... Clean raw data
│           ├── intermediate/
│           │   └── int_odds_with_margins.sql  Calculate odds metrics
│           └── marts/
│               ├── fct_daily_odds_summary.sql  Daily aggregates
│               └── fct_match_odds.sql ........ Match-level details
├── docker/
│   └── docker-compose.yml ..................... Airflow & PostgreSQL setup
├── scripts/
│   ├── api_extraction/
│   │   └── odds_extractor.py ................. Extract from The Odds API
│   └── databricks_upload.py .................. Load CSV to Databricks
├── sql/
├── notebooks/
├── SETUP_GUIDE.md ............................ Complete setup instructions
└── README.md ................................ Project overview
```

---

## Key Components

### 1. Data Extraction
**File:** `scripts/api_extraction/odds_extractor.py`

**Features:**
- Multi-league extraction (EPL, La Liga, Serie A, Champions League)
- Exhaustive market types (h2h, spreads, totals)
- Betway bookmaker filter
- Automatic CSV export to `data/raw/`

**Run Manually:**
```powershell
python scripts/api_extraction/odds_extractor.py
```

---

### 2. Databricks Integration
**File:** `scripts/databricks_upload.py`

**Features:**
- SQL/Connector connection to Databricks
- Create/verify bronze layer table
- CSV to Delta Lake loading
- Table statistics and monitoring

**Run Manually:**
```powershell
python scripts/databricks_upload.py
```

---

### 3. Airflow Orchestration
**File:** `airflow/dags/odds_api_pipeline.py`

**DAG Details:**
- **Name:** `odds_api_pipeline`
- **Schedule:** Every 3 hours (0, 3, 6, 9, 12, 15, 18, 21:00 UTC)
- **Tasks:**
  1. `extract_odds` → Extract from API
  2. `load_to_databricks` → Load CSV to bronze
  3. `validate_data` → Quality checks
  4. `prepare_summary` → Prepare email content
  5. `run_dbt_models` → Transform data
  6. `run_dbt_tests` → Quality tests
  7. `send_success_email` → Alert success (nomatyel@gmail.com)
  8. `send_failure_email` → Alert failure

**Run Airflow:**
```powershell
cd docker
docker-compose up -d
# Access at http://localhost:8080
```

---

### 4. dbt Transformation Models

#### Staging (Silver Layer)
**Model:** `stg_odds_raw.sql`
- Clean and standardize raw data
- Remove invalid odds (≤0)
- Type casting and validation

#### Intermediate (Silver Layer)
**Model:** `int_odds_with_margins.sql`
- Pivot odds by outcome (home, away, draw)
- Calculate implied probabilities: `1/odds`
- Calculate bookmaker margin (overround)
- Incremental materialization (daily updates)

#### Marts (Gold Layer)
**Models:**
- `fct_daily_odds_summary.sql` → Daily aggregations by sport
- `fct_match_odds.sql` → Match-level analytics-ready data

**Run dbt:**
```powershell
cd dbt/odds_transform
dbt run                    # Run all models
dbt test                   # Run all tests
dbt docs serve            # View documentation
```

---

## Configuration

### .env File (Not Committed)
```env
ODDS_API_KEY=your_api_key_here
DATABRICKS_HOST=dbc-xxxxx.cloud.databricks.com
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/abc123
DATABRICKS_TOKEN=dapixxxxx
AIRFLOW_UID=50000
AIRFLOW__CORE__FERNET_KEY=your_fernet_key
```

### Environment Variables
Must be set before running Airflow DAG:
- `ODDS_API_KEY` → API key for The Odds API
- `DATABRICKS_HOST` → Databricks workspace hostname
- `DATABRICKS_HTTP_PATH` → SQL warehouse HTTP path
- `DATABRICKS_TOKEN` → Databricks personal access token

---

## Execution Timeline

**Every 3 Hours:**
```
00:00 UTC ──┐
            ├─► Extract odds
            ├─► Load to Databricks
            ├─► Transform with dbt
            ├─► Run tests
            └─► Send email
03:00 UTC ──┼─► (repeat)
06:00 UTC ──┼─► (repeat)
...
21:00 UTC ──┘─► (repeat)
```

**For Match at 14:00 UTC:**
- Extracted at: 06:00 UTC (8 hours before)
- Available in Databricks: Within 5 minutes
- Transformed by: 06:10-06:15 UTC
- Email sent by: 06:15 UTC

---

## Data Layers in Databricks

### Bronze (Raw)
```
Database: odds_api_db
Schema: bronze
Table: odds_raw
- Raw data from The Odds API
- Delta Lake partitioned by ingestion_date
- 100+ columns (flattened nested JSON)
```

### Silver (Processed)
```
Database: odds_api_db
Schema: silver
Tables:
  - stg_odds_raw (view) → Cleaned staging data
  - int_odds_with_margins (table) → Calculated metrics
```

### Gold (Analytics)
```
Database: odds_api_db
Schema: gold
Tables:
  - fct_daily_odds_summary → Daily aggregations
  - fct_match_odds → Match-level details
```

---

## Sample Queries

### Latest Data in Bronze
```sql
SELECT MAX(ingestion_date) as latest_date,
       COUNT(*) as records,
       COUNT(DISTINCT game_id) as matches
FROM bronze.odds_raw;
```

### Today's EPL Matches
```sql
SELECT home_team, away_team, commence_time,
       home_win_odds, away_win_odds, draw_odds,
       home_win_implied_prob, bookmaker_margin_h2h
FROM gold.fct_match_odds
WHERE sport_key = 'soccer_epl'
  AND match_date = CURRENT_DATE()
ORDER BY commence_time;
```

### Daily Margin Trends
```sql
SELECT match_date, sport_title,
       AVG(avg_bookmaker_margin) as margin,
       MIN(min_bookmaker_margin) as min_margin,
       MAX(max_bookmaker_margin) as max_margin
FROM gold.fct_daily_odds_summary
WHERE match_date >= CURRENT_DATE() - 30
GROUP BY match_date, sport_title
ORDER BY match_date DESC;
```

---

## Maintenance Tasks

### Daily
- Check email alerts
- Monitor Airflow DAG runs
- Verify Databricks table row counts

### Weekly
- Review dbt test results
- Check data quality metrics
- Monitor API request usage

### Monthly
- Archive old data (data/raw/ CSVs)
- Review transformation logic
- Update documentation

---

## Troubleshooting Checklist

| Issue | Check |
|-------|-------|
| Data not loading | ✓ API key valid<br>✓ CSV created in data/raw<br>✓ Databricks credentials correct |
| Airflow DAG not running | ✓ Scheduler container running<br>✓ DAG enabled<br>✓ No scheduling conflicts |
| dbt models failing | ✓ Bronze table has data<br>✓ Databricks connection<br>✓ SQL syntax errors |
| Email not sending | ✓ SMTP configured<br>✓ Email address valid<br>✓ Airflow logs show no errors |

---

## Useful Commands

### Airflow
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs airflow-scheduler -f

# Execute task
docker-compose exec airflow-scheduler \
  airflow tasks run odds_api_pipeline extract_odds 2026-02-08
```

### dbt
```bash
# Parse project
dbt parse

# Run models
dbt run --select tag:marts

# Test models
dbt test --select stg_odds_raw

# Generate docs
dbt docs generate

# Serve docs
dbt docs serve
```

### Git
```bash
# Stage changes
git add .

# Commit
git commit -m "Your message"

# Push
git push origin main

# View history
git log --oneline -10
```

---

## Contact & Support

- **Pipeline Issues:** Check GitHub issues
- **Databricks Questions:** See https://docs.databricks.com/
- **Airflow Docs:** https://airflow.apache.org/
- **dbt Docs:** https://docs.getdbt.com/
- **Email Alerts:** nomatyel@gmail.com

---

**Version:** 1.0  
**Last Updated:** February 2026  
**Status:** Production Ready

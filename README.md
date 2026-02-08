# Odds API Data Engineering Project

A complete data engineering pipeline for extracting Betway sports betting odds using The Odds API, with orchestration via Apache Airflow, storage in Databricks, and transformation using dbt.

## Project Overview

This project implements a **Medallion Architecture** (Bronze â†’ Silver â†’ Gold) to build an enterprise-grade data pipeline for sports betting odds data.

### Architecture Diagram

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚  The Odds API   â”‚ (Data Source)
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚
    â”Œâ”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”
    â”‚  Python     â”‚ (Data Extraction)
    â”‚  Extractor  â”‚
    â””â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚
    â”Œâ”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
    â”‚  Apache Airflow   â”‚ (Orchestration)
    â”‚  (Docker)         â”‚
    â””â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚
    â”Œâ”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
    â”‚  Databricks       â”‚ (Data Storage)
    â”‚  - Bronze Layer   â”‚
    â””â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚
    â”Œâ”€â”€â”€â”€â–¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
    â”‚  dbt              â”‚ (Transformation)
    â”‚  - Silver Layer   â”‚
    â”‚  - Gold Layer     â”‚
    â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

## Tech Stack

- [ ] Configure error handling and monitoring
 
- **Orchestration**: Apache Airflow 2.7.0
- **Containerization**: Docker & Docker Compose
- **Data Warehouse**: Databricks (Delta Lake)
- **Transformation**: dbt (data build tool)
- **Languages**: Python, SQL, YAML
- **Version Control**: Git

## Project Structure

```
odds-api-project/
â”œâ”€â”€ airflow/
â”‚   â”œâ”€â”€ dags/                    # Airflow DAG definitions
â”‚   â”œâ”€â”€ plugins/                 # Custom Airflow operators
â”‚   â””â”€â”€ logs/                    # Airflow logs
â”œâ”€â”€ dbt/
â”‚   â””â”€â”€ odds_transform/          # dbt project for transformations
â”œâ”€â”€ docker/
â”‚   â””â”€â”€ docker-compose.yml       # Docker Compose configuration
â”œâ”€â”€ scripts/
â”‚   â””â”€â”€ api_extraction/          # Data extraction scripts
â”‚       â””â”€â”€ odds_extractor.py    # Main API extractor class
â”œâ”€â”€ sql/                         # SQL queries and schemas
â”œâ”€â”€ notebooks/                   # Jupyter notebooks for exploration
â”œâ”€â”€ .env.example                 # Environment variables template
â”œâ”€â”€ requirements.txt             # Python dependencies
â”œâ”€â”€ .gitignore                   # Git ignore rules
â””â”€â”€ README.md                    # This file
```

## Prerequisites

- Python 3.9+
- Docker Desktop
- Docker Compose
- Git
- Databricks Account with workspace
- The Odds API Account (free tier available)

## Setup Instructions

### 1. Clone and Navigate to Project

```bash
cd odds-api-project
```

### 2. Create Python Virtual Environment

```bash
# Windows
python -m venv venv
.\venv\Scripts\Activate.ps1

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Copy the template and add your credentials:

```bash
cp .env.example .env
```

Edit `.env` and add:
- Your Odds API key from https://the-odds-api.com/
- Your Databricks workspace credentials
- Other configuration values

**Important**: Never commit `.env` to Git!

### 5. Register for The Odds API

1. Go to https://the-odds-api.com/
2. Sign up for a free account
3. Generate an API key
4. Note your monthly request limit (free tier: 500 requests/month)

### 6. Test API Connection

```bash
python scripts/test_api_connection.py
```

Expected output:
```
âœ… API Connection Successful!
Status Code: 200
Requests Remaining: 485
```

### 7. Start Docker Services

From the `docker/` directory:

```bash
cd docker
docker-compose up -d
```

This will start:
- **PostgreSQL**: Database for Airflow metadata
- **Airflow Webserver**: http://localhost:8080 (username: airflow, password: airflow)
- **Airflow Scheduler**: Runs DAGs on schedule

### 8. Access Airflow UI

Open http://localhost:8080 in your browser

Default credentials:
- Username: `airflow`
- Password: `airflow`

## Phase-by-Phase Implementation

### Phase 1: Project Setup & Architecture Design âœ…
- [x] Created directory structure
- [x] Initialized Git repository
- [x] Created .gitignore file
- [x] Created requirements.txt
- [x] Created environment template

### Phase 2: Docker Environment Setup (IN PROGRESS)
- [ ] Start Docker services
- [ ] Initialize Airflow database
- [ ] Verify Airflow UI access

### Phase 3: Data Extraction Layer
- [ ] Test API extractor with different sports
- [ ] Extract Betway odds for multiple sports
- [ ] Validate data quality

### Phase 4: Databricks Integration
- [ ] Create Databricks connection
- [ ] Create bronze layer tables
- [ ] Upload initial data

### Phase 5: Apache Airflow DAG Development
- [ ] Create main orchestration DAG
- [ ] Set up extraction tasks
- [ ] Configure error handling and monitoring

### Phase 6: dbt Transformation Layer
- [ ] Initialize dbt project (if not done)
- [ ] Create staging models
- [ ] Create intermediate models with calculations
- [ ] Create gold layer marts

### Phase 7: Data Quality & Testing
- [ ] Add dbt tests
- [ ] Implement data validation
- [ ] Add monitoring

### Phase 8: Orchestration & Scheduling
- [ ] Configure DAG schedule (every 6 hours)
- [ ] Set up alerting
- [ ] Test end-to-end pipeline

## Key Scripts

### API Extractor

```python
from scripts.api_extraction.odds_extractor import OddsAPIExtractor
import os

# Initialize
api_key = os.getenv('ODDS_API_KEY')
extractor = OddsAPIExtractor(api_key)

# Get available sports
sports = extractor.get_available_sports()

# Extract odds for a specific sport
raw_data = extractor.extract_odds('soccer_epl')

# Transform to DataFrame
df = extractor.transform_to_dataframe(raw_data)

# Save to CSV
filepath = extractor.save_to_csv(df, 'betway_odds')
```

## API Endpoints Used

### Get Available Sports
```
GET https://api.the-odds-api.com/v4/sports/?apiKey={YOUR_KEY}
```

### Get Odds for Sport
```
GET https://api.the-odds-api.com/v4/sports/{sport_key}/odds/
    ?apiKey={YOUR_KEY}
    &regions=uk,us
    &markets=h2h
    &bookmakers=betway
    &oddsFormat=decimal
```

## Common Sports Keys
- `soccer_epl` - English Premier League
- `soccer_uefa_champs_league` - UEFA Champions League
- `basketball_nba` - NBA
- `baseball_mlb` - MLB
- `american_football_nfl` - NFL

## Monitoring & Debugging

### Check Airflow Logs
```bash
docker logs docker_airflow-scheduler_1
```

### View Extracted Data
```bash
ls -la data/raw/
```

### Test API Manually
```bash
python scripts/test_api_connection.py
```

## Troubleshooting

### "ODDS_API_KEY not found"
- Ensure `.env` file exists in the project root
- Check that your API key is correctly set
- Run: `python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('ODDS_API_KEY'))"`

### Docker Port Already in Use
```bash
# Stop all containers
docker-compose down
# Or use different port in docker-compose.yml
```

### API Rate Limit Exceeded
- You've used all requests for the month
- Upgrade your The Odds API plan or wait for the next month

### No Betway Odds Available
- Some sports/events may not have Betway odds
- Check the `test_all_sports.py` script to find sports with Betway data

## Success Metrics

- âœ… Airflow DAG runs successfully every 6 hours
- âœ… Betway odds data lands in Databricks bronze layer
- âœ… dbt models transform data through silver to gold
- âœ… All dbt tests pass
- âœ… Data quality checks validate odds ranges
- âœ… Historical data accumulates for trend analysis

## Next Steps

1. **Immediate**: Get Docker running and Airflow accessible
2. **Short-term**: Create first Airflow DAG and test extraction
3. **Medium-term**: Set up Databricks connection and load data
4. **Long-term**: Implement dbt transformations and build analytics layer

## Resources

- [The Odds API Documentation](https://the-odds-api.com/api-usage)
- [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- [dbt Documentation](https://docs.getdbt.com/)
- [Databricks SQL Documentation](https://docs.databricks.com/sql/)
- [Medallion Architecture](https://www.databricks.com/glossary/medallion-architecture)

## License

This project is for educational purposes.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review API documentation at https://the-odds-api.com/
3. Check Airflow logs: `docker-compose logs -f airflow-scheduler`

---

**Last Updated**: February 2026
**Status**: Initial Setup Phase
>>>>>>> 2987264 (Initial commit: Odds API pipeline setup with data extraction layer)


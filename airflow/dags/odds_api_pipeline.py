"""
Main Odds API Orchestration DAG
Orchestrates: Extraction → Databricks → dbt Transformation → Alerts

Scheduling Strategy:
- Runs every 3 hours (0:00, 3:00, 6:00, 9:00, 12:00, 15:00, 18:00, 21:00)
- This ensures capture of all matches 6+ hours before kickoff
- For match at 14:00 UTC, extraction happens at 06:00 UTC (8 hours before)
- For match at 20:00 UTC, extraction happens at 15:00 or 18:00 UTC (5-2 hours before)
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.email import EmailOperator
from airflow.utils.dates import days_ago
from airflow.exceptions import AirflowException
import sys
import os
import logging
import glob

# Add project paths to Python path
sys.path.insert(0, '/opt/airflow')
sys.path.insert(0, '/opt/airflow/dags/../..')

# Import custom modules
from scripts.api_extraction.odds_extractor import OddsAPIExtractor
from scripts.databricks_upload import DatabricksLoader

logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configuration
ODDS_API_KEY = os.getenv('ODDS_API_KEY')
DATABRICKS_HOST = os.getenv('DATABRICKS_HOST')
DATABRICKS_HTTP_PATH = os.getenv('DATABRICKS_HTTP_PATH')
DATABRICKS_TOKEN = os.getenv('DATABRICKS_TOKEN')
ALERT_EMAIL = 'nomatyel@gmail.com'

# Extract hostname from URL if needed
if DATABRICKS_HOST and DATABRICKS_HOST.startswith('https://'):
    DATABRICKS_HOST = DATABRICKS_HOST.replace('https://', '').split('/')[0]

# Soccer leagues to extract
SOCCER_LEAGUES = [
    'soccer_epl',
    'soccer_la_liga',
    'soccer_serie_a',
    'soccer_uefa_champs_league'
]

# DAG configuration
default_args = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email': [ALERT_EMAIL],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# Define DAG
with DAG(
    'odds_api_pipeline',
    default_args=default_args,
    description='Extract Betway odds every 3 hours, load to Databricks, transform with dbt',
    schedule_interval='0 */3 * * *',  # Every 3 hours (0:00, 3:00, 6:00, etc. UTC)
    catchup=False,
    tags=['odds', 'betway', 'soccer', 'pipeline'],
    max_active_runs=1,  # Only one run at a time
) as dag:

    # ==================== PYTHON TASKS ====================

    def extract_odds_task(**context):
        """
        Extract odds data from The Odds API for multiple soccer leagues
        Saves combined CSV to data/raw/
        """
        logger.info("[START] Extract Odds Task")
        
        try:
            if not ODDS_API_KEY:
                raise ValueError("ODDS_API_KEY not configured in environment")
            
            # Initialize extractor
            extractor = OddsAPIExtractor(ODDS_API_KEY)
            
            logger.info(f"[INFO] Extracting odds for {len(SOCCER_LEAGUES)} leagues")
            
            # Extract for all configured leagues
            combined_df = extractor.extract_odds_for_leagues(
                leagues=SOCCER_LEAGUES,
                regions=['uk', 'us'],
                bookmakers=['betway']
            )
            
            if combined_df.empty:
                logger.warning("[WARNING] No data extracted from API")
                context['ti'].xcom_push(key='csv_filepath', value=None)
                context['ti'].xcom_push(key='row_count', value=0)
                return {'status': 'no_data', 'rows': 0}
            
            # Save to CSV
            filepath = extractor.save_to_csv(combined_df, 'odds_extracted')
            row_count = len(combined_df)
            
            logger.info(f"[OK] Extraction complete: {filepath} ({row_count} rows)")
            
            # Push to XCom for downstream tasks
            context['ti'].xcom_push(key='csv_filepath', value=filepath)
            context['ti'].xcom_push(key='row_count', value=row_count)
            
            return {
                'status': 'success',
                'filepath': filepath,
                'rows': row_count,
                'leagues': len(SOCCER_LEAGUES)
            }
        
        except Exception as e:
            logger.error(f"[ERROR] Extract task failed: {e}")
            raise AirflowException(f"Extract odds failed: {str(e)}")

    def load_to_databricks_task(**context):
        """
        Load extracted CSV data to Databricks bronze layer
        """
        logger.info("[START] Load to Databricks Task")
        
        try:
            csv_filepath = context['ti'].xcom_pull(key='csv_filepath', task_ids='extract_odds')
            row_count = context['ti'].xcom_pull(key='row_count', task_ids='extract_odds')
            
            if not csv_filepath:
                logger.warning("[WARNING] No CSV file to load (no data extracted)")
                context['ti'].xcom_push(key='rows_loaded', value=0)
                return {'status': 'no_data', 'rows_loaded': 0}
            
            if not all([DATABRICKS_HOST, DATABRICKS_HTTP_PATH, DATABRICKS_TOKEN]):
                raise ValueError("Databricks credentials not configured in environment")
            
            # Initialize loader
            loader = DatabricksLoader(
                server_hostname=DATABRICKS_HOST,
                http_path=DATABRICKS_HTTP_PATH,
                access_token=DATABRICKS_TOKEN
            )
            
            # Connect and create table
            if not loader.connect():
                raise Exception("Failed to connect to Databricks")
            
            try:
                loader.create_bronze_table()
                
                # Load data
                logger.info(f"[INFO] Loading {row_count} rows to Databricks...")
                rows_loaded = loader.load_csv_to_bronze(csv_filepath)
                
                # Get statistics
                stats = loader.get_table_stats()
                
                logger.info(f"[OK] Load complete: {rows_loaded} rows loaded")
                logger.info(f"[INFO] Bronze table stats: {stats}")
                
                context['ti'].xcom_push(key='rows_loaded', value=rows_loaded)
                context['ti'].xcom_push(key='db_stats', value=stats)
                
                return {
                    'status': 'success',
                    'rows_loaded': rows_loaded,
                    'stats': stats
                }
            
            finally:
                loader.close()
        
        except Exception as e:
            logger.error(f"[ERROR] Databricks load failed: {e}")
            raise AirflowException(f"Databricks load failed: {str(e)}")

    def validate_data_task(**context):
        """
        Validate data quality before transformation
        """
        logger.info("[START] Data Validation Task")
        
        try:
            row_count = context['ti'].xcom_pull(key='row_count', task_ids='extract_odds')
            rows_loaded = context['ti'].xcom_pull(key='rows_loaded', task_ids='load_to_databricks')
            
            logger.info(f"[INFO] Extracted: {row_count} rows")
            logger.info(f"[INFO] Loaded: {rows_loaded} rows")
            
            # Validation rules
            if row_count == 0:
                logger.warning("[WARNING] No data extracted - skipping transformation")
                return {'status': 'no_data', 'validation_passed': False}
            
            if rows_loaded != row_count:
                logger.warning(f"[WARNING] Row mismatch: extracted {row_count} but loaded {rows_loaded}")
            
            # If we have at least some data, proceed
            validation_passed = rows_loaded > 0
            
            logger.info(f"[OK] Validation complete: validation_passed={validation_passed}")
            context['ti'].xcom_push(key='validation_passed', value=validation_passed)
            
            return {
                'status': 'success',
                'validation_passed': validation_passed,
                'rows_validated': rows_loaded
            }
        
        except Exception as e:
            logger.error(f"[ERROR] Validation failed: {e}")
            raise AirflowException(f"Data validation failed: {str(e)}")

    def prepare_summary_task(**context):
        """
        Prepare summary for email alert
        """
        logger.info("[START] Prepare Summary Task")
        
        try:
            run_date = context['execution_date']
            row_count = context['ti'].xcom_pull(key='row_count', task_ids='extract_odds') or 0
            rows_loaded = context['ti'].xcom_pull(key='rows_loaded', task_ids='load_to_databricks') or 0
            db_stats = context['ti'].xcom_pull(key='db_stats', task_ids='load_to_databricks') or {}
            
            summary = {
                'run_date': run_date.isoformat(),
                'run_id': context['run_id'],
                'extracted_rows': row_count,
                'loaded_rows': rows_loaded,
                'total_bronze_rows': db_stats.get('row_count', 0),
                'sports_covered': db_stats.get('sports', 0),
                'matches_total': db_stats.get('matches', 0),
                'market_types': db_stats.get('markets', 0),
                'latest_data_date': str(db_stats.get('latest_date', 'N/A')),
                'status': 'success' if rows_loaded > 0 else 'no_data'
            }
            
            logger.info(f"[OK] Summary prepared: {summary}")
            context['ti'].xcom_push(key='pipeline_summary', value=summary)
            
            return summary
        
        except Exception as e:
            logger.error(f"[ERROR] Summary preparation failed: {e}")
            raise AirflowException(f"Summary preparation failed: {str(e)}")

    # ==================== OPERATOR TASKS ====================

    extract_odds = PythonOperator(
        task_id='extract_odds',
        python_callable=extract_odds_task,
        provide_context=True,
        doc='Extract odds from The Odds API for soccer leagues'
    )

    load_to_databricks = PythonOperator(
        task_id='load_to_databricks',
        python_callable=load_to_databricks_task,
        provide_context=True,
        doc='Load extracted CSV to Databricks bronze layer'
    )

    validate_data = PythonOperator(
        task_id='validate_data',
        python_callable=validate_data_task,
        provide_context=True,
        doc='Validate data quality and consistency'
    )

    prepare_summary = PythonOperator(
        task_id='prepare_summary',
        python_callable=prepare_summary_task,
        provide_context=True,
        doc='Prepare pipeline execution summary'
    )

    run_dbt_models = BashOperator(
        task_id='run_dbt_models',
        bash_command="""
            cd /opt/airflow/dbt/odds_transform && \
            dbt run --profiles-dir . --select staging intermediate marts 2>&1
        """,
        doc='Run dbt transformation models',
        trigger_rule='all_done'  # Run even if upstream has no data
    )

    run_dbt_tests = BashOperator(
        task_id='run_dbt_tests',
        bash_command="""
            cd /opt/airflow/dbt/odds_transform && \
            dbt test --profiles-dir . 2>&1
        """,
        doc='Run dbt data quality tests',
        trigger_rule='all_done'
    )

    send_success_email = EmailOperator(
        task_id='send_success_email',
        to=ALERT_EMAIL,
        subject='[SUCCESS] Odds Pipeline - Data Loaded to Databricks',
        html_content="""
        <h2>Pipeline Execution Summary</h2>
        <table border="1" cellpadding="10">
            <tr><td><b>Run Date</b></td><td>{{ ti.xcom_pull(task_ids='prepare_summary')['run_date'] }}</td></tr>
            <tr><td><b>Status</b></td><td>SUCCESS</td></tr>
            <tr><td><b>Rows Extracted</b></td><td>{{ ti.xcom_pull(task_ids='prepare_summary')['extracted_rows'] }}</td></tr>
            <tr><td><b>Rows Loaded</b></td><td>{{ ti.xcom_pull(task_ids='prepare_summary')['loaded_rows'] }}</td></tr>
            <tr><td><b>Total Bronze Records</b></td><td>{{ ti.xcom_pull(task_ids='prepare_summary')['total_bronze_rows'] }}</td></tr>
            <tr><td><b>Sports Covered</b></td><td>{{ ti.xcom_pull(task_ids='prepare_summary')['sports_covered'] }}</td></tr>
            <tr><td><b>Matches Available</b></td><td>{{ ti.xcom_pull(task_ids='prepare_summary')['matches_total'] }}</td></tr>
            <tr><td><b>Market Types</b></td><td>{{ ti.xcom_pull(task_ids='prepare_summary')['market_types'] }}</td></tr>
            <tr><td><b>Latest Data Date</b></td><td>{{ ti.xcom_pull(task_ids='prepare_summary')['latest_data_date'] }}</td></tr>
        </table>
        <br/>
        <h3>Next Steps:</h3>
        <ul>
            <li>Silver layer tables: Check Databricks schema.silver</li>
            <li>Gold layer tables: Check Databricks schema.gold</li>
            <li>Dashboard: Query fct_daily_odds_summary for daily summaries</li>
        </ul>
        """,
        trigger_rule='all_success'
    )

    send_failure_email = EmailOperator(
        task_id='send_failure_email',
        to=ALERT_EMAIL,
        subject='[FAILED] Odds Pipeline - Error Occurred',
        html_content="""
        <h2>Pipeline Execution Failed</h2>
        <p>The odds API pipeline encountered an error during execution.</p>
        <p><b>Error Details:</b></p>
        <ul>
            <li>Run ID: {{ run_id }}</li>
            <li>Execution Date: {{ execution_date }}</li>
            <li>Check Airflow UI for detailed logs</li>
        </ul>
        <p><a href="http://localhost:8080/dags/odds_api_pipeline/grid">View in Airflow</a></p>
        """,
        trigger_rule='one_failed'
    )

    # ==================== TASK DEPENDENCIES ====================
    
    extract_odds >> load_to_databricks >> validate_data >> prepare_summary
    
    [prepare_summary, validate_data] >> run_dbt_models >> run_dbt_tests
    
    [run_dbt_tests, prepare_summary] >> [send_success_email, send_failure_email]

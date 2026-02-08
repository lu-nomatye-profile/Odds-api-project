"""
Databricks Upload Module
Handles uploading extracted odds data to Databricks Delta Lake (Bronze Layer)
"""

import pandas as pd
import os
from datetime import datetime, timezone
from databricks import sql
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabricksLoader:
    """Load odds data to Databricks Delta Lake"""
    
    def __init__(self, server_hostname, http_path, access_token):
        """
        Initialize Databricks connection.
        
        Args:
            server_hostname: Databricks workspace URL (without https://)
            http_path: HTTP path to compute endpoint
            access_token: Databricks personal access token
        """
        self.server_hostname = server_hostname
        self.http_path = http_path
        self.access_token = access_token
        self.connection = None
        
        logger.info(f"[DATABRICKS] Initializing connection to {server_hostname[:20]}...")
    
    def connect(self):
        """Establish connection to Databricks"""
        try:
            self.connection = sql.connect(
                server_hostname=self.server_hostname,
                http_path=self.http_path,
                access_token=self.access_token
            )
            logger.info("[OK] Connected to Databricks successfully")
            return True
        except Exception as e:
            logger.error(f"[ERROR] Failed to connect to Databricks: {e}")
            return False
    
    def close(self):
        """Close Databricks connection"""
        if self.connection:
            self.connection.close()
            logger.info("[OK] Databricks connection closed")
    
    def create_bronze_table(self):
        """
        Create bronze layer table for raw odds data.
        Delta Lake format with ingestion partitioning.
        """
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS bronze.odds_raw (
            game_id STRING,
            sport_key STRING,
            sport_title STRING,
            home_team STRING,
            away_team STRING,
            commence_time TIMESTAMP,
            bookmaker STRING,
            market_type STRING,
            outcome_name STRING,
            odds DECIMAL(10,4),
            point DECIMAL(10,2),
            extracted_at TIMESTAMP,
            ingestion_date DATE,
            ingestion_timestamp TIMESTAMP
        )
        USING DELTA
        PARTITIONED BY (ingestion_date)
        """
        
        try:
            with self.connection.cursor() as cursor:
                logger.info("[INFO] Creating bronze.odds_raw table...")
                cursor.execute(create_table_sql)
                logger.info("[OK] Bronze table created/verified")
                return True
        except Exception as e:
            logger.warning(f"[WARNING] Table creation issue: {e}")
            return True  # Table might already exist
    
    def load_csv_to_bronze(self, csv_filepath, table_name='bronze.odds_raw'):
        """
        Load CSV data to bronze table using Databricks SQL.
        
        Args:
            csv_filepath: Path to CSV file
            table_name: Target table name
        
        Returns:
            Number of rows inserted
        """
        try:
            # Read CSV
            logger.info(f"[INFO] Reading CSV: {csv_filepath}")
            df = pd.read_csv(csv_filepath)
            
            if df.empty:
                logger.warning("[WARNING] CSV file is empty")
                return 0
            
            # Add ingestion columns
            ingestion_date = pd.Timestamp.now(tz=timezone.utc).date()
            ingestion_timestamp = datetime.now(timezone.utc).isoformat()
            
            df['ingestion_date'] = ingestion_date
            df['ingestion_timestamp'] = ingestion_timestamp
            
            # Ensure column data types are correct
            df['odds'] = pd.to_numeric(df['odds'], errors='coerce')
            df['point'] = pd.to_numeric(df['point'], errors='coerce')
            df['commence_time'] = pd.to_datetime(df['commence_time'])
            df['extracted_at'] = pd.to_datetime(df['extracted_at'])
            
            row_count = len(df)
            logger.info(f"[INFO] Loaded {row_count} rows from CSV")
            
            # Insert into Databricks using cursor
            with self.connection.cursor() as cursor:
                # Convert DataFrame to list of tuples for insertion
                columns = ','.join(df.columns)
                placeholders = ','.join(['?' for _ in df.columns])
                insert_sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                
                logger.info(f"[INFO] Inserting {row_count} rows into {table_name}...")
                
                # Insert in batches
                batch_size = 100
                for i in range(0, len(df), batch_size):
                    batch = df.iloc[i:i+batch_size]
                    for row in batch.values:
                        cursor.execute(insert_sql, tuple(row))
                    
                    logger.info(f"[INFO]   Inserted {min(i+batch_size, len(df))}/{row_count} rows")
                
            logger.info(f"[OK] Successfully inserted {row_count} rows to {table_name}")
            return row_count
        
        except FileNotFoundError:
            logger.error(f"[ERROR] CSV file not found: {csv_filepath}")
            return 0
        except Exception as e:
            logger.error(f"[ERROR] Failed to load CSV to Databricks: {e}")
            return 0
    
    def query_bronze_table(self, limit=10):
        """
        Query and display sample data from bronze table.
        
        Args:
            limit: Number of rows to fetch
        
        Returns:
            List of rows as dictionaries
        """
        try:
            with self.connection.cursor() as cursor:
                query = f"SELECT * FROM bronze.odds_raw LIMIT {limit}"
                logger.info(f"[INFO] Querying bronze table (limit {limit})...")
                cursor.execute(query)
                rows = cursor.fetchall()
                logger.info(f"[OK] Retrieved {len(rows)} rows")
                return rows
        except Exception as e:
            logger.error(f"[ERROR] Failed to query bronze table: {e}")
            return []
    
    def get_table_stats(self, table_name='bronze.odds_raw'):
        """
        Get statistics about the data in table.
        
        Args:
            table_name: Table to analyze
        
        Returns:
            Dictionary with statistics
        """
        try:
            with self.connection.cursor() as cursor:
                stats_queries = {
                    'row_count': f"SELECT COUNT(*) as count FROM {table_name}",
                    'latest_date': f"SELECT MAX(ingestion_date) as latest_date FROM {table_name}",
                    'sports': f"SELECT COUNT(DISTINCT sport_key) as sports FROM {table_name}",
                    'matches': f"SELECT COUNT(DISTINCT game_id) as matches FROM {table_name}",
                    'markets': f"SELECT COUNT(DISTINCT market_type) as markets FROM {table_name}"
                }
                
                stats = {}
                for key, query in stats_queries.items():
                    cursor.execute(query)
                    result = cursor.fetchone()
                    stats[key] = result[0] if result else 0
                
                logger.info(f"[INFO] Table statistics: {stats}")
                return stats
        except Exception as e:
            logger.error(f"[ERROR] Failed to get table stats: {e}")
            return {}


# Example usage
if __name__ == "__main__":
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Get credentials from environment
    databricks_host = os.getenv('DATABRICKS_HOST')
    databricks_http_path = os.getenv('DATABRICKS_HTTP_PATH')
    databricks_token = os.getenv('DATABRICKS_TOKEN')
    
    # Extract hostname from URL if needed
    if databricks_host.startswith('https://'):
        databricks_host = databricks_host.replace('https://', '').split('/')[0]
    
    if not all([databricks_host, databricks_http_path, databricks_token]):
        logger.error("[ERROR] Missing Databricks credentials in .env file")
        exit(1)
    
    # Initialize loader
    loader = DatabricksLoader(
        server_hostname=databricks_host,
        http_path=databricks_http_path,
        access_token=databricks_token
    )
    
    try:
        # Connect
        if loader.connect():
            # Create bronze table
            loader.create_bronze_table()
            
            # Find latest CSV file
            import glob
            csv_files = glob.glob('data/raw/*.csv')
            if csv_files:
                latest_csv = max(csv_files, key=os.path.getctime)
                logger.info(f"[INFO] Using file: {latest_csv}")
                
                # Load to Databricks
                rows_loaded = loader.load_csv_to_bronze(latest_csv)
                
                if rows_loaded > 0:
                    # Get stats
                    stats = loader.get_table_stats()
                    
                    print("\n" + "="*70)
                    print("DATABRICKS LOAD SUMMARY")
                    print("="*70)
                    print(f"Rows Loaded: {rows_loaded}")
                    print(f"Total Rows in Bronze: {stats.get('row_count', 'N/A')}")
                    print(f"Sports Covered: {stats.get('sports', 'N/A')}")
                    print(f"Total Matches: {stats.get('matches', 'N/A')}")
                    print(f"Market Types: {stats.get('markets', 'N/A')}")
                    print(f"Latest Data Date: {stats.get('latest_date', 'N/A')}")
                    print("="*70 + "\n")
            else:
                logger.warning("[WARNING] No CSV files found in data/raw/")
    
    finally:
        loader.close()

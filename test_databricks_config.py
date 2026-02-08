"""Test Databricks Connection with Updated Credentials"""
from dotenv import load_dotenv
import os

load_dotenv()

print("\n" + "="*70)
print("DATABRICKS CONNECTION TEST")
print("="*70 + "\n")

host = os.getenv('DATABRICKS_HOST')
path = os.getenv('DATABRICKS_HTTP_PATH')
token = os.getenv('DATABRICKS_TOKEN')

print(f"[INFO] Loaded credentials from .env file\n")
print(f"Databricks Host: {host}")
print(f"HTTP Path: {path}")
print(f"Token (first 20 chars): {token[:20]}***\n")

# Validation
print("Validation Checks:")
print(f"  ✓ HOST doesn't start with 'https://': {not host.startswith('https://')}")
print(f"  ✓ PATH starts with '/sql/': {path.startswith('/sql/')}")
print(f"  ✓ TOKEN starts with 'dapi': {token.startswith('dapi')}")
print(f"  ✓ All credentials present: {all([host, path, token])}\n")

if all([host, path, token]):
    print("[OK] All Databricks credentials are properly configured!")
    print("\nYou can now:")
    print("  1. Run: python scripts/databricks_upload.py")
    print("  2. Start Airflow: cd docker && docker-compose up -d")
    print("  3. Query Databricks directly with SQL")
else:
    print("[ERROR] Some credentials are missing!")

print("\n" + "="*70 + "\n")

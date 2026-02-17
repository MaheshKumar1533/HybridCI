"""
Configuration loader
"""
import yaml
import os

def load_config():
    """Load configuration from config.yaml."""
    with open('config.yaml', 'r') as f:
        return yaml.safe_load(f)

DATABASE_URL = os.environ.get('DATABASE_URL')
API_SECRET = os.environ.get('API_SECRET')

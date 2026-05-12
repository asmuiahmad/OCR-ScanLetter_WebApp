from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
import json
import os

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

def load_metadata():
    """
    Load metadata from metadata.json file.
    If file doesn't exist, return an empty dictionary.
    """
    metadata_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'metadata.json')
    
    # If file does not exist, return an empty dictionary
    if not os.path.exists(metadata_path):
        return {}
    
    try:
        with open(metadata_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        # If there is an error reading the file, return an empty dictionary
        return {}

def save_metadata(metadata):
    """
    Save metadata to metadata.json file.
    
    :param metadata: Dictionary containing metadata to save
    """
    metadata_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'metadata.json')
    
    try:
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=4)
    except IOError as e:
        print(f"Error saving metadata: {e}")

import os
import sys
import click

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.extensions import db
from app import create_app

@click.command()
def reset_database():
    """Reset the entire database."""
    # Create app context
    app = create_app()
    
    with app.app_context():
        # Drop all existing tables
        db.drop_all()
        click.echo("Dropped all existing tables.")
        
        # Create new tables
        db.create_all()
        click.echo("Created new tables.")
        
        click.echo("Database reset completed successfully.")

if __name__ == '__main__':
    reset_database() 
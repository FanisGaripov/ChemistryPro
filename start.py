from server import app, db
from flask_migrate import Migrate, upgrade

migrate = Migrate(app, db)

def run_migrations():
    with app.app_context():
        upgrade()

if __name__ == "__main__":
    run_migrations()
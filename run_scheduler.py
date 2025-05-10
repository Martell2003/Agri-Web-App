import logging
from app import create_app
from app.scheduler import start_scheduler

# Configure logging
logging.basicConfig(
    filename='debug.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)

app = create_app()
with app.app_context():
    start_scheduler()
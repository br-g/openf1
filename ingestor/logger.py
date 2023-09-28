import sys
from loguru import logger

# Initialize logging for Cloud Run
logger.remove()
logger.add(sys.stdout, level='INFO')

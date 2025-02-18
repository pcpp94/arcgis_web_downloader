import logging
import os
from .config import LOG_DIR

def setup_logger(log_level=logging.INFO):
    logging.basicConfig(
        filename=os.path.join(LOG_DIR,'arcgis.log'),
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger()

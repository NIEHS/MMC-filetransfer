import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def add_log_handlers(filename:Path) -> None:
    logger.debug(f'Creating log file for session at {filename}')
    main_handler = logging.FileHandler(str(filename), mode='a', encoding='utf-8')
    main_handler.setFormatter(logging.getLogger('root').handlers[0].formatter)
    logging.getLogger(__name__).addHandler(main_handler)
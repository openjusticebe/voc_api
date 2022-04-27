import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.getLevelName('INFO'))
logger.addHandler(logging.StreamHandler())


def get_index():
    # pass along whoosh index
    pass

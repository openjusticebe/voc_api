import calendar
import math
import os
from datetime import datetime

import pytz

COUNTER = 0


def check_envs(env_list):
    return all(os.getenv(e) for e in env_list)


def get_now():
    now = datetime.now(pytz.utc)
    return calendar.timegm(now.utctimetuple())


def status_get(start_time, version):
    now = datetime.now(pytz.utc)
    delta = now - start_time
    delta_s = math.floor(delta.total_seconds())
    return {
        'all_systems': 'nominal',
        'id': __name__,
        'timestamp': str(now),
        'online_since': str(start_time),
        'online_for_seconds': delta_s,
        'api_version': version,
        'api_counter': COUNTER,
    }

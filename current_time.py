"""
Author: Patrick Thomas

Helper to get the time as a string.
"""

import time


def s_time():
    """
    Get the current time as a ASC string.
    :return: string, time
    """

    return time.asctime(time.localtime())

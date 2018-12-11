
import time

start_time = time.time()



def check_time():
    """
    :return: This function returns a string of how many minutes or hours the script
    has run so far.
    """
    time_so_far = time.time() - start_time
    time_so_far /= 60  # changes this from seconds to minutes

    if time_so_far < 60.:
        return str(int(round(time_so_far))) + " minutes"

    else:
        return str(round(time_so_far / 60., 1)) + " hours"


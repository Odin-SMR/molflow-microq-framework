import sys
import traceback
import threading


def get_current_stacks():
    """Return list of current stacks as strings for all running threads
    excluding this thread.
    """
    this_thread = threading.current_thread().ident
    stacks = []
    for ident, frame in sys._current_frames().items():
        if ident == this_thread:
            continue
        stacks.append(''.join(traceback.format_stack(frame)))
    return stacks

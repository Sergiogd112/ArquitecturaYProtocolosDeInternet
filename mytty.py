import os
import subprocess
def get_tty_width():
    try:
        return os.get_terminal_size().columns
    except OSError:
        return 80  # Default value for terminal width


import inspect
import logging
import os
import sys
import traceback
from typing import Optional

# Define two formatters: one with line numbers (for ERROR) and one without (for others)
standard_formatter = logging.Formatter('%(levelname)s - %(name)s - %(message)s')
error_formatter = logging.Formatter(
    '%(levelname)s - %(name)s - %(message)s [in %(pathname)s:%(lineno)d]')

class LoggerSetup(logging.Logger):
    def __init__(self, log_level: Optional[str] = None):

        # Get the name of the calling module
        caller_frame = inspect.stack()[1]
        module = inspect.getmodule(caller_frame[0])

        # Use module's name, or fallback to filename (if `__main__` detected)
        if module and module.__name__ != "__main__":
            logger_name = module.__name__
        else:
            # Get the file path of the caller
            file_path = os.path.relpath(caller_frame.filename)
            # Replace the file separators with dots and remove the `.py` extension
            logger_name = file_path.replace(os.path.sep, ".").replace('.py', '')

        # Initialize the base Logger with the determined name
        super().__init__(logger_name)

        # Set log level from parameter or environment
        if log_level:
            self.setLevel(log_level.upper())
        elif os.getenv("LOG_LEVEL"):
            self.setLevel(os.getenv("LOG_LEVEL").upper())
        else:
            self.setLevel(logging.NOTSET)

        # Create console handler for stdout with specific log level
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.level)

        # Custom filter to apply the correct formatter based on log level
        class LevelBasedFormatter(logging.Filter):
            def filter(self, record):
                if record.levelno == logging.ERROR:
                    console_handler.setFormatter(error_formatter)
                else:
                    console_handler.setFormatter(standard_formatter)
                return True

        # Attach the filter to the handler
        console_handler.addFilter(LevelBasedFormatter())

        # Clear existing handlers to avoid duplicates and add the new handler
        if not self.hasHandlers():
            self.addHandler(console_handler)

    def error(self, msg, *args, exc_info=True, **kwargs):
        """
        Overrides the error method to automatically include traceback information
        when logging an error.
        """
        msg = self.add_traceback(exc_info, msg)
        super().error(msg, *args, exc_info=exc_info, **kwargs)

    def critical(self, msg, *args, exc_info=True, **kwargs):
        """
        Overrides the critical method to automatically include traceback information
        when logging an error.
        """
        msg = self.add_traceback(exc_info, msg)
        super().critical(msg, *args, exc_info=exc_info, **kwargs)

    @staticmethod
    def add_traceback(exc_info, msg):
        if exc_info:
            # Capture the full traceback and use the last entry for accurate line info
            _, _, exc_traceback = sys.exc_info()
            if exc_traceback:
                tb = traceback.extract_tb(exc_traceback)
                if tb:
                    filename, lineno, _, _ = tb[-1]
                    # Append the traceback location to the message
                    msg = f"{msg} [in {filename}:{lineno}]"
        return msg

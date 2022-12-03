"""Custom Exceptions"""


class StargazerException(Exception):
    """Encapsulate native Exception"""

    def __init__(self, message: str):
        self.message = message

class Singleton:  # pylint: disable=too-few-public-methods
    """Singleton base class.
    https://mail.python.org/pipermail/python-list/2007-July/450681.html
    """

    def __new__(cls, *args, **kwargs):  # pylint: disable=unused-argument
        """Create a new instance."""
        if "_inst" not in vars(cls):
            cls._inst = object.__new__(cls)
        return cls._inst

class Defaults(Singleton):
    TcpPort = 502
    SlaveId = 1
    SerialNumberPrefix = 1530
    MaxNumberOfRooms = 24
    BaudRate = 19200
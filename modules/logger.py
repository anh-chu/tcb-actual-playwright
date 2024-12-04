import logging

_fmt_file_debug = "[ %(asctime)s ] [ DBUG ] (%(name)s) %(message)s"
_fmt_file_info = "[ %(asctime)s ] [ INFO ] (%(name)s) %(message)s"
_fmt_file_warning = "[ %(asctime)s ] [ WARN ] (%(name)s) %(message)s"
_fmt_file_error = "[ %(asctime)s ] [ ERRO ] (%(name)s) %(message)s"
_fmt_file_critical = "[ %(asctime)s ] [ CRIT ] (%(name)s) %(message)s"

_fmt_console_debug = "[ DBUG ]" + " (%(name)s) %(message)s"
_fmt_console_info = (
    "\u001b[0;34m" + "[ INFO ]" + "\u001b[0m" + " (%(name)s) %(message)s"
)
_fmt_console_warning = (
    "\u001b[33;20m" + "[ WARN ]" + "\u001b[0m" + " (%(name)s) %(message)s"
)
_fmt_console_error = (
    "\u001b[0;31m" + "[ ERRO ]" + "\u001b[0m" + " (%(name)s) %(message)s"
)
_fmt_console_critical = (
    "\u001b[1;31m" + "[ CRIT ]" + " (%(name)s) %(message)s" + "\u001b[0m"
)


class _FormatterConsole(logging.Formatter):
    def __init__(self, time: bool):
        time_fmt = "[ %H:%M:%S ] " if time else ""
        self.formatters = {
            logging.DEBUG: logging.Formatter(fmt=_fmt_console_debug, datefmt=time_fmt),
            logging.INFO: logging.Formatter(fmt=_fmt_console_info, datefmt=time_fmt),
            logging.WARNING: logging.Formatter(
                fmt=_fmt_console_warning, datefmt=time_fmt
            ),
            logging.ERROR: logging.Formatter(fmt=_fmt_console_error, datefmt=time_fmt),
            logging.CRITICAL: logging.Formatter(
                fmt=_fmt_console_critical, datefmt=time_fmt
            ),
        }

    def format(self, record):
        return self.formatters[record.levelno].format(record)


class _FormatterFile(logging.Formatter):
    _formatters_file = {
        logging.DEBUG: logging.Formatter(fmt=_fmt_file_debug),
        logging.INFO: logging.Formatter(fmt=_fmt_file_info),
        logging.WARNING: logging.Formatter(fmt=_fmt_file_warning),
        logging.ERROR: logging.Formatter(fmt=_fmt_file_error),
        logging.CRITICAL: logging.Formatter(fmt=_fmt_file_critical),
    }

    def format(self, record):
        return _FormatterFile._formatters_file[record.levelno].format(record)


def consoleHandler(
    time: bool = True, level: int = logging.INFO
) -> logging.StreamHandler:
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(_FormatterConsole(time))
    console_handler.setLevel(level)
    return console_handler


def fileHandler(file: str, level: int = logging.DEBUG) -> logging.FileHandler:
    file_handler = logging.FileHandler(file)
    file_handler.setFormatter(_FormatterFile())
    file_handler.setLevel(level)
    return file_handler


class Logger(logging.Logger):
    def __init__(
        self,
        name: str,
        level: int = logging.INFO,
        file: str | None = None,
        time: bool = True,
    ):
        self._file = file
        self._time = time
        super().__init__(name)
        self.addHandler(consoleHandler(time, level))
        if file is not None:
            self.addHandler(fileHandler(file))
        self.setLevel(logging.DEBUG)

    def getChild(self, name: str) -> logging.Logger:
        child = Logger(self.name + "." + name, self.level, self._file, self._time)
        return child


logger = Logger("tcb-actual", logging.DEBUG, "tcb-actual.log")


if __name__ == "__main__":
    logger.debug("debug")
    logger.info("info")
    logger.warning("warning")
    logger.error("error")
    logger.critical("critical")

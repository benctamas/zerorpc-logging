import zerorpc
import gevent.queue
import logging
import sys

logging.basicConfig()

# root logger
logger = logging.getLogger()

# set the mimimum level for root logger so it will be possible for a client 
# to subscribe and receive logs for any log level
logger.setLevel(0)


class QueueingLogHandler(logging.Handler):
    """ A simple logging handler which puts all emitted logs into a
        gevent queue.
    """

    def __init__(self, queue, level, formatter):
        super(QueueingLogHandler, self).__init__()
        self._queue = queue
        self.setLevel(level)
        self.setFormatter(formatter)
    
    def emit(self, record):
        msg = self.format(record)
        self._queue.put_nowait(msg)
    
    def close(self):
        super(QueueingLogHandler, self).close()
        self._queue.put_nowait(None)
    
    @property
    def emitted(self):
        return self._queue


class TestService(object):
    
    _HANDLER_CLASS = QueueingLogHandler
    _DEFAULT_FORMAT = '%(name)s - %(levelname)s - %(asctime)s - %(message)s'
    
    logger = logging.getLogger("service")

    def __init__(self):
        self._logging_handlers = set()
    
    def test(self, logger_name, logger_level, message):
        logger = logging.getLogger(logger_name)
        getattr(logger, logger_level.lower())(message)

    def available_loggers(self):
        """ List of initalized loggers """
        return logging.getLogger().manager.loggerDict.keys()
    
    def close_log_streams(self):
        """ Closes all log_stream streams. """
        while self._logging_handlers:
            self._logging_handlers.pop().close()

    @zerorpc.stream
    def log_stream(self, logger_name, level_name, format_str):
        """ Attaches a log handler to the specified logger and sends emitted logs 
            back as stream. 
        """
        if logger_name != "" and logger_name not in self.available_loggers():
            raise ValueError("logger {0} is not available".format(logger_name))

        level_name_upper = level_name.upper() if level_name else "NOTSET"
        try:
            level = getattr(logging, level_name_upper)
        except AttributeError, e:
            raise AttributeError("log level {0} is not available".format(level_name_upper))
        
        q = gevent.queue.Queue()
        fmt = format_str if format_str.strip() else self._DEFAULT_FORMAT 
        
        logger = logging.getLogger(logger_name)
        formatter = logging.Formatter(fmt)
        handler = self._HANDLER_CLASS(q, level, formatter)
        
        logger.addHandler(handler)
        self._logging_handlers.add(handler)

        self.logger.debug("new subscriber for {0}/{1}".format(logger_name or "root", level_name_upper))
        try:
            for msg in handler.emitted:
                if msg is None:
                    return
                yield msg
        finally:
            self._logging_handlers.discard(handler)
            handler.close()
            self.logger.debug("subscription finished for {0}/{1}".format(logger_name or "root", level_name_upper))
    
    
if __name__ == "__main__":
    service = TestService()
    server = zerorpc.Server(service)
    server.bind(sys.argv[1])
    logger.warning("starting service")
    try: 
        server.run()
    except BaseException, e:
        logger.error(str(e))
    finally:
        logger.warning("shutting down")



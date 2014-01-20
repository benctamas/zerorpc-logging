Poc code for a zerorpc service where clients can subscribe to log messages emitted by any existing python logger.

I would like to use it only for debugging purposes.

Start the service:

	sh1# python logstream_test.py tcp://127.0.0.1:5000


Add subscribers:

	# stream of log messages emitted by root logger, any level, default formatter
	sh2# zerorpc tcp://127.0.0.1:5000 log_stream "" "" ""

	# stream of log messages emitted by "service" logger, with "ERROR" or higher level, using custom formatter
	sh3# zerorpc tcp://127.0.0.1:5000 log_stream "service" "ERROR" "%(name)s:%(levelname)s %(asctime)s %(message)s"


Generate some logs:
	
	sh4# zerorpc tcp://127.0.0.1:5000 test "service" "ERROR" "some error message"
	sh4# zerorpc tcp://127.0.0.1:5000 test "service" "DEBUG" "some debug message"


Close subscribers:

	sh4# zerorpc tcp://127.0.0.1:5000 close_log_streams


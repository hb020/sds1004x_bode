'''
Created on May 5, 2018

@author: dima
'''

import argparse
from awg_server import AwgServer
from awg_factory import awg_factory

DEFAULT_AWG = "dummy"
DEFAULT_PORT = "/dev/ttyUSB0"
DEFAULT_BAUD_RATE = 19200

def main():
    parser = argparse.ArgumentParser(description="Siglent SDS 800X-HD/1000X-E to non-Siglent AWG bode plot bridge.")
    parser.add_argument("awg", type=str.lower, nargs='?', default=DEFAULT_AWG, choices=awg_factory.get_names(), help=f"The AWG to use. (default: {DEFAULT_AWG})")
    parser.add_argument("port", type=str, nargs='?', default=DEFAULT_PORT, help=f"The port to use. Either a serial port, or a Visa compatible connection string. (default: {DEFAULT_PORT})")
    parser.add_argument("baudrate", type=int, nargs='?', default=DEFAULT_BAUD_RATE, help=f"When using serial, baud rate to use. (default: {DEFAULT_BAUD_RATE})")
    parser.add_argument('-v', default=0, help="Verbosity level. Specify one or more 'v' for more detail in the logs.", action="count", dest="verbosity")
    parser.add_argument('-1', default=0, help="Run only once: exit after one bode plot is done. If not specified: use Ctrl-C to stop the program.", dest="runonce", action="store_true", required=False)
    args = parser.parse_args()

    # Extract AWG name from parameters
    awg_name = args.awg
    # Extract port name from parameters
    awg_port = args.port
    # Extract AWG port baud rate from parameters
    awg_baud_rate = args.baudrate
    # and whether to run only once
    runonce = args.runonce
    
    # Using the logging module in multiprocessing makes the code more complicated to read.
    # So I keep it simple
    log_commands = False
    log_mapping = False
    log_VXI = False
    
    if args.verbosity > 0:
        log_commands = True    
    if args.verbosity > 1:
        log_VXI = True
    if args.verbosity > 2:
        log_mapping = True

    # Initialize AWG
    print("Initializing AWG...")
    print(f"AWG: {awg_name}")
    print(f"Port: {awg_port}")
    awg_class = awg_factory.get_class_by_name(awg_name)
    awg = awg_class(port=awg_port, baud_rate=awg_baud_rate, log_debug=log_commands)
    awg.initialize()
    print(f"IDN: {awg.get_id()}")
    print("AWG initialized.")
    if runonce:
        print("The program will stop after one bode plot is done. You can also use Ctrl-C to stop the program at any time.")
    else:
        print("Use Ctrl-C to stop the program.")

    # Run AWG server
    server = None
    try:
        server = AwgServer(awg, log_VXI=log_VXI, log_mapping=log_mapping, runonce=runonce)
        server.start()

    except KeyboardInterrupt:
        print('Ctrl+C pressed. Exiting...')

    finally:
        print("Stopping server...")
        if server is not None:
            server.close_sockets()
            del server

    print("Bye.")


if __name__ == '__main__':
    main()
# This is the main entry point for the sds1004x_bode package.
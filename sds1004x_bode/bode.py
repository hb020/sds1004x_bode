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

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Siglent SDS 800X-HD/1000X-E to non-Siglent AWG bode plot bridge.",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("awg", type=str, nargs='?', default=DEFAULT_AWG, choices=awg_factory.get_names(), help="The AWG to use.")
    parser.add_argument("port", type=str, nargs='?', default=DEFAULT_PORT, help="The port to use. Either a serial port, or a Visa compatible connection string.")
    parser.add_argument("baudrate", type=int, nargs='?', default=DEFAULT_BAUD_RATE, help="When using serial, baud rate to use.")
    parser.add_argument("-udp", action="store_true", default=False, dest="portmap_on_udp", help="Use UDP for the init phase (is needed by SDS800X-HD/SDS1000X-HD series for example).")
    args = parser.parse_args()

    # Extract AWG name from parameters
    awg_name = args.awg
    # Extract port name from parameters
    awg_port = args.port
    # Extract AWG port baud rate from parameters
    awg_baud_rate = args.baudrate

    # Initialize AWG
    print("Initializing AWG...")
    print("AWG: %s" % awg_name)
    print("Port: %s" % awg_port)
    awg_class = awg_factory.get_class_by_name(awg_name)
    awg = awg_class(awg_port, awg_baud_rate)
    awg.initialize()
    print("IDN: %s" % awg.get_id())
    print("AWG initialized.")

    # Run AWG server
    server = None
    try:
        server = AwgServer(awg, portmap_on_udp=args.portmap_on_udp)
        server.start()

    except KeyboardInterrupt:
        print('Ctrl+C pressed. Exiting...')

    finally:
        if server is not None:
            server.close_sockets()

    print("Bye.")

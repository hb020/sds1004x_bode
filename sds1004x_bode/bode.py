'''
Created on May 5, 2018

@author: dima
'''

import argparse
import pyvisa as visa
from awg_server import AwgServer
from awg_factory import awg_factory

DEFAULT_AWG = "dummy"
DEFAULT_PORT = "/dev/ttyUSB0"
DEFAULT_BAUD_RATE = 19200

def show_visa_instruments(force_pyvisa_py: bool = False):
    print("Scanning for VISA resources...")
    rm = visa.ResourceManager("@py" if force_pyvisa_py else "")
    resources = rm.list_resources()
    resources = sorted(resources)
    resources = [r for r in resources if not r.startswith("ASRL/dev/cu.")]  # skip known bad devices that very likely not SCPI compatible
    if len(resources) == 0:
        print("No VISA resources found.")
        return
    # get longest address length for better formatting
    max_len = max([len(m) for m in resources])
    max_len += 2  # add some padding
    if max_len < 20:
        max_len = 20
    max_name = 60
    print("VISA Resources found: ")
    print(f"{'Address':<{max_len}} Identification")
    print(f"{'-'*max_len} {'-'*max_name}")
    
    for m in resources:            
        inst = None
        try:
            inst = rm.open_resource(m, timeout=1000)
            r = inst.query("*IDN?").strip()
            print(f"{m:<{max_len}} {r}")
            inst.close()
        except:
            if (inst is not None):
                inst.close()
                print(f"{m:<{max_len}} unknown instrument at this address")
            else:
                print(f"{m:<{max_len}} no instrument at this address")


def main():
    
    detect_str = "visadetect"
    awg_names = awg_factory.get_names()
    awg_names = awg_names + [detect_str]
    
    parser = argparse.ArgumentParser(description="Siglent SDS 800X-HD/1000X-E to non-Siglent AWG bode plot bridge.")
    parser.add_argument("awg", type=str.lower, nargs='?', default=DEFAULT_AWG, choices=awg_names, help=f"The AWG to use. (default: {DEFAULT_AWG}). Use '{detect_str}' to automatically detect all connected VISA instruments.")
    parser.add_argument("port", type=str, nargs='?', default=DEFAULT_PORT, help=f"The port to use. Either a serial port, or a Visa compatible connection string. (default: {DEFAULT_PORT})")
    parser.add_argument("baudrate", type=int, nargs='?', default=DEFAULT_BAUD_RATE, help=f"When using serial, baud rate to use. (default: {DEFAULT_BAUD_RATE})")
    parser.add_argument('-v', default=0, help="Verbosity level. Specify one or more 'v' for more detail in the logs.", action="count", dest="verbosity")
    parser.add_argument('-1', default=False, help="Run only once: exit after one bode plot is done. If not specified: use Ctrl-C to stop the program.", dest="runonce", action="store_true", required=False)
    parser.add_argument('-old', default=False, help="If you have old firmware on the scope, you must set this. It forces changing of the VXI-11 ports at every request.", dest="old_firmware", action="store_true", required=False)
    parser.add_argument('-py', '--pyvisa-py', default=False, help="Force the use of PyVISA-Py.", dest="pyvisa_py", action="store_true", required=False)
    args = parser.parse_args()

    # Extract AWG name from parameters
    awg_name = args.awg
    # Extract port name from parameters
    awg_port = args.port
    # Extract AWG port baud rate from parameters
    awg_baud_rate = args.baudrate
    # and whether to run only once
    runonce = args.runonce
    # and whether to use old firmware mode
    change_ports = args.old_firmware
    # Using the logging module in multiprocessing makes the code more complicated to read.
    # So I keep it simple
    log_commands = False
    log_mapping = False
    log_VXI = False
    force_pyvisa_py = args.pyvisa_py
    
    if args.verbosity > 0:
        log_commands = True    
    if args.verbosity > 1:
        log_VXI = True
    if args.verbosity > 2:
        log_mapping = True
        
    if awg_name == detect_str:
        show_visa_instruments(force_pyvisa_py = force_pyvisa_py)
        return

    # Initialize AWG
    print("Initializing AWG...")
    print(f"AWG: {awg_name}")
    print(f"Port: {awg_port}")
    awg_class = awg_factory.get_class_by_name(awg_name)
    awg = awg_class(port=awg_port, baud_rate=awg_baud_rate, log_debug=log_commands, force_pyvisa_py=force_pyvisa_py)
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
        server = AwgServer(awg, log_VXI=log_VXI, log_mapping=log_mapping, runonce=runonce, change_ports=change_ports)
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
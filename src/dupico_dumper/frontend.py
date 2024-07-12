"""Frontend module"""

import argparse
import traceback

import serial

from dupico_dumper import __name__, __version__
from dupico_dumper.dumper_utilities import DumperUtilities

def _build_argsparser() -> argparse.ArgumentParser:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        prog=__name__,
        description='A tool for fiddling with a dupico board'
    )
    
   
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    parser.add_argument('-v', '--verbose', action='count', default=0)

    arg_group = parser.add_argument_group()
    arg_group.add_argument('-p', '--port',
                        required=True,
                        type=str,
                        nargs='?',
                        metavar="<serial port>",
                        help='Serial port associated with the board')
    
    mut_group = arg_group.add_mutually_exclusive_group()
    mut_group.add_argument('--hw_version',
                           action='store_true', 
                           help='Read the hardware board version',
                           required=False)


    return parser

def cli() -> int:
    args = _build_argsparser().parse_args()

    if not args.port:
        DumperUtilities.print_serial_ports()      
        return 1
    else:
        ser_port: serial.Serial | None = None

        try:
            ser_port = serial.Serial(port = args.port,
                                     baudrate=115200,
                                     bytesize = 8,
                                     stopbits = 1,
                                     parity = 'N',
                                     timeout = 5.0)

            if not DumperUtilities.check_connection_string(ser_port):
                print('Serial port connected, but the board did not respond in time.')
                return -1
            else:
                print('Board connected...')

        except Exception as ex:
            if args.verbose:
                print(traceback.format_exc())
            else:
                print(ex)
            return -1

        finally:
            if ser_port and not ser_port.closed:
                ser_port.close()

        print('Bye bye!')
        return 1 
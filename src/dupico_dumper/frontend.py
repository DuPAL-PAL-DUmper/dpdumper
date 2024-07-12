"""Frontend module"""

import argparse
import traceback

import serial

from dupico_dumper import __name__, __version__

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

    return parser

def cli() -> int:
    args = _build_argsparser().parse_args()

    if not args.port:        
        return 1
    else:
        ser_port: serial.Serial

        try:
            ser_port = serial.Serial(port = args.port,
                                     baudrate=115200,
                                     bytesize = 8,
                                     stopbits = 1,
                                     parity = 'N',
                                     rtscts = True,
                                     timeout = 1.0)
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
"""Frontend module"""

import argparse
import traceback

import serial

from enum import Enum

from dupico_dumper import __name__, __version__
from dupico_dumper.dumper_utilities import DumperUtilities
from dupico_dumper.board_commands import BoardCommands
from dupico_dumper.ll_board_utilities import LLBoardUtilities

MIN_SUPPORTED_MODEL: int = 3

class Subcommands(Enum):
    TEST = 'test'
    WRITE = 'write'
    READ = 'read'

def _build_argsparser() -> argparse.ArgumentParser:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        prog=__name__,
        description='A tool for fiddling with a dupico board'
    )
   
    parser.add_argument('-v', '--verbose', action='count', default=0)
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    parser.add_argument('-p', '--port',
                        required=True,
                        type=str,
                        nargs='?',
                        metavar="serial port",
                        help='Serial port associated with the board')
    
    subparsers = parser.add_subparsers(help='supported subcommands', dest='subcommand')
    subparsers.add_parser(Subcommands.TEST.value, help='Execute the selftest routine of the dupico board')

    parser_read = subparsers.add_parser(Subcommands.READ.value, help='Read data from an IC')
    parser_read.add_argument('-d', '--definition',
                             nargs=1,
                             metavar='definition file',
                             help='Path to the file containing the definition of the IC to be read',
                             required=True)
    parser_read.add_argument('-o', '--outfile',
                             type=str,
                             nargs=1,
                             metavar='output file',
                             help='Output file that will contain the data read from the IC in ASCII human-readable format',
                             required=True)
    parser_read.add_argument('-ob', '--outfile_binary',
                             type=str,
                             nargs=1,
                             metavar='binary output file',
                             help='Binary output file that will contain the data read from the IC')
    parser_read.add_argument('--hiz_high',
                             action='store_true',
                             default=False,
                             help='The binary output will be saved with hi-z bits set to 1')

    parser_write = subparsers.add_parser(Subcommands.WRITE.value, help='Write the content of a file into a supported (and writable) IC')
    parser_write.add_argument('-d', '--definition',
                             nargs=1,
                             metavar='definition file',
                             help='Path to the file containing the definition of the IC to be written',
                             required=True)
    parser_write.add_argument('-i', '--infile',
                              type=str,
                              nargs=1,
                              metavar='input file',
                              help='File with the contents that will be written to the IC',
                              required=True)

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

            if not LLBoardUtilities.check_connection_string(ser_port):
                print('Serial port connected, but the board did not respond in time.')
                return -1
            
            print('Board connected...')
            model: int | None = BoardCommands.get_model(ser_port)
            if model is None:
                print('Unable to retrieve model number...')
                return -1
            elif model < MIN_SUPPORTED_MODEL:
                print(f'Model {model} is not supported.')
                return -1
            
            print(f'Model {model} detected!')

            match args.subcommand:
                case Subcommands.TEST.value:
                    print('Testing the board, make sure the ZIF socket is empty!')
                    test_result: bool | None = BoardCommands.test_board(ser_port)

                    if test_result is None:
                        print('Unable to get a proper response.')
                    else:
                        print(f'Test result is {"OK" if test_result else "BAD"}!')                    
                case _:
                    print(f'Unsupported command {args.subcommand}')


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
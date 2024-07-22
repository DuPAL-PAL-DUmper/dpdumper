"""Frontend module"""

import argparse
import traceback
import logging

import serial

from enum import Enum

from dupicolib.board_commands import BoardCommands
from dupicolib.board_utilities import BoardUtilities

from dpdumper import __name__, __version__
from dpdumper.dumper_utilities import DumperUtilities
from dpdumper.hl_board_utilities import HLBoardUtilities, DataElement
from dpdumper.ic.ic_loader import ICLoader
from dpdumper.ic.ic_definition import ICDefinition

import dpdumper.outfile_utilities as OutFileUtilities

MIN_SUPPORTED_MODEL: int = 3

_LOGGER: logging.Logger = logging.getLogger(__name__)

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
    
    parser.add_argument('-b', '--baudrate',
                        type=int,
                        metavar="Baud rate",
                        default=115200,
                        help='Speed at which to the serial port is opened')
    
    subparsers = parser.add_subparsers(help='supported subcommands', dest='subcommand')
    subparsers.add_parser(Subcommands.TEST.value, help='Execute the selftest routine of the dupico board')

    parser_read = subparsers.add_parser(Subcommands.READ.value, help='Read data from an IC')
    parser_read.add_argument('-d', '--definition',
                             metavar='definition file',
                             help='Path to the file containing the definition of the IC to be read',
                             required=True)
    parser_read.add_argument('-o', '--outfile',
                             type=str,
                             metavar='output file',
                             help='Output file that will contain the data read from the IC in ASCII human-readable format',
                             required=True)
    parser_read.add_argument('-ob', '--outfile_binary',
                             type=str,
                             metavar='binary output file',
                             help='Binary output file that will contain the data read from the IC')
    parser_read.add_argument('--check_hiz',
                             action='store_true',
                             default=False,
                             help='Check if data pins are Hi-Z or not. Slows down the read.')    
    parser_read.add_argument('--hiz_high',
                             action='store_true',
                             default=False,
                             help='The binary output will be saved with hi-z bits set to 1')

    parser_write = subparsers.add_parser(Subcommands.WRITE.value, help='Write the content of a file into a supported (and writable) IC')
    parser_write.add_argument('-d', '--definition',
                             metavar='definition file',
                             help='Path to the file containing the definition of the IC to be written',
                             required=True)
    parser_write.add_argument('-i', '--infile',
                              type=str,
                              metavar='input file',
                              help='File with the contents that will be written to the IC',
                              required=True)

    return parser

def test_command(ser: serial.Serial) -> None:
    print('Testing the board, make sure the ZIF socket is empty!')
    test_result: bool | None = BoardCommands.test_board(ser)

    if test_result is None:
        print('Unable to get a proper response.')
    else:
        print(f'Test result is {"OK" if test_result else "BAD"}!')

def read_command(ser: serial.Serial, deff: str, outf: str, outfb: str | None = None, check_hiz: bool = False, hiz_high: bool = False) -> None:
    _LOGGER.debug(f'Read command with definition {deff}, output table {outf}, output binary {outfb}, check hi-z {check_hiz}, treat hi-z as high {hiz_high}')

    ic_definition: ICDefinition = ICLoader.extract_definition_from_file(deff)
    ic_data: list[DataElement] | None = HLBoardUtilities.read_ic(ser, ic_definition, check_hiz)

    if ic_data is None:
        _LOGGER.critical(f'Unable to read data from the IC {ic_definition.name}')
        return

    # No point in keeping the connection open. Close it early, as the dupico will power down the IC when connection closes.
    ser.close()

    OutFileUtilities.build_output_table_file(outf, ic_definition, ic_data)
    data_array, sha1sum = OutFileUtilities.build_binary_array(ic_definition, ic_data, hiz_high)

    print(f'Read data has SHA1SUM {sha1sum}')

    if outfb:
        OutFileUtilities.build_output_binary_file(outfb, data_array)

    return

def write_command(ser: serial.Serial, deff: str, inf: str) -> None:
    _LOGGER.debug(f'Write command with definition {deff} and input file {inf}')
    ic_definition: ICDefinition = ICLoader.extract_definition_from_file(deff)
    data_list: list[int] = OutFileUtilities.build_data_list_from_file(inf, ic_definition)
    HLBoardUtilities.write_ic(ser, ic_definition, data_list)

def cli() -> int:
    args = _build_argsparser().parse_args()

    # Prepare the logger
    debug_level: int = logging.NOTSET
    if args.verbose > 1:
        debug_level = logging.DEBUG
    elif args.verbose > 0:
        debug_level = logging.INFO
    logging.basicConfig(level=debug_level)
    
    if not args.port:
        DumperUtilities.print_serial_ports()      
        return 1
    else:
        ser_port: serial.Serial | None = None

        try:
            _LOGGER.debug(f'Trying to open serial port {args.port}')
            ser_port = serial.Serial(port = args.port,
                                     baudrate=args.baudrate,
                                     bytesize = 8,
                                     stopbits = 1,
                                     parity = 'N',
                                     timeout = 5.0)

            if not BoardUtilities.check_connection_string(ser_port):
                _LOGGER.critical('Serial port connected, but the board did not respond in time.')
                return -1
            
            _LOGGER.info(f'Board connected @{args.port}, speed:{args.baudrate} ...')
            model: int | None = BoardCommands.get_model(ser_port)
            if model is None:
                _LOGGER.critical('Unable to retrieve model number...')
                return -1
            elif model < MIN_SUPPORTED_MODEL:
                _LOGGER.critical(f'Model {model} is not supported.')
                return -1
            else:
                _LOGGER.info(f'Model {model} detected!')

            match args.subcommand:
                case Subcommands.TEST.value:
                    test_command(ser_port)
                case Subcommands.WRITE.value:
                    write_command(ser_port, args.definition, args.infile)
                case Subcommands.READ.value:
                    read_command(ser_port, args.definition, args.outfile,
                                 args.outfile_binary if args.outfile_binary else None,
                                 args.check_hiz if args.check_hiz else False,
                                 args.hiz_high if args.hiz_high else False)
                case _:
                    _LOGGER.critical(f'Unsupported command {args.subcommand}')


        except Exception as ex:
            _LOGGER.critical(traceback.format_exc())
            return -1

        finally:
            if ser_port and not ser_port.closed:
                _LOGGER.debug('Closing the serial port.')
                ser_port.close()

        _LOGGER.info('Quitting.')
        return 1 
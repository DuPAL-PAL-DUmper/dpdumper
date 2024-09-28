"""Frontend module"""

import argparse
import traceback
import logging
import time
import math

import serial

from enum import Enum

from dupicolib.hardware_board_commands import HardwareBoardCommands
from dupicolib.board_command_class_factory import BoardCommandClassFactory
from dupicolib.board_utilities import BoardUtilities
from dupicolib.board_fw_version import FwVersionTools, FWVersionDict

from dpdumperlib.ic.ic_loader import ICLoader
from dpdumperlib.ic.ic_definition import ICDefinition
import dpdumperlib.io.file_utils as FileUtils

from dpdumper import __name__, __version__
from dpdumper.dumper_utilities import DumperUtilities
from dpdumper.hl_board_utilities import HLBoardUtilities, DataElement

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
        description='A tool to dump combinatorial ICs with a dupico board'
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
    parser_read.add_argument('-obz', '--outfile_binary_z',
                             type=str,
                             metavar='binary output file for the Hi-Z mask',
                             help='Binary output file that will contain the Hi-Z mask for every data entry')
    parser_read.add_argument('--check_hiz',
                             action='store_true',
                             default=False,
                             help='Check if data pins are Hi-Z or not. Slows down the read.')    
    parser_read.add_argument('--hiz_high',
                             action='store_true',
                             default=False,
                             help='The binary output will be saved with hi-z bits set to 1')
    parser_read.add_argument('--skip_note',
                             action='store_true',
                             default=False,
                             help='If set, skip printing adapter notes and associated delays')
    parser_read.add_argument('-rb', '--reverse_byte_order',
                             action='store_true',
                             default=False,
                             help='If set, the output binary file will be written in Little Endian format')

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
    parser_write.add_argument('-ss', '--start_skip',
                              type=int,
                              default=0,
                              metavar='start entries to skip',
                              help='Number of entries to skip at start of the write')
    parser_write.add_argument('-es', '--end_skip',
                              type=int,
                              default=0,
                              metavar='ending entries to skip',
                              help='Number of entries to skip at end of the write')
    parser_write.add_argument('--skip_note',
                             action='store_true',
                             default=False,
                             help='If set, skip printing adapter notes and associated delays')
    parser_read.add_argument('-rb', '--reverse_byte_order',
                             action='store_true',
                             default=False,
                             help='If set, the input file will be read in Little Endian format')


    return parser

def print_note(note: str, delay: int = 5) -> None:
    print('-' * 10)
    print(note.strip())
    print('-' * 10)

    for i in range(delay, 0, -1):
        print(f'To cancel, press CTRL-C within {i} seconds'.ljust(80, ' '), end='\r')
        time.sleep(1)
    print(' ' * 80, end='\r')

def test_command(ser: serial.Serial, cmd_class: type[HardwareBoardCommands]) -> None:
    delay: int = 5

    print('Make sure the ZIF socket is empty before starting the test!')

    for i in range(delay, 0, -1):
        print(f'To cancel, press CTRL-C within {i} seconds'.ljust(80, ' '), end='\r')
        time.sleep(1)
    print(' ' * 80, end='\r')

    test_result: bool | None = cmd_class.test_board(ser)

    if test_result is None:
        print('Unable to get a proper response.')
    else:
        print(f'Test result is {"OK" if test_result else "BAD"}!')

def read_command(ser: serial.Serial, cmd_class: type[HardwareBoardCommands], ic_definition: ICDefinition, outf: str, outfb: str | None = None, outfbz: str | None = None, check_hiz: bool = False, hiz_high: bool = False, skip_note: bool = False, reverse_byte_order: bool = False) -> None:
    _LOGGER.debug(f'Read command with definition {ic_definition.name}, output table {outf}, output binary {outfb}, output Hi-Z binary {outfbz}, check Hi-Z {check_hiz}, treat Hi-Z as high {hiz_high}')

    if outfbz and not check_hiz:
        _LOGGER.warning(f'Output for Hi-Z binary {outfbz} was requested, but check for Hi-Z was disabled, we are not going to write the file!')
        outfbz = None

    print(f'Reading {ic_definition.name}')
    if not skip_note and ic_definition.adapter_notes and bool(ic_definition.adapter_notes.strip()):
        print_note(ic_definition.adapter_notes)

    start_time: float = time.time()
    ic_data: list[DataElement] | None = HLBoardUtilities.read_ic(ser, cmd_class, ic_definition, check_hiz)
    end_time: float = time.time()

    if ic_data is None:
        _LOGGER.critical(f'Unable to read data from {ic_definition.name}')
        return

    # No point in keeping the connection open. Close it early, as the dupico will power down the IC when connection closes.
    ser.close()

    print(f'Reading took {math.ceil(end_time - start_time)} seconds.')

    OutFileUtilities.build_output_table_file(outf, ic_definition, ic_data)
    data_array, hiz_array, sha1sum = OutFileUtilities.build_binary_array(ic_definition, ic_data, hiz_high, reverse_byte_order)

    print(f'Data has SHA1SUM {sha1sum}')

    if outfb:
        OutFileUtilities.build_output_binary_file(outfb, data_array)

    if outfbz:
        OutFileUtilities.build_output_binary_file(outfbz, hiz_array)

    return

def write_command(ser: serial.Serial, cmd_class: type[HardwareBoardCommands], ic_definition: ICDefinition, inf: str, begin_skip: int = 0, end_skip: int = 0, skip_note: bool = False, reverse_byte_order: bool = False) -> None:
    _LOGGER.debug(f'Write command with definition {ic_definition.name} and input file {inf}')

    print(f'Writing {ic_definition.name}')
    
    if begin_skip or end_skip:
        print(f'Skipping {begin_skip} entries at the start, and {end_skip} at the end.')

    if not skip_note and ic_definition.adapter_notes and bool(ic_definition.adapter_notes.strip()):
        print_note(ic_definition.adapter_notes)

    bytes_per_entry: int = -(len(ic_definition.data) // -8)
    data_list: list[int] = FileUtils.load_file_data(inf, bytes_per_entry, reverse_byte_order)
    
    start_time: float = time.time()
    HLBoardUtilities.write_ic(ser, cmd_class, ic_definition, data_list, begin_skip, end_skip)
    end_time: float = time.time()

    print(f'Writing took {math.ceil(end_time - start_time)} seconds.')

def cli() -> int:
    args = _build_argsparser().parse_args()

    # Prepare the logger
    debug_level: int = logging.ERROR
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

            if not BoardUtilities.initialize_connection(ser_port):
                _LOGGER.critical('Serial port connected, but the board did not respond in time.')
                return -1
            
            _LOGGER.info(f'Board connected @{args.port}, speed:{args.baudrate} ...')
            model: int | None = HardwareBoardCommands.get_model(ser_port)
            if model is None:
                _LOGGER.critical('Unable to retrieve model number...')
                return -1
            elif model < MIN_SUPPORTED_MODEL:
                _LOGGER.critical(f'Model {model} is not supported.')
                return -1
            else:
                _LOGGER.info(f'Model {model} detected!')

            fw_version: str | None = HardwareBoardCommands.get_version(ser_port)
            fw_version_dict: FWVersionDict
            if fw_version is None:
                _LOGGER.critical('Unable to retrieve firmware version...')
                return -1
            else:
                fw_version_dict = FwVersionTools.parse(fw_version) # Check that the version is formatted correctly
                _LOGGER.info(f'Firmware version on board is "{fw_version}"')

            # Now we have enough information to obtain the class that handles commands specific for this board
            command_class: type[HardwareBoardCommands] = BoardCommandClassFactory.get_command_class(model, fw_version_dict) # type: ignore

            # Load and check IC definition requirements
            ic_definition: ICDefinition
            if hasattr(args, 'definition') and args.definition is not None:
                ic_definition = ICLoader.extract_definition_from_file(args.definition)
                
                if ic_definition.hw_model > model:
                    raise ValueError(f'Current hardware model {model} does not satisfy requirement {ic_definition.hw_model}')

            match args.subcommand:
                case Subcommands.TEST.value:
                    test_command(ser_port, command_class)
                case Subcommands.WRITE.value:
                    write_command(ser_port, command_class, ic_definition, args.infile, 
                                  args.start_skip,
                                  args.end_skip,
                                  args.skip_note,
                                  args.reverse_byte_order)
                case Subcommands.READ.value:
                    read_command(ser_port, command_class, ic_definition, args.outfile,
                                 args.outfile_binary if args.outfile_binary else None,
                                 args.outfile_binary_z if args.outfile_binary_z else None,
                                 args.check_hiz,
                                 args.hiz_high,
                                 args.skip_note,
                                 args.reverse_byte_order)
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
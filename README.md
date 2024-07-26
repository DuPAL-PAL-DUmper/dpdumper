# dpdumper

## DISCLAIMER

Any use of this project is **under your own responsibility**.

Please, **do not come to me asking for hand-holding** using or building this: my time is limited.

## Introduction

This is a tool to interface your computer with the DuPAL V3 ("dupico") board and dump purely combinatorial ICs (mainly ROMs).

It takes a description of the IC to read in TOML format and outputs a human readable table containing the state of every data pin ('1', '0' or 'Z') for every address combination, and, optionally, a binary file representing the same data (with the option to set pins in Hi-Z state to either 1 or 0).


## Command line

```
usage: dpdumper [-h] [-v] [--version] -p [serial port] [-b Baud rate] {test,read,write} ...

A tool for fiddling with a dupico board

positional arguments:
  {test,read,write}     supported subcommands
    test                Execute the selftest routine of the dupico board
    read                Read data from an IC
    write               Write the content of a file into a supported (and writable) IC

options:
  -h, --help            show this help message and exit
  -v, --verbose
  --version             show program's version number and exit
  -p [serial port], --port [serial port]
                        Serial port associated with the board
  -b Baud rate, --baudrate Baud rate
                        Speed at which to the serial port is opened
```

This tool supports 3 commands: `test`, `read` and `write`. All the commands require passing the `-p` parameter to specify which com port the dupico is associated to. If you pass `-p` without any parameter, the tool will print a list of available ports for you to choose from:

```
>dpdumper -p
Available serial ports:
        COM4 - USB Serial Device (COM4)
        COM3 - USB Serial Device (COM3)
```

### Test
This command simply asks the dupico to run the internal self-test procedure, and relays the result:

```
>dpdumper -p com4 test
Testing the board, make sure the ZIF socket is empty!
Test result is OK!
```

**❗Make sure the ZIF socket is empty, or the test will fail!**

### Read
```
usage: dpdumper read [-h] -d definition file -o output file [-ob binary output file] [--check_hiz] [--hiz_high]

options:
  -h, --help            show this help message and exit
  -d definition file, --definition definition file
                        Path to the file containing the definition of the IC to be read
  -o output file, --outfile output file
                        Output file that will contain the data read from the IC in ASCII human-readable format
  -ob binary output file, --outfile_binary binary output file
                        Binary output file that will contain the data read from the IC
  --check_hiz           Check if data pins are Hi-Z or not. Slows down the read.
  --hiz_high            The binary output will be saved with hi-z bits set to 1
```

The definition file is in TOML format, and described later in this document.

If `--check_hiz` is omitted, the dumper will execute simple reads from the IC, without trying to pull the data lines both high or low and check if any pin is in Hi-Z.
This means that pins that are actually Hi-Z will be detected as low, but also that half the writes to the dupico are required, and thus the read is much faster.

`--hiz_high`: By default, if hi-z is checked and a binary file is to be written, hi-z pins will be considered low when written. With this flag, they will be written as a high bit.

### Write
⚠️ Writing is supported only by some ICs and is, as of now, untested.

## IC Definition format
**TODO**
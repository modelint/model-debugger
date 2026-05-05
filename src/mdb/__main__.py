"""
Blueprint Model Debugger

"""
# System
import logging
import logging.config
import sys
import argparse
from pathlib import Path
import atexit

# MDB
from mdb.session import Session
from mdb import version

_logpath = Path("mdb.log")
_progname = 'Blueprint Model Debugger'

def clean_up():
    """Normal and exception exit activities"""
    _logpath.unlink(missing_ok=True)

def get_logger():
    """Initiate the logger"""
    log_conf_path = Path(__file__).parent / 'log.conf'  # Logging configuration is in this file
    logging.config.fileConfig(fname=log_conf_path, disable_existing_loggers=False)
    return logging.getLogger(__name__)  # Create a logger for this module


# Configure the expected parameters and actions for the argparse module
def parse(cl_input):
    parser = argparse.ArgumentParser(description=_progname)
    parser.add_argument('-s', '--system', action='store',
                        help='Name of the metamodel TclRAL database *.ral file populated with one or more domains')
    parser.add_argument('-p', '--playground', action='store',
                        help='Name of the context directory specifying the initialized domain dbs and a *.sip file')
    parser.add_argument('-x', '--scenario', action='store',
                        help='Name of the scenario *.yaml file to run against the populated system')
    parser.add_argument('-L', '--log', action='store_true',
                        help='Generate a diagnostic log file')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Verbose messages')
    parser.add_argument('-V', '--version', action='store_true',
                        help='Print the current version of the model execution app')
    return parser.parse_args(cl_input)


def main():
    # Start logging
    logger = get_logger()
    msg = f'{_progname} version: {version}\n'
    logger.info(msg)

    # Parse the command line args
    args = parse(sys.argv[1:])

    if args.version:
        # Just print the version and quit
        print(f'{_progname} version: {version}')
        sys.exit(0)

    if not args.log:
        # If no log file is requested, remove the log file before termination
        atexit.register(clean_up)

    print(f"\n{msg}")
    if args.verbose:
        print("\nVerbose mode set\n")

    # All pathnames are optional since the user can specify them in the debug session
    session = Session()  # Create the singleton instance
    session.initialize(
        system_path=Path(args.system) if args.system else None,
        playground_name=args.playground if args.playground else None,
        scenario_name=args.scenario if args.scenario else None,
        verbose=args.verbose)

    logger.info("No problemo")  # We didn't die on an exception, basically
    if args.verbose:
        print("\nNo problemo")


if __name__ == "__main__":
    main()

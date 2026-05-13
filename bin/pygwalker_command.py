"""
PyGWalker is a python library that simplify your Jupyter Notebook data analysis 
and data visualization workflow, by turning your pandas dataframe into an interactive 
user interface for visual exploration.

Updated on Tue November 11 15:15:48 2024

@author: Kanaries

"""

import argparse
import sys
from pathlib import Path
from typing import Tuple
from pygwalker.services.kanaries_cli_login import kanaries_login
from pygwalker.services.config import (
    reset_all_config,
    set_config,
    get_config_params_help,
    reset_config,
    get_all_config_str,
    CONFIG_PATH
)


parser = argparse.ArgumentParser(
    prog="pygwalker",
    description='pygwalker: turn your data into an interactive UI for data exploration \
    and visualization'
)
subparsers = parser.add_subparsers(dest='command')

# config command
config_parser = subparsers.add_parser(
    'config',
    help=f'Modify configuration file. (default: {CONFIG_PATH})',
    add_help=True,
    description=f'Modify configuration file. \
    (default: {CONFIG_PATH}) \n' + get_config_params_help(),
    formatter_class=argparse.RawTextHelpFormatter
)
config_parser.add_argument(
    '--set',
    nargs='*',
    metavar='key=value',
    help='Set configuration. e.g. "pygwalker config --set privacy=update-only"'
)
config_parser.add_argument(
    '--reset',
    nargs='*',
    metavar='key',
    help='Reset user configuration and use default values instead. \
    e.g. "pygwalker config --reset privacy"'
)
config_parser.add_argument(
    '--reset-all',
    action='store_true',
    help='Reset all user configuration and use default values instead. \
    e.g. "pygwalker config --reset-all"'
)
config_parser.add_argument(
    '--list',
    action='store_true',
    help='List current used configuration.'
)

# login command
login_parser = subparsers.add_parser(
    'login',
    help="set up your kanaries token via kanaries website authorization.",
    add_help=True,
    description="set up your kanaries token via kanaries website authorization.",
    formatter_class=argparse.RawTextHelpFormatter
)

# verify command
verify_parser = subparsers.add_parser(
    'verify',
    help='Run unified verification suite (frontend build, static check, unit tests, regression tests)',
    add_help=True,
    description='Run unified verification suite for PyGWalker',
    formatter_class=argparse.RawTextHelpFormatter
)
verify_parser.add_argument(
    '--skip',
    nargs='+',
    default=[],
    help='Stages to skip (e.g., "Frontend Build" "Static Architecture Check")'
)
verify_parser.add_argument(
    '--no-stop',
    action='store_true',
    help='Continue running even if a stage fails'
)
verify_parser.add_argument(
    '--verbose', '-v',
    action='store_true',
    help='Show verbose output'
)
verify_parser.add_argument(
    '--quick',
    action='store_true',
    help='Quick mode: skip frontend build and run only essential tests'
)


def command_set_config(value: Tuple[str]):
    """
    setup command configuration.

    Parameters
    ----------
    value : String tuple
        tuples of string values.

    """
    config = dict(
        item.split('=')
        for item in value
    )
    set_config(config)


def command_reset_config(value: Tuple[str]):
    """
    reset command configuration.

    Parameters
    ----------
    value : String tuple
        tuples of string values.

    """
    reset_config(value)


def command_reset_all_config(_):
    """
    reset all command configuration.

    """
    reset_all_config()


def command_list_config(_):
    """
    Prints all command configuration.

    """
    config = get_all_config_str()
    print("Current configuration:")
    print(config)


def command_verify(args):
    """
    Run unified verification suite.

    Parameters
    ----------
    args : argparse.Namespace
        Command line arguments from verify parser.

    """
    from scripts.verify import VerifyRunner, VerifyConfig

    project_root = Path(__file__).resolve().parent.parent

    skip_stages = list(args.skip)
    if args.quick:
        skip_stages.extend(["Frontend Build"])

    config = VerifyConfig(
        project_root=project_root,
        app_dir=project_root / "app",
        tests_dir=project_root / "tests",
        skip_stages=skip_stages,
        verbose=args.verbose,
        stop_on_failure=not args.no_stop
    )

    runner = VerifyRunner(config)
    success = runner.run()

    sys.exit(0 if success else 1)


def main():
    """
    Entry point of the program. It acts like programcontroller and interface 
    with program users. It handles commands from a command line and redirect 
    to the disignated function or task.


    Parameters
    ----------
    None

    """
    conifg_command_list = [
        ("set", command_set_config),
        ("reset", command_reset_config),
        ("reset_all", command_reset_all_config),
        ("list", command_list_config)
    ]

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    if args.command == 'config':
        for action, action_func in conifg_command_list:
            value = getattr(args, action)
            if value:
                action_func(value)
                return
        config_parser.print_help()
        return

    if args.command == 'login':
        kanaries_login()
        return

    if args.command == 'verify':
        command_verify(args)
        return

    parser.print_help()


if __name__ == '__main__':
    main()

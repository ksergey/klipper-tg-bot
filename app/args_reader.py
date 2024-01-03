__all__ = ("args")

import argparse
import logging

def create_parser():
    parser = argparse.ArgumentParser(description='klipper telegram bot')
    parser.add_argument(
        '-c', '--config',
        help='path to config file',
        dest='config',
        metavar='PATH',
        required=True
    )
    parser.add_argument(
        '--log-file',
        help='path to output log file',
        dest='logfile',
        metavar='PATH',
        default=None
    )
    parser.add_argument(
        '-d', '--debug',
        help='print lots of debug data',
        dest='loglevel',
        action='store_const',
        const=logging.DEBUG,
        default=logging.INFO
    )

    return parser

args = create_parser().parse_args()

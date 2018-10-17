import nacl.signing
import nacl.encoding
import sys
import os.path
import argparse
import json
import logging


def keygen():
    return None


def rename():
    return None


def setup():
    return None


parser = argparse.ArgumentParser(description='Create mailmap files for the mailmapper system')
parser.add_argument('v', 'verbose', help='Show debugging information', action='store_true')
subparsers = parser.add_subparsers(help='Subcommand')

parser_keygen = subparsers.add_parser('keygen', help='Generate new key')

parser_rename = subparsers.add_parser('rename', help='Change name and email')

parser_setup = subparsers.add_parser('setup', help='Configure git to use mailmap')

args = parser.parse_args()

if args.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig()

# Find and create the config directory
config_dir = ""
if 'MAILMAPPER_DIR' in os.environ:
    config_dir = os.environ['MAILMAPPER_FILE']
elif 'XDG_CONFIG_DIR' in os.environ:
    config_dir = os.path.join(os.environ['XDG_CONFIG_DIR'], 'mailmapper')
elif 'HOME' in os.environ:
    config_dir = os.path.join(os.environ['HOME'], '.config', 'mailmapper')
else:
    logging.fatal('Could not find configuration directory. Please set HOME, XDG_CONFIG_DIR, or MAILMAPPER_DIR')
    exit(1)

logging.debug(f'Config directory is {config_dir}')

if not os.path.exists(config_dir):
    logging.info('Config directory does not exist, creating')
    os.makedirs(config_dir)
elif not os.path.isdir(config_dir):
    logging.fatal('Config directory is not a directory')
    exit(1)

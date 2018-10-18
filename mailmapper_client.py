#!/usr/bin/env python3
import typing

import nacl.signing
import nacl.encoding
import nacl.exceptions
import glob
import os.path
import argparse
import json
import logging
import datetime


def get_config_dir() -> str:
    config_dir = ''
    if 'MAILMAPPER_DIR' in os.environ:
        config_dir = os.environ['MAILMAPPER_FILE']
    elif 'XDG_CONFIG_DIR' in os.environ:
        config_dir = os.path.join(os.environ['XDG_CONFIG_DIR'], 'mailmapper')
    elif 'HOME' in os.environ:
        config_dir = os.path.join(os.environ['HOME'], '.config', 'mailmapper')
    else:
        logging.fatal('Could not find configuration directory. Please set HOME, XDG_CONFIG_DIR, or MAILMAPPER_DIR')
        exit(1)

    if not os.path.exists(config_dir):
        logging.info('Config directory does not exist, creating')
        os.makedirs(config_dir, exist_ok=True)
    elif not os.path.isdir(config_dir):
        logging.fatal('Config directory is not a directory')
        exit(1)

    logging.debug(f'Config directory is {config_dir}')

    return config_dir


def load_privkey(path=None) -> nacl.signing.SigningKey:
    if path is None:
        path = os.path.join(get_config_dir(), 'privkey')
    if not os.path.exists(path):
        logging.fatal("Unable to load key. Make sure you generated one with mailmapper keygen")
        exit(1)

    key_data = open(path, 'rb').read()
    return nacl.signing.SigningKey(key_data)


def get_pubkey(privkey: nacl.signing.SigningKey) -> str:
    return privkey.verify_key.encode(encoder=nacl.encoding.Base32Encoder).decode('ascii')


def validate_email(email: str) -> bool:
    # Validating emails is hard because quotes and lots of special characters are valid
    return email.count('@') >= 1


def format_line(pubkey: str, content: dict) -> str:
    key_email = content['prefix'] + pubkey + '@' + content['domain']
    return f"{content['name']} <{content['email']}> {pubkey} <{key_email}>"


def keygen(args: argparse.Namespace) -> int:
    config_dir = get_config_dir()
    key_file = os.path.join(config_dir, 'privkey')
    if os.path.exists(key_file):
        logging.warning('Key already exists')
        if not args.force:
            logging.fatal('Key already exists and force not set. Not replacing')
            return 1
        else:
            logging.debug('Force set, overwriting key')

    key = nacl.signing.SigningKey.generate()
    f = open(key_file, 'wb')
    f.write(key.encode())
    f.close()

    logging.debug('done configuring key')


def rename(args: argparse.Namespace) -> int:
    privkey = load_privkey()
    pubkey = get_pubkey(privkey).rstrip('=')
    if args.email is not None:
        email = args.email
    else:
        email = input('Enter your email: ')

    if not validate_email(email):
        logging.fatal('Invalid email.')
        return 1

    if args.name is not None:
        name = args.name
    else:
        name = input('Enter your name: ')

    data = {
        'name': name,
        'email': email,
        'prefix': args.prefix,
        'domain': args.domain,
        'date': datetime.datetime.utcnow().isoformat(timespec='seconds')
    }
    raw_data = json.dumps(data).encode('utf8')
    signed = privkey.sign(raw_data)

    os.makedirs(os.path.join(get_config_dir(), 'data'), exist_ok=True)
    outfile = open(os.path.join(get_config_dir(), 'data', pubkey + '.signed'), 'wb')
    outfile.write(signed)
    outfile.close()

    return 0


def sync(args: argparse.Namespace) -> int:
    config_dir = get_config_dir()

    mailmap = open(os.path.join(config_dir, 'mailmap'), 'w')

    for fname in glob.iglob(os.path.join(config_dir, 'data', '*.signed'), recursive=True):
        basename = fname.split(os.sep)[-1].split('.')[0]
        logging.info(f'found {basename}')

        raw_file = open(fname, 'rb')
        ciphertext = raw_file.read()
        raw_file.close()

        key = nacl.signing.VerifyKey(basename + '====', encoder=nacl.encoding.Base32Encoder)

        try:
            verified = key.verify(ciphertext)
            logging.info(f'Signature verification succeeded for {basename}')
            plaintext = json.loads(verified.decode('utf8'))
            mailmap.write(format_line(basename, plaintext) + '\n')

        except nacl.exceptions.BadSignatureError:
            logging.warning(f'Signature verification failed for {basename}')
            continue
        except json.JSONDecodeError:
            logging.warning(f'JSON decode failed for {basename}')
        except UnicodeDecodeError:
            logging.warning(f'Could not decode {basename} as utf8')

    mailmap.close()
    return 0


parser = argparse.ArgumentParser(description='Create mailmap files for the mailmapper system')
parser.add_argument('-v', '--verbose', help='Show debugging information', action='store_true')
subparsers = parser.add_subparsers(help='Subcommand', dest='command')
subparsers.required = True

parser_keygen = subparsers.add_parser('keygen', help='Generate new key')
parser_keygen.add_argument('-f', '--force', action='store_true',
                           help='Force regeneration of an existing key, deleting the previous one')
parser_keygen.set_defaults(func=keygen)

parser_rename = subparsers.add_parser('rename', help='Change name and email')
parser_rename.add_argument('-d', '--domain', help='Domain to use in the raw email', default='mailmap.example')
parser_rename.add_argument('-p', '--prefix', help='Prefix to use in the raw email, such as "git+"', default='')
parser_rename.add_argument('-e', '--email', help='Your email address')
parser_rename.add_argument('-n', '--name', help='Your name')
parser_rename.set_defaults(func=rename)

parser_sync = subparsers.add_parser('sync', help='Update the mailmap file')
# TODO: add actual syncing, not just parsing
parser_sync.set_defaults(func=sync)

parsed_args = parser.parse_args()

if parsed_args.verbose:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig()

exit(parsed_args.func(parsed_args))

import subprocess
import argparse
import sys
import os

from funcUtil import fetchSqlScript, createSqlFile, openSqlFile
from ClientTemplater.Templater import Templater
from Saver import Saver


def find(args):
    try:
        sqlFile = fetchSqlScript(args.nFindFile, args.nCreateFile)
        print("\nfind done!")
    except FileNotFoundError:
        pass
    except IOError:
        pass
    else:
        if args.open:
            openSqlFile(sqlFile)


def make(args):
    templater = Templater(args.host, args.port, args.name)
    try:
        sqlFile = templater.makeSqlScript(args.templates, args.filter)
        print("\nmake done!")
    except IOError as e:
        print(f'Error: create sql file {e}')
    else:
        if args.open:
            openSqlFile(sqlFile)


def save(args):
    try:
        Saver().save(args.name)
    except Exception as e:
        print(e)


parser = argparse.ArgumentParser()
subparser = parser.add_subparsers()

find_parser = subparser.add_parser('find')
find_parser.add_argument('nFindFile', help='file name of find sqlScript')
find_parser.add_argument('nCreateFile', help='file name for new sqlFile')
find_parser.add_argument(
    '-o', '--open', action='store_true', help='is true open in MMSSQL')
find_parser.set_defaults(func=find)

make_parser = subparser.add_parser('make')
make_parser.add_argument('name', help='name for make sqlFile')
make_parser.add_argument('templates', help='template body for make sqlFile')
make_parser.add_argument('-f', '--filter', help='set filter for all template')
make_parser.add_argument(
    '-o', '--open', action='store_true', help='is true open in MMSSQL')
make_parser.add_argument(
    '--host', '--h', default='127.0.0.1', help='Set IP for TempleterServer')
make_parser.add_argument('--port', '--p', default='8080')
make_parser.set_defaults(func=make)

save_parser = subparser.add_parser('save')
save_parser.add_argument('name', help='name for save sqlFile')
save_parser.set_defaults(func=save)

if __name__ == '__main__':
    args = parser.parse_args()
    args.func(args)

#!/usr/bin/python
'''
Created on May 20, 2016

@author:
'''
import sys
import os
import json
import eeprom

#import logging as log
from argparse import ArgumentParser


class SysBoard(object):
    '''
    Main system definition
    '''
    def __init__(self, json_data):
        '''
        Constructor
        '''
        self.eeprom = eeprom.EepromBin("syseeprom.bin")
        # Init EEPROM programmer
        self.eepprog = eeprom.JsonEepromProg(self.eeprom,json_data['SysEeprom'])


def main(board, argv=None):
    '''Command line options.'''

    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    eepprog = board.eepprog

    try:
        # Setup argument parser
        parser = ArgumentParser(prog=sys.argv[0])
        subparsers = parser.add_subparsers(help='help for subcommand', dest='subcommand')

        parser_show = subparsers.add_parser('show', help='Display the device info')
        parser_dump = subparsers.add_parser('dump', help='Dump the binary content')
        parser_json = subparsers.add_parser('json', help='Output JSON format')
        parser_init = subparsers.add_parser('init', help='Initialize the device info')
        parser_erase = subparsers.add_parser('erase', help='Erase the device info')
        parser_update = subparsers.add_parser('update', help='Update the device info')
        parser_update.add_argument('fields', type=str, metavar='<field>=<value>', nargs='+',
                                    help='Update the specified field. ')
        parser_list = subparsers.add_parser('field', help='List the available fields. ')

        if len(sys.argv) == 1:
            parser.print_help()
            return 1

        args = parser.parse_args()
        
        if args.subcommand == 'show': # eepprog show
            eepprog.eep_dev.reload()
            for key in sorted(eepprog.fields.keys(), key = lambda name: eepprog.fields[name].offset):
                print '%-16s: %s' % (eepprog.fields[key].descr, eepprog.get_field(key))

        elif args.subcommand == 'dump': # eepprog dump
            eepprog.eep_dev.reload()
            print eepprog.eep_dev.dump()

        elif args.subcommand == 'erase': # eepprog erase
            if operation_confirm() == True:
                eepprog.erase_all()
                eepprog.eep_dev.save()

        elif args.subcommand == 'init': # eepprog init
            if operation_confirm() == True:
                eepprog.init_default()
                eepprog.eep_dev.save()

        elif args.subcommand == 'json': # eepprog json
            eepprog.eep_dev.reload()
            print eepprog.toJSON()

        elif args.subcommand == 'field': # eepprog field
            print '\nAvailable fields are: ' +', '.join(eepprog.fields.keys())

        elif args.subcommand == 'update': # eepprog update
            # parse <field>=<value>
            eepprog.eep_dev.reload()
            fields = []
            for f in args.fields:
                pair = f.split('=')
                if len(pair) != 2:
                    parser_update.print_help()
                    return 2
                elif pair[0] not in eepprog.fields:
                    print 'Available fields are: ' +', '.join(eepprog.fields.keys())
                    return 2
                else: fields.append(pair)
            for f in fields:
                if eepprog.fields[f[0]] != None:
                    eepprog.set_field(f[0],f[1])
            eepprog.eep_dev.save()

        else:
            parser.print_help()
        print ''
    except Exception, e:
        indent = len(parser.prog) * " "
        sys.stderr.write(parser.prog + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help\n")
        return 2

def operation_confirm():
    s = raw_input('Are you sure to do this? (y/N): ')
    if s.lower() == 'y':
        return True
    return False

# Entry point of the script
if __name__ == '__main__':
    try:
        f=open('eeprom.json') # EEPROM format
        j_data = json.load(f)
        f.close()
    except Exception, e:
        print "File eeprom.json is not found."
        exit(1)
    board = SysBoard(j_data)
    sys.exit(main(board))


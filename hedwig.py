#!/usr/bin/env python3
# coding=utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
Hedwig is a CMS monitor.
"""
import os
import sys
import json
import logging
import argparse

from modules import *


class HedwigCommandLine(object):
    """
    Command-line interface for Hedwig.
    """
    HOME = os.path.dirname(os.path.abspath(__file__))
    VERSION = 0.3

    def parse_args(self):
        parser = argparse.ArgumentParser(
            description='Hedwig Runtime',
            prog=__file__,
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            epilog='The exit status is 0 for non-failures and -1 for failures.'
        )

        m = parser.add_argument_group('mandatory arguments')
        m.add_argument('-project', metavar='str', type=str, required=True, help='project name')

        o = parser.add_argument_group('optional arguments')
        o.add_argument('-h', '-help', '--help', action='help', help=argparse.SUPPRESS)
        o.add_argument('-logging', metavar='#', type=int, choices=list(range(1, 6, 1)),
                       default=2,
                       help='verbosity level of logging')
        o.add_argument('-repositories', metavar='file', type=argparse.FileType(),
                       default=os.path.relpath(os.path.join(self.HOME, 'repositories.json')),
                       help='repository definitions')
        o.add_argument('-conf', metavar='path', type=argparse.FileType(),
                       default=os.path.relpath(os.path.join(self.HOME, 'hedwig.json')),
                       help='Hedwig configuration')
        o.add_argument('-keywords', metavar='path', type=argparse.FileType(),
                       default=os.path.relpath(os.path.join(self.HOME, "keywords", 'default.json')),
                       help='keyword expressions')
        o.add_argument('-version', action='version', version='%(prog)s 1.0', help=argparse.SUPPRESS)

        return parser.parse_args()

    def main(self):
        args = self.parse_args()
        logging.basicConfig(format='[Hedwig] %(asctime)s %(levelname)s: %(message)s',
                            level=args.logging * 10,
                            datefmt='%Y-%m-%d %H:%M:%S')

        if args.repositories:
            try:
                repositories = json.loads(args.repositories.read())
            except ValueError as err:
                logging.error('Unable to parse %s: %s', args.repositories.name)
                return 1

            if args.project not in repositories:
                logging.error('Project "{}" is not defined in {}.'.format(args.project, args.repositories.name))
                return 1

            repository = repositories[args.project]

        if args.conf:
            try:
                conf = json.loads(args.conf.read())
            except ValueError as err:
                logging.error('Unable to parse %s: %s', args.conf.name)
                return 1
        conf = conf[repository['type']]

        if args.keywords:
            try:
                keywords = json.loads(args.keywords.read())
            except ValueError as err:
                logging.error('Unable to parse %s: %s', args.keywords.name)
                return 1

        module_name = repository['type']
        if module_name not in globals():
            logging.error('Repository system {} currently not supported.', module_name)
            return 1

        module = globals()[module_name]
        try:
            git = module.GitHubCommitMonitor(repository, keywords, 2)
            git.configure(conf["token"])
            git.start()
        except KeyboardInterrupt:
            raise Exception('Caught SIGINT, aborting.')
        except Exception as e:
            logging.error(e)
        finally:
            logging.info('Stopping Hedwig.')


if __name__ == '__main__':
    sys.exit(HedwigCommandLine().main())

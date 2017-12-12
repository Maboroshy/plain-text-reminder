#!/bin/env python3

import os
import logging
import argparse

import cli
import model
import config
import r_scheduler


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-s', '--scan', action='store', dest='scan_path', required=False,
                            help="Path of directory or file to scan")
    arg_parser.add_argument('-c', '--config', action='store', dest='config_path', required=False,
                            default='reminder.cfg', help="Path to config file")
    arg_parser.add_argument('-v', action='count', dest='log_level', required=False,
                            help="Debug logging verbosity")
    arg_parser.add_argument('-d', '--demo', action='store_true', dest='run_demo', required=False,
                            help="Run reminder tag parsing interactive demo")
    args = arg_parser.parse_args()

    cfg = config.Cfg(args.config_path)

    if args.run_demo:
        cli.ParseDemo(cfg).run()
        exit(0)

    if not args.scan_path:
        if cfg.scan_path:
            args.scan_path = cfg.scan_path
        else:
            print('Path of folder to scan is not set.',
                  '\nProvide path by running "run.py -s path" or put it into reminder.cfg "scan_path".')
            exit(1)

    if not os.path.exists(args.scan_path):
        print('Can\'t find folder or file at provided path.')
        exit(1)

    if args.log_level:
        if args.log_level == 1:
            logging.basicConfig(evel=logging.INFO, format='%(message)s')
        elif args.log_level > 1:
            logging.basicConfig(level=logging.DEBUG,
                                format='%(asctime)s,%(msecs)03d - %(funcName)-18s - %(message)s',
                                datefmt='%X')

    scheduler = r_scheduler.RScheduler()
    interface = cli.CliInterface()

    model.run(args.scan_path, cfg)
    scheduler.run()
    interface.run()

import argparse
import yaml
from collections import OrderedDict

def load_commands(cli_file):
    with open(cli_file) as f:
        return yaml.safe_load(f)

def create_parser_from_yaml(command):
    parser = argparse.ArgumentParser(command['help'])
    for arg in command['args']:
        name = arg.pop('name')
        if 'required' in arg and arg.pop('required'):
            names = [name]
        else:
            names = [f"-{name}",f"--{name}"]
        if 'type' in arg:
            arg['type'] =  eval(arg['type'])
        parser.add_argument(*names, **arg)

    return parser

def general_parser(commands):
    print('Welcome to the MMC command line interface.')
    print('\nBelow is a list of available commands with their associated subcommands.\n')
    commands = OrderedDict(sorted(commands.items()))
    for k,v in commands.items():
        print(f'{k:>10}')
        v = OrderedDict(sorted(v.items()))
        for k,v in v.items():
            print(f"{'|->':>10} {k:<15} ({v['help']})")
        print()

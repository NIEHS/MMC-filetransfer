import argparse
import yaml

def load_commands(cli_file):
    with open(cli_file) as f:
        return yaml.safe_load(f)

def create_parser_from_yaml(command):
    parser = argparse.ArgumentParser(command['help'])
    for arg in command['args']:
        name = f"-{arg.pop('name')}"
        if 'type' in arg:
            arg['type'] =  eval(arg['type'])
        parser.add_argument(name, **arg)

    return parser

def general_parser(commands):
    print('Welcome to the MMC command line interface.')
    print('\nBelow is a list of available commands with their associated subcommands.\n')
    for k,v in commands.items():
        print(f'{k:>10}')
        for k,v in v.items():
            print(f"{'|->':>10} {k:<15} ({v['help']})")

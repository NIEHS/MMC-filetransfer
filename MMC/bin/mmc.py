import logging
from MMC import settings
import sys
import MMC.cli.cli as cli
import importlib
import asyncio

logger = logging.getLogger(__name__)


if __name__ == "__main__":
    args = sys.argv
    if len(args) == 1 or 'help' in args:
        cli.general_parser(settings.commands)
        sys.exit(0)
    command = settings.commands[args[1]][args[2]]
    parser = cli.create_parser_from_yaml(command)
    parsed_args = vars(parser.parse_args(args[3:]))

    module = importlib.import_module(command['package'])
    method = getattr(module, command['method'])
    logger.info(f"Command received: {command['package']}.{command['method']} Arguments: {parsed_args}")
    if 'async' not in command or not command['async']:
        if command['splitArgs']:
            method(**parsed_args)
            sys.exit(0)
        method(parsed_args)
        sys.exit(0)
    asyncio.run(method(**parsed_args))

    
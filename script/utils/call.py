from argparse import ArgumentParser, Namespace
from enum import Enum, auto
from script import import_index, helper, install
from script.utils.logutil import Logger
from script.utils.constant import *


class From(Enum):
    HELPER = auto()
    HUMAN = auto()

def __register_arg(arg: list[str] | None = None) -> Namespace:
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    # helper
    subparsers.add_parser("helper")

    # import
    parser_import = subparsers.add_parser("import")
    parser_import.add_argument(
        "--platform",
        choices=[PlatForm.MODRINTH, PlatForm.CURSEFORGE, PlatForm.ALL],
        default=PlatForm.MODRINTH
    )

    # install
    parser_install = subparsers.add_parser("install")
    parser_install.add_argument(
        "--platform",
        choices=[PlatForm.MODRINTH, PlatForm.CURSEFORGE, PlatForm.ALL],
        default=PlatForm.ALL
    )
    parser_install.add_argument("--version")

    args = parser.parse_args(arg)
    return args


def call(arg: list[str] | None = None, by: From = From.HUMAN):
    args = __register_arg(arg)
    match args.command:
        case "helper":
            if by == From.HUMAN:
                helper.run()
            else:
                log = Logger("helper").get_log()
                log.error("WHAT ARE YOU DOING???")

        case "import":
            import_index.run(args.platform)

        case "install":
            install.run(args.platform, args.version)

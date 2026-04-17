from argparse import ArgumentParser, Namespace
from enum import Enum, auto
from script import import_index, helper, install, create, remove, update, export, refresh, loader, update_version
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
    parser_install.add_argument("--versions")

    # create
    parser_create = subparsers.add_parser("create").add_mutually_exclusive_group()
    parser_create.add_argument("--versions")
    parser_create.add_argument("--snapshot", action="store_true")

    # remove
    parser_remove = subparsers.add_parser("remove")
    parser_remove.add_argument(
        "--versions",
        required=True
    )

    # update
    parser_update = subparsers.add_parser("update")
    parser_update.add_argument("--version")

    # export
    parser_export = subparsers.add_parser("export")
    parser_export.add_argument("--version")
    parser_export.add_argument(
        "--platform",
        choices=[PlatForm.MODRINTH, PlatForm.CURSEFORGE, PlatForm.ALL],
        default=PlatForm.ALL
    )

    # refresh
    subparsers.add_parser("refresh")

    # update loader
    subparsers.add_parser('loader')

    # update version
    parser_update_version = subparsers.add_parser("update_version")
    parser_update_version.add_argument(
        "--match",
        default="*"
    )
    parser_update_version.add_argument(
        "--version",
        required=True
    )

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
            install.run(args.platform, args.versions)

        case "create":
            create.run(
                [] if args.versions is None else args.versions.split(","),
                args.snapshot
            )

        case "remove":
            remove.run(str(args.versions).split(","))

        case "update":
            update.run(args.version)

        case "export":
            export.run(args.version, args.platform)

        case "refresh":
            refresh.run()

        case "loader":
            loader.run()

        case "update_version":
            update_version.run(args.match, args.version)

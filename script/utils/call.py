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
    subparsers.add_parser("helper", description="Start helper")

    # import
    parser_import = subparsers.add_parser("import", description="Import mods from the '.index' folder")
    parser_import.add_argument(
        "--platform",
        choices=[PlatForm.MODRINTH, PlatForm.CURSEFORGE, PlatForm.ALL],
        default=PlatForm.MODRINTH,
        help="default 'modrinth'"
    )

    # install
    parser_install = subparsers.add_parser("install", description="parse and download files from 'file_list'")
    parser_install.add_argument(
        "--platform",
        choices=[PlatForm.MODRINTH, PlatForm.CURSEFORGE, PlatForm.ALL],
        default=PlatForm.ALL,
        help="default 'all'"
    )
    parser_install.add_argument("--versions", help="Your version folder name, if empty select all")

    # create
    parser_create = subparsers.add_parser("create", description="Create a Minecraft version").add_mutually_exclusive_group()
    parser_create.add_argument("--versions", help="Minecraft version, if there are multiple uses ',' split")
    parser_create.add_argument("--snapshot", action="store_true", help="Use the latest snapshot")

    # remove
    parser_remove = subparsers.add_parser("remove", description="Removed the Minecraft version")
    parser_remove.add_argument(
        "--versions",
        required=True,
        help="The name of the Minecraft folder that needs to be removed, if there are multiple uses ',' split"
    )

    # update
    parser_update = subparsers.add_parser("update", description="Update mod")
    parser_update.add_argument(
        "--match",
        default="*",
        help="NPM-compliant version matching, default '*'"
    )

    # export
    parser_export = subparsers.add_parser("export", description="Export the integration package")
    parser_export.add_argument("--version", help="The name of the Minecraft folder")
    parser_export.add_argument(
        "--platform",
        choices=[PlatForm.MODRINTH, PlatForm.CURSEFORGE, PlatForm.ALL],
        default=PlatForm.ALL,
        help="default 'all'"
    )

    # refresh
    subparsers.add_parser("refresh", description="Refresh everything")

    # update loader
    subparsers.add_parser("loader", description="Update fabric_loader to the latest version")

    # update version
    parser_update_version = subparsers.add_parser("update_version", description="Update the version of the 'pack.toml'")
    parser_update_version.add_argument(
        "--match",
        default="*",
        help="NPM-compliant version matching, default '*'"
    )
    parser_update_version.add_argument(
        "--version",
        required=True,
        help="e.g: X.Y.Z"
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
            update.run(args.match)

        case "export":
            export.run(args.version, args.platform)

        case "refresh":
            refresh.run()

        case "loader":
            loader.run()

        case "update_version":
            update_version.run(args.match, args.version)

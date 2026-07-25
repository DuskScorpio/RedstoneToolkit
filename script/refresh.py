from script.utils.constant import *
from script.utils import logutil, util
from pathlib import Path
from subprocess import Popen, PIPE, STDOUT

def run():
    for platform in [PlatFormLegacy.MODRINTH, PlatFormLegacy.CURSEFORGE]:
        vers = util.get_dir_vers(platform)
        for mc_ver in vers:
            log = logutil.get_log("refresh", False)
            path = Path(platform).joinpath(mc_ver)
            with Popen(
                [PACKWIZ, "refresh"],
                cwd=path,
                stdout=PIPE,
                stderr=STDOUT,
                text=True,
                bufsize=1
            ) as process:
                for e in process.stdout:
                    log.info(f"({platform}/{mc_ver}) {e.strip()}")
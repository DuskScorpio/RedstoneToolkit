from pathlib import Path
from subprocess import Popen, STDOUT, PIPE

from script.utils import logutil, util
from script.utils.constant import *


def run():
    for platform in PlatformSource:
        dirs = util.get_dir_vers(platform)
        for mc_dir in dirs:
            log = logutil.get_log("update_loader")
            path = Path(platform).joinpath(mc_dir)
            with Popen(
                [PACKWIZ, "migrate", "loader", "latest"],
                cwd=path,
                stdout=PIPE,
                stderr=STDOUT,
                text=True,
                bufsize=1
            ) as process:
                for e in process.stdout:
                    log.info(f"({platform}/{mc_dir}) {e.strip()}")

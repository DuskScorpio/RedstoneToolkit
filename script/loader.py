from script.utils.constant import *
from script.utils import logutil, util
from pathlib import Path
from subprocess import Popen, STDOUT, PIPE

def run():
    for platform in [PlatForm.MODRINTH, PlatForm.CURSEFORGE]:
        dirs = util.get_dir_vers(platform)
        for mc_dir in dirs:
            log = logutil.Logger(f"{platform}/{mc_dir}").get_log()
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
                    log.info(e.strip())
                process.wait()

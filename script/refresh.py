from script.utils.constant import *
from script.utils import logutil, util
from pathlib import Path
from subprocess import Popen, PIPE

def run():
    for platform in [PlatForm.MODRINTH, PlatForm.CURSEFORGE]:
        vers = util.get_dir_vers(platform)
        for mc_ver in vers:
            log = logutil.Logger(f"{platform}/{mc_ver}").get_log()
            path = Path(platform).joinpath(mc_ver)
            process = Popen(
                [PACKWIZ, "refresh"],
                cwd=path,
                stdin=PIPE,
                stdout=PIPE,
                stderr=PIPE,
                text=True,
                bufsize=1
            )
            for e in process.stdout:
                log.info(e.strip())
            process.wait()
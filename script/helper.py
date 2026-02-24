from prompt_toolkit import PromptSession
from prompt_toolkit.completion import NestedCompleter
from script.utils.constant import *
from script.utils.logutil import Logger

import shlex


def run():
    from script.utils.call import call, From
    completer = NestedCompleter.from_nested_dict(COMMAND)
    log = Logger("helper").get_log()
    session = PromptSession()
    while True:
        text = session.prompt(">> ", completer=completer)
        if text == "stop":
            break
        call(arg=shlex.split(text), by=From.HELPER)
    log.info("bye~")

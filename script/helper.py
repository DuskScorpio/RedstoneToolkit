from prompt_toolkit import prompt
from prompt_toolkit.completion import NestedCompleter

import shlex


def run():
    from script.call import call, From
    completer = NestedCompleter.from_nested_dict({
        "stop": None,
        "import": {"-platform": {"mr", "cf", "all"}}
    })
    while True:
        text = prompt('', completer=completer)
        if text == "stop":
            break
        call(arg=shlex.split(text), by=From.HELPER)

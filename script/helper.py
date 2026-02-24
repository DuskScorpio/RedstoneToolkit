from prompt_toolkit import prompt
from prompt_toolkit.completion import NestedCompleter

import shlex


def run():
    from script.call import call, From
    completer = NestedCompleter.from_nested_dict({
        "import": {"-platform": {"mr", "cf", "all"}}
    })
    text = prompt('', completer=completer)
    call(arg=shlex.split(text), by=From.HELPER)

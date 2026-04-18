from typing import Iterable, override

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, CompleteEvent, Completion, WordCompleter
from prompt_toolkit.document import Document

from script.utils.constant import *
from script.utils.logutil import Logger

import shlex


def run():
    from script.utils.call import call, From
    completer = HelperCompleter.from_nested_dict(COMMAND)
    log = Logger("helper").get_log()
    session = PromptSession()
    while True:
        text = session.prompt(">> ", completer=completer)
        if text == "stop":
            break
        try:
            call(arg=shlex.split(text), by=From.HELPER)
        except SystemExit:
            ...
    log.info("bye~")


class HelperCompleter(Completer):
    def __init__(
            self,
            options: dict[str, Completer | None],
            no_empty_options: dict[str, Completer | None]
    ):
        self.options = options
        self.no_empty_options = no_empty_options


    @classmethod
    def from_nested_dict(cls, data: dict) -> HelperCompleter:
        options: dict[str, Completer | None] = dict()
        options_no_empty: dict[str, Completer | None] = dict()
        for key, value in data.items():
            if isinstance(value, Completer):
                options[key] = value
            elif isinstance(value, dict):
                options[key] = cls.from_nested_dict(value)
            elif isinstance(value, set):
                options[key] = cls.from_nested_dict(dict.fromkeys(value))
            else:
                assert value is None
                options[key] = None

        for key, value in data.items():
            if key == "":
                continue
            if isinstance(value, Completer):
                options_no_empty[key] = value
            elif isinstance(value, dict):
                options_no_empty[key] = cls.from_nested_dict(value)
            elif isinstance(value, set):
                options_no_empty[key] = cls.from_nested_dict(dict.fromkeys(value))
            else:
                assert value is None
                options_no_empty[key] = None
        return cls(options, options_no_empty)


    @override
    def get_completions(self, document: Document, complete_event: CompleteEvent) -> Iterable[Completion]:
        # Split document.
        text = document.text_before_cursor.lstrip()
        stripped_len = len(document.text_before_cursor) - len(text)

        # If there is a space, check for the first term, and use a
        # subcompleter.
        if " " in text:
            first_term = text.split()[0]
            completer = self.no_empty_options.get(first_term)

            # If we have a sub completer, use this for the completions.
            if completer is not None:
                remaining_text = text[len(first_term):].lstrip()
                move_cursor = len(text) - len(remaining_text) + stripped_len

                new_document = Document(
                    remaining_text,
                    cursor_position=document.cursor_position - move_cursor,
                )

                yield from completer.get_completions(new_document, complete_event)
            else:
                if "" in self.options:
                    completer = self.options.get("")
                    remaining_text = text[len(first_term):].lstrip()
                    move_cursor = len(text) - len(remaining_text) + stripped_len

                    new_document = Document(
                        remaining_text,
                        cursor_position=document.cursor_position - move_cursor,
                    )

                    yield from completer.get_completions(new_document, complete_event)

        # No space in the input: behave exactly like `WordCompleter`.
        else:
            completer = WordCompleter(
                list(self.no_empty_options), ignore_case=True
            )
            yield from completer.get_completions(document, complete_event)
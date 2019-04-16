from abc import ABC, abstractmethod
from pprint import pformat
from typing import Any, Tuple, Union

from discord import Embed


class EvalFormatter(ABC):
    @abstractmethod
    def format(self, input_: str, output: Any, printed: str) -> Union[str, Embed, Tuple[str, Embed]]:
        ...

    @abstractmethod
    def exit(self, input_: str) -> str:
        pass


class SimpleEvalFormatter(EvalFormatter):
    def format(self, input_: str, output: Any, printed: str) -> Union[str, Embed, Tuple[str, Embed]]:
        lines = input_.split("\n")
        line_start = ">>> " + lines[0]
        other_lines = "\n".join(
            "... "+(line
                    if not line.startswith("return")
                    else line[6:].strip())
            for line in lines[1:]
        )

        args = [line_start]
        if other_lines:
            args.append(other_lines)
        if printed:
            args.append(printed)
        if output is not None:
            args.append(repr(output))
            if isinstance(output, Embed):
                args[-1] = "<Embed>"
                return "\n".join(args), output

        return "\n".join(
            args
        )

    def exit(self, input_: str):
        return f">>> {input_}\nInterpreter reset!"


class IPythonEvalFormatter(EvalFormatter):
    def __init__(self, pretty: bool = True, max_lines: int = 10):
        self.line_no = 1
        self.pretty = pretty
        self.max_lines = max_lines

    def truncate(self, text: str) -> str:
        if text.count("\n") > self.max_lines:
            lines = text.split("\n")
            return "\n".join(
                (*lines[:3], "...", *lines[-3:])
            )
        return text

    def format(self, input_: str, output: Any, printed: str) -> Union[str, Embed, Tuple[str, Embed]]:
        lines = input_.split("\n")
        line_start = f"In [{self.line_no}]: " + lines[0]
        indent = len(str(self.line_no))
        other_lines = "\n".join(
            " "*(2+indent) + "...: " + (line
                                        if not line.startswith("return")
                                        else line[6:].strip())
            for line in lines[1:]
        )
        out_line = f"Out[{self.line_no}]: " + (pformat(output, compact=True, width=60)
                                               if self.pretty else repr(output))
        self.line_no += 1

        args = [line_start]
        if other_lines:
            args.append(other_lines)
        if printed:
            args.append(self.truncate(printed.strip()))
        if output is not None:
            args.append(self.truncate(out_line))
            if isinstance(output, Embed):
                args[-1] = f"Out[{self.line_no-1}]: <Embed>"
                return "\n".join(args), output

        return "\n".join(
            args
        )

    def exit(self, input_: str):
        prefix = f"In [{self.line_no}]: "
        self.line_no = 1
        return f"{prefix}{input_}\nInterpreter reset!"

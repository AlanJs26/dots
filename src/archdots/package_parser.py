from typing import NamedTuple
from lark import Lark, Transformer

parser = Lark(
    r"""
        start: _NL? (item|function|_NL)+

        ?value: string
            | array

        item: NAME "=" value? (_NL|)

        NAME: /\w/+

        string: ESCAPED_STRING
        array: "(" string* ")"

        function: NAME "(" ")" "{" content "}" _NL?
        content: (TEXT | "{" content "}")*
        TEXT: /[^{}]+/

        _STRING_INNER: /.*?/
        _STRING_ESC_INNER: _STRING_INNER /(?<!\\)(\\\\)*?/

        ESCAPED_STRING : ("\"" _STRING_ESC_INNER "\"") | ("'" _STRING_ESC_INNER "'")

        %import common.NEWLINE -> _NL
        %import common.WS_INLINE
        %import common.SH_COMMENT
        %ignore WS_INLINE 
        %ignore SH_COMMENT
    """
)


class Item(NamedTuple):
    key: str
    value: str


class Function(NamedTuple):
    name: str
    content: str


class PackageTransformer(Transformer):
    def function(self, items):
        name, content = items
        return Function(name, content)

    def content(self, content):
        return " ".join([str(token) for token in content])

    def NAME(self, content):
        return str(content)

    def string(self, content):
        (s,) = content
        return s[1:-1]

    def array(self, items):
        return items

    def item(self, key_value):
        k, v = key_value
        return Item(str(k), v)

    def start(self, items):
        return items

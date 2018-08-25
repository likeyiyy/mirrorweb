from enum import Enum, unique
import re
from mirrors.libs.utils import decode_uri


@unique
class TokenType(Enum):
    Identify = 1
    EQ = 2  # =
    And = 3  # &
    Or = 4  # |
    LeftBracket = 5  # [
    RightBracket = 6  # ]
    LeftParen = 7  # (
    RightParen = 8  # )
    Not = 9  # !
    EOF = 99


class Token(object):

    def __init__(self, type, value=None):
        self.type = type
        self.value = value


@unique
class ScannerState(Enum):
    Normal = 0
    InStr = 1


class GQLError(Exception):
    pass


class GQLAndError(GQLError):
    pass


class GQLIdentifyError(GQLError):
    pass


class TokenTypeError(GQLError):
    pass


class Scanner(object):

    def __init__(self, input):
        self.tokens = []
        self.raw = str(input)
        self.i = 0
        self.scan_input()
        self.output_pos = 0

    def scan_input(self):
        state = ScannerState.Normal
        buf = []
        self.raw += '#'
        length = len(self.raw)
        while self.i < length:
            char = self.raw[self.i]
            if state == ScannerState.Normal:
                if char == '#':
                    self.tokens.append(Token(TokenType.EOF))
                elif char == '[':
                    self.tokens.append(Token(TokenType.LeftParen))
                    self.tokens.append(Token(TokenType.LeftParen))
                elif char == ']':
                    self.tokens.append(Token(TokenType.RightParen))
                    self.tokens.append(Token(TokenType.RightParen))
                elif char == '(':
                    self.tokens.append(Token(TokenType.LeftParen))
                elif char == ')':
                    self.tokens.append(Token(TokenType.RightParen))
                elif char == '=':
                    self.tokens.append(Token(TokenType.EQ))
                    state = ScannerState.InStr
                elif char == '|':
                    self.tokens.append(Token(TokenType.Or))
                elif char == '&':
                    self.tokens.append(Token(TokenType.And))
                elif char == '!':
                    self.tokens.append(Token(TokenType.Not))
                elif char != ' ':
                    state = ScannerState.InStr
                    buf.append(char)
            elif state == ScannerState.InStr:
                if char in '#()[]=|&':
                    self.i -= 1
                    str = decode_uri(''.join(buf))
                    self.tokens.append(Token(TokenType.Identify, str))
                    state = ScannerState.Normal
                    buf = []
                else:
                    buf.append(char)
            self.i += 1

    def peak(self, step=0):
        try:
            return self.tokens[self.output_pos + step]
        except:
            raise GQLError({'postion': self.output_pos})

    def get_next(self):
        ret = self.tokens[self.output_pos]
        self.output_pos += 1
        return ret


class ChildrenAST(object):

    def __init__(self):
        self.children = []

    def add_child(self, child):
        self.children.append(child)


class OrAST(ChildrenAST):

    def accept(self, visitor):
        return visitor.visit_or(self)


class AndAST(ChildrenAST):

    def accept(self, visitor):
        return visitor.visit_and(self)


class AttrAST(object):

    def __init__(self, key_token=None, value_token=None):
        if key_token:
            self.key = key_token.value
        else:
            self.key = None
        if value_token:
            self.val = value_token.value
        else:
            self.val = ''

    def accept(self, visitor):
        return visitor.visit_attr(self)

    def clone(self):
        cloned = type(self)()
        cloned.key = self.key
        cloned.val = self.val
        return cloned


class NotAST(object):

    def __init__(self, ast):
        self.ast = ast

    def accept(self, visitor):
        return visitor.visit_not(self)


class Parser(object):

    def __init__(self, scanner=None):
        self.scanner = scanner

    def expect_next(self, token_type):
        token = self.scanner.get_next()
        self.expect_token_type(token, token_type)

    def expect_token_type(self, token, token_type):
        if token.type != token_type:
            raise TokenTypeError({
                "expect": token_type.name,
                "got": token.type.name,
                "postion": self.scanner.output_pos,
            })

    @classmethod
    def parse(cls, str):
        if str:
            ins = cls(Scanner(str))
            ret = ins.parse_and()
            ins.expect_next(TokenType.EOF)
            return ret
        return AttrAST(Token(TokenType.EOF, ''), Token(TokenType.EOF, ''))

    def parse_and(self):
        return self._parse_one_more_pattern(
            self.parse_or,
            AndAST,
            TokenType.And,
        )

    def parse_or(self):
        return self._parse_one_more_pattern(self.parse_not, OrAST, TokenType.Or)

    def parse_not(self):
        ahead = self.scanner.peak()
        if ahead.type == TokenType.Not:
            self.scanner.get_next()
            attr_ast = self.parse_term()
            return NotAST(attr_ast)
        return self.parse_term()

    def parse_term(self):
        token = self.scanner.get_next()
        if token.type == TokenType.LeftParen:
            ret = self.parse_and()
            if isinstance(ret, AttrAST):
                ast = AndAST()
                ast.add_child(ret)
            else:
                ast = ret
            self.expect_next(TokenType.RightParen)
            return ast
        else:
            self.expect_token_type(token, TokenType.Identify)
            key = token
            ahead = self.scanner.peak()
            if ahead.type == TokenType.EQ:
                self.scanner.get_next()
                val = self.scanner.get_next()
                return AttrAST(key, val)
            else:
                return AttrAST(key)

    def _parse_one_more_pattern(
            self,
            parse_child_method,
            ins_constructor,
            token_type,
    ):
        child = parse_child_method()
        ahead = self.scanner.peak()
        has_child = False
        ins = ins_constructor()
        ins.add_child(child)
        while ahead.type == token_type:
            has_child = True
            self.scanner.get_next()
            child = parse_child_method()
            ins.add_child(child)
            ahead = self.scanner.peak()
        if has_child:
            return ins
        else:
            return child

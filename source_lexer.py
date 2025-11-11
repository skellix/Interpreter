import input_tokens


class LexerToken:
    """
    The lexer produces these tokens. They have additional information the parser needs for processing.
    """
    
    token: input_tokens.InputToken
    digit: bool
    whitespace: bool
    plus: bool
    minus: bool
    multiply: bool
    divide: bool
    percent: bool
    equals: bool

    def __init__(self, token: input_tokens.InputToken) -> None:
        self.token = token
        self.digit = ord('0') <= ord(token.c) <= ord(
            '9') if len(token.c) > 0 else False
        self.whitespace = token.c == ' ' or token.c == '\t' or token.c == '\r' or token.c == '\n'
        self.plus = token.c == '+'
        self.minus = token.c == '-'
        self.multiply = token.c == '*'
        self.divide = token.c == '/'
        self.percent = token.c == '%'
        self.equals = token.c == '='

    def __str__(self) -> str:
        return f"token({self.token})"


def lex(tokens: list[input_tokens.InputToken]) -> list[LexerToken]:
    return [LexerToken(token) for token in tokens]

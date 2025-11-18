from typing import TypeVar, Generic, Callable, Optional
from enum import Enum

import basic_interpreter.input_tokens as input_tokens
import basic_interpreter.source_lexer as source_lexer
import interpreter_vm.parser_node as parser_node

"""
Expresion -> '=' BitwiseShift $
BitwiseShift -> AdditionOrSubtraction (('<' '<' | '>' '>') AdditionOrSubtraction)*
AdditionOrSubtraction -> MultiplicationOrDivision (('+' | '-') MultiplicationOrDivision)*
MultiplicationOrDivision -> Exponentiation (('*' | '/' | '%') Exponentiation)*
Exponentiation -> Numeric ('**' Numeric)*
Numeric -> Number | ParenGroup
Number -> Float | Integer
Integer -> Digit+
Float -> Digit+ '.' Digit+
ParenGroup -> '(' BitwiseShift ')'
"""


class ParseResultType(Enum):
    UNPARSED = 0
    PARSING = 1
    SUCCESS = 2
    FAILURE = 3


T = TypeVar('T')


class ParseResult(Generic[T]):
    """
    Result of a parse step
    """

    def __init__(self, start: 'ParseState', type: ParseResultType, value: T, next: 'ParseState') -> None:
        super().__init__()
        self.start = start
        self.type = type
        self.value = value
        self.next = next


class ParseIssue:
    def __init__(self, start: 'ParseState', issue: Exception, next: Optional['ParseState'] = None) -> None:
        super().__init__()
        self.start = start
        self.issue = issue
        self.next = next

    def __str__(self) -> str:
        return f"{self.issue} at {self.start.get_line_number()}:{self.start.get_column_number()}"


class ParseIssues:
    def __init__(self) -> None:
        super().__init__()
        self.issues: list[ParseIssue] = []

    def add_issue(self, start: 'ParseState', issue: Exception, next: Optional['ParseState'] = None):
        self.issues.append(ParseIssue(start, issue, next))


class ParseState:
    def __init__(self, lexer_tokens: list[source_lexer.LexerToken], index: int = 0, issues: ParseIssues = ParseIssues()) -> None:
        self.lexer_tokens = lexer_tokens
        self.index = index
        self.issues = issues

    def get_token(self):
        return self.lexer_tokens[self.index]

    def is_char(self, c: str):
        return self.get_token().token.c == c

    def is_one_of_chars(self, options: list[str]):
        return next((c for c in options if self.is_char(c)), None)

    def is_end(self):
        return isinstance(self.get_token().token, input_tokens.EndOfStream)

    def get_next(self):
        return ParseState(self.lexer_tokens, self.index + 1, self.issues)

    def get_success(self):
        return ParseResult(self, ParseResultType.SUCCESS, self.get_token(), self.get_next())

    def get_failure(self):
        return ParseResult(self, ParseResultType.FAILURE, self.get_token(), self.get_next())

    def get_char(self, c: str):
        if self.is_char(c):
            return self.get_success()
        else:
            return self.get_failure()

    def get_digit(self):
        if self.get_token().digit:
            return self.get_success()
        else:
            return self.get_failure()

    def get_whitespace(self):
        if self.get_token().whitespace:
            return self.get_success()
        else:
            return self.get_failure()

    def get_one_of_chars(self, options: list[str]):
        if self.is_one_of_chars(options):
            return self.get_success()
        else:
            return self.get_failure()

    def raise_issue(self, issue: Exception, next: Optional['ParseState'] = None):
        self.issues.add_issue(self, issue, next)

    def get_line_number(self):
        return len([token for token in self.lexer_tokens[:self.index] if token.token.c == '\n']) + 1

    def get_column_number(self):
        for i, token in enumerate(reversed(self.lexer_tokens[:self.index])):
            if token.token.c == '\n':
                return i + 1

        return self.index + 1

    def get_last_issues(self) -> list[ParseIssue]:
        if len(self.issues.issues) == 0:
            return []

        issue_index = sorted(
            (issue.start.index for issue in self.issues.issues), reverse=True)[0]
        return [issue for issue in self.issues.issues if issue.start.index == issue_index]


def get_not(parse_result: ParseResult[T]):
    return ParseResult(parse_result.start, ParseResultType.SUCCESS if parse_result.type == ParseResultType.FAILURE else ParseResultType.FAILURE, parse_result.value, parse_result.next)


def get_choose(state: ParseState, *get_funcs: Callable[[ParseState], ParseResult[None] | ParseResult[T]]):
    if len(get_funcs) == 0:
        return ParseResult(state, ParseResultType.FAILURE, None, state)

    for get_func in get_funcs:
        result = get_func(state)

        if result.type != ParseResultType.FAILURE:
            return result

    return ParseResult(state, ParseResultType.FAILURE, None, state)


def get_each(state: ParseState, **get_funcs: Callable[[ParseState], ParseResult[None] | ParseResult[T]]):
    parts: dict[str, ParseResult[None] | ParseResult[T]] = {}

    if len(get_funcs) == 0:
        return ParseResult(state, ParseResultType.SUCCESS, parts, state)

    current_state = state

    for label in get_funcs:
        get_func = get_funcs[label]
        result = get_func(current_state)

        if result.type == ParseResultType.FAILURE:
            return ParseResult(state, ParseResultType.FAILURE, None, state)

        parts[label] = result
        current_state = result.next

    return ParseResult(state, ParseResultType.SUCCESS, parts, current_state)


def get_zero_or_more(state: ParseState, get_func: Callable[[ParseState], ParseResult[None] | ParseResult[T]]) -> ParseResult[list[ParseResult[None] | ParseResult[T]]]:
    parts: list[ParseResult[None] | ParseResult[T]] = []
    current_result_type: ParseResultType = ParseResultType.SUCCESS
    previous_state = state
    current_state = state

    # get the rest of the parts and add them to the list
    while current_result_type != ParseResultType.FAILURE:
        current_part = get_func(current_state)
        current_result_type = current_part.type

        # did it match?
        if current_result_type != ParseResultType.FAILURE:
            parts.append(current_part)

        previous_state = current_state
        current_state = current_part.next

    return ParseResult(state, ParseResultType.SUCCESS, parts, previous_state)


def get_one_or_more(state: ParseState, get_func: Callable[[ParseState], ParseResult[None] | ParseResult[T]]):
    # return get_each(state,
    #                 first = lambda x: get_func(x),
    #                 rest = lambda x: get_zero_or_more(x, get_func))

    # Get the first part
    start_result = get_func(state)

    # did it match?
    if start_result.type == ParseResultType.FAILURE:
        return ParseResult(state, ParseResultType.FAILURE, None, state)

    # Get the rest
    rest = get_zero_or_more(start_result.next, get_func)

    # did they match?
    if rest.type == ParseResultType.FAILURE:
        return ParseResult(state, ParseResultType.SUCCESS, [start_result], start_result.next)

    # parts: list[ParseResult[None] | ParseResult[T]] = rest.value[:]
    parts = rest.value[:]
    parts.insert(0, start_result)

    return ParseResult(state, ParseResultType.SUCCESS, parts, rest.next)


def debug_wrapper(func: Callable[[ParseState], ParseResult[None] | ParseResult[T]]):
    def wrapper(state: ParseState) -> ParseResult[None] | ParseResult[T]:
        try:
            return func(state)
        except Exception as e:
            state.raise_issue(e)
            return ParseResult(state, ParseResultType.FAILURE, None, state)

    return wrapper


@debug_wrapper
def parse_expresion(state: ParseState):
    """
    Expresion -> \\s* '=' \\s* BitwiseShift $
    """
    leading_whitespace_part = get_zero_or_more(
        state, lambda x: x.get_whitespace())

    # did it match?
    if leading_whitespace_part.type == ParseResultType.FAILURE:
        return ParseResult(state, ParseResultType.FAILURE, None, state)

    operator_part = leading_whitespace_part.next.get_char('=')

    # did it match?
    if operator_part.type == ParseResultType.FAILURE:
        leading_whitespace_part.next.raise_issue(
            Exception("Expected '='"), state)
        return ParseResult(state, ParseResultType.FAILURE, None, state)

    whitespace_part = get_zero_or_more(
        operator_part.next, lambda x: x.get_whitespace())

    # did it match?
    if whitespace_part.type == ParseResultType.FAILURE:
        return ParseResult(state, ParseResultType.FAILURE, None, state)

    value_part = parse_bitwise_shift(whitespace_part.next)

    # did it match?
    if value_part.type == ParseResultType.FAILURE or value_part.value is None:
        whitespace_part.next.raise_issue(
            Exception("Expected bitwise shift"), state)
        return ParseResult(state, ParseResultType.FAILURE, None, state)

    if value_part.next.is_end():
        return ParseResult(state, ParseResultType.SUCCESS, parser_node.Expresion(value_part.value), value_part.next)
    else:
        value_part.next.raise_issue(Exception("Expected end of file"), state)
        return ParseResult(state, ParseResultType.FAILURE, None, state)
        # raise Exception("Expected end of file!")


@debug_wrapper
def parse_bitwise_shift_part(state: ParseState):
    leading_whitespace_part = get_zero_or_more(
        state, lambda x: x.get_whitespace())

    # did it match?
    if leading_whitespace_part.type == ParseResultType.FAILURE:
        return ParseResult(state, ParseResultType.FAILURE, None, state)

    operator_part = leading_whitespace_part.next.get_one_of_chars(['<', '>'])

    # did it match?
    if operator_part.type == ParseResultType.FAILURE:
        leading_whitespace_part.next.raise_issue(
            Exception("Expected '<' or >'"), state)
        return ParseResult(state, ParseResultType.FAILURE, None, state)

    operator_part2 = operator_part.next.get_char(operator_part.value.token.c)

    # did it match?
    if operator_part2.type == ParseResultType.FAILURE:
        operator_part.next.raise_issue(
            Exception(f"Expected '{operator_part.value.token.c}'"), state)
        return ParseResult(state, ParseResultType.FAILURE, None, state)

    whitespace_part = get_zero_or_more(
        operator_part2.next, lambda x: x.get_whitespace())

    # did it match?
    if whitespace_part.type == ParseResultType.FAILURE:
        return ParseResult(state, ParseResultType.FAILURE, None, state)

    right_part = parse_addition_or_subtraction(whitespace_part.next)

    # did it match?
    if right_part.type == ParseResultType.FAILURE or right_part.value is None:
        whitespace_part.next.raise_issue(
            Exception("Expected addition or subtraction"), state)
        return ParseResult(state, ParseResultType.FAILURE, None, state)

    return ParseResult(state, ParseResultType.SUCCESS, parser_node.BitwiseShiftPart(operator_part.value, right_part.value), right_part.next)


@debug_wrapper
def parse_bitwise_shift(state: ParseState) -> ParseResult[None] | ParseResult[parser_node.BitwiseShift]:
    """
    BitwiseShift -> AdditionOrSubtraction (\\s* ('<' '<' | '>' '>') \\s* AdditionOrSubtraction)*
    """
    start_part = parse_addition_or_subtraction(state)

    if start_part.type == ParseResultType.FAILURE or start_part.value is None:
        state.raise_issue(
            Exception("Expected addition or subtraction"), state)
        return ParseResult(state, ParseResultType.FAILURE, None, state)

    rest_part = get_zero_or_more(
        start_part.next, parse_bitwise_shift_part)

    if rest_part.type == ParseResultType.FAILURE:
        return ParseResult(state, ParseResultType.FAILURE, None, state)

    rest: list[parser_node.BitwiseShiftPart] = []

    for part in rest_part.value:
        if part.value is not None:
            rest.append(part.value)

    return ParseResult(state, ParseResultType.SUCCESS, parser_node.BitwiseShift(start_part.value, rest), rest_part.next)


@debug_wrapper
def parse_addition_or_subtraction_part(state: ParseState):
    leading_whitespace_part = get_zero_or_more(
        state, lambda x: x.get_whitespace())

    # did it match?
    if leading_whitespace_part.type == ParseResultType.FAILURE:
        return ParseResult(state, ParseResultType.FAILURE, None, state)

    operator_part = leading_whitespace_part.next.get_one_of_chars(['+', '-'])

    # did it match?
    if operator_part.type == ParseResultType.FAILURE:
        leading_whitespace_part.next.raise_issue(
            Exception("Expected '+' or '-'"), state)
        return ParseResult(state, ParseResultType.FAILURE, None, state)

    whitespace_part = get_zero_or_more(
        operator_part.next, lambda x: x.get_whitespace())

    # did it match?
    if whitespace_part.type == ParseResultType.FAILURE:
        return ParseResult(state, ParseResultType.FAILURE, None, state)

    right_part = parse_multiplication_or_division(whitespace_part.next)

    # did it match?
    if right_part.type == ParseResultType.FAILURE or right_part.value is None:
        whitespace_part.next.raise_issue(
            Exception("Expected multiplication or division"), state)
        return ParseResult(state, ParseResultType.FAILURE, None, state)

    return ParseResult(state, ParseResultType.SUCCESS, parser_node.AdditionOrSubtractionPart(operator_part.value, right_part.value), right_part.next)


@debug_wrapper
def parse_addition_or_subtraction(state: ParseState) -> ParseResult[None] | ParseResult[parser_node.AdditionOrSubtraction]:
    """
    AdditionOrSubtraction -> MultiplicationOrDivision (\\s* ('+' | '-') \\s* MultiplicationOrDivision)*
    """
    start_part = parse_multiplication_or_division(state)

    if start_part.type == ParseResultType.FAILURE or start_part.value is None:
        state.raise_issue(
            Exception("Expected multiplication or division"), state)
        return ParseResult(state, ParseResultType.FAILURE, None, state)

    rest_part = get_zero_or_more(
        start_part.next, parse_addition_or_subtraction_part)

    if rest_part.type == ParseResultType.FAILURE:
        return ParseResult(state, ParseResultType.FAILURE, None, state)

    rest: list[parser_node.AdditionOrSubtractionPart] = []

    for part in rest_part.value:
        if part.value is not None:
            rest.append(part.value)

    return ParseResult(state, ParseResultType.SUCCESS, parser_node.AdditionOrSubtraction(start_part.value, rest), rest_part.next)


@debug_wrapper
def parse_multiplication_or_division_part(state: ParseState):
    leading_whitespace_part = get_zero_or_more(
        state, lambda x: x.get_whitespace())

    # did it match?
    if leading_whitespace_part.type == ParseResultType.FAILURE:
        return ParseResult(state, ParseResultType.FAILURE, None, state)

    operator_part = leading_whitespace_part.next.get_one_of_chars([
                                                                  '*', '/', '%'])

    # did it match?
    if operator_part.type == ParseResultType.FAILURE:
        leading_whitespace_part.next.raise_issue(
            Exception("Expected '*' or '/' or '%'"), state)
        return ParseResult(state, ParseResultType.FAILURE, None, state)

    whitespace_part = get_zero_or_more(
        operator_part.next, lambda x: x.get_whitespace())

    # did it match?
    if whitespace_part.type == ParseResultType.FAILURE:
        return ParseResult(state, ParseResultType.FAILURE, None, state)

    right_part = parse_exponentiation(whitespace_part.next)

    # did it match?
    if right_part.type == ParseResultType.FAILURE or right_part.value is None:
        whitespace_part.next.raise_issue(
            Exception("Expected exponentiation"), state)
        return ParseResult(state, ParseResultType.FAILURE, None, state)

    return ParseResult(state, ParseResultType.SUCCESS, parser_node.MultiplicationOrDivisionPart(operator_part.value, right_part.value), right_part.next)


@debug_wrapper
def parse_multiplication_or_division(state: ParseState) -> ParseResult[None] | ParseResult[parser_node.MultiplicationOrDivision]:
    """
    MultiplicationOrDivision -> Exponentiation (\\s* ('*' | '/' | '%') \\s* Exponentiation)*
    """
    start_part = parse_exponentiation(state)

    if start_part.type == ParseResultType.FAILURE or start_part.value is None:
        state.raise_issue(Exception("Expected exponentiation"), state)
        return ParseResult(state, ParseResultType.FAILURE, None, state)

    rest_part = get_zero_or_more(
        start_part.next, parse_multiplication_or_division_part)

    if rest_part.type == ParseResultType.FAILURE:
        return ParseResult(state, ParseResultType.FAILURE, None, state)

    rest: list[parser_node.MultiplicationOrDivisionPart] = []

    for part in rest_part.value:
        if part.value is not None:
            rest.append(part.value)

    return ParseResult(state, ParseResultType.SUCCESS, parser_node.MultiplicationOrDivision(start_part.value, rest), rest_part.next)


def parse_exponentiation_part(state: ParseState):
    leading_whitespace_part = get_zero_or_more(
        state, lambda x: x.get_whitespace())

    # did it match?
    if leading_whitespace_part.type == ParseResultType.FAILURE:
        return ParseResult(state, ParseResultType.FAILURE, None, state)

    operator_part = leading_whitespace_part.next.get_char('*')

    # did it match?
    if operator_part.type == ParseResultType.FAILURE:
        leading_whitespace_part.next.raise_issue(
            Exception("Expected '**'"), state)
        return ParseResult(state, ParseResultType.FAILURE, None, state)

    operator_part2 = operator_part.next.get_char('*')

    # did it match?
    if operator_part2.type == ParseResultType.FAILURE:
        operator_part.next.raise_issue(
            Exception("Expected '*'"), state)
        return ParseResult(state, ParseResultType.FAILURE, None, state)

    whitespace_part = get_zero_or_more(
        operator_part2.next, lambda x: x.get_whitespace())

    # did it match?
    if whitespace_part.type == ParseResultType.FAILURE:
        return ParseResult(state, ParseResultType.FAILURE, None, state)

    right_part = parse_numeric(whitespace_part.next)

    # did it match?
    if right_part.type == ParseResultType.FAILURE or right_part.value is None:
        whitespace_part.next.raise_issue(Exception("Expected numeric"), state)
        return ParseResult(state, ParseResultType.FAILURE, None, state)

    return ParseResult(state, ParseResultType.SUCCESS, parser_node.ExponentiationPart(operator_part.value, right_part.value), right_part.next)


def parse_exponentiation(state: ParseState):
    """
    Exponentiation -> Numeric (\\s* '**' \\s* Numeric)*
    """
    start_part = parse_numeric(state)

    if start_part.type == ParseResultType.FAILURE or start_part.value is None:
        state.raise_issue(Exception("Expected numeric"), state)
        return ParseResult(state, ParseResultType.FAILURE, None, state)

    rest_part = get_zero_or_more(
        start_part.next, parse_exponentiation_part)

    if rest_part.type == ParseResultType.FAILURE:
        return ParseResult(state, ParseResultType.FAILURE, None, state)

    rest: list[parser_node.ExponentiationPart] = []

    for part in rest_part.value:
        if part.value is not None:
            rest.append(part.value)

    return ParseResult(state, ParseResultType.SUCCESS, parser_node.Exponentiation(start_part.value, rest), rest_part.next)


@debug_wrapper
def parse_numeric(state: ParseState):
    """
    Numeric -> Number | ParenGroup
    """
    number_part = parse_number(state)

    if number_part.type == ParseResultType.FAILURE or number_part.value is None:
        paren_group_part = parse_paren_group(state)

        if paren_group_part.type == ParseResultType.FAILURE or paren_group_part.value is None:
            state.raise_issue(
                Exception("Expected number or paren group"), state)
            return ParseResult(state, ParseResultType.FAILURE, None, state)
        else:
            return ParseResult(state, ParseResultType.SUCCESS, parser_node.Numeric(paren_group_part.value), paren_group_part.next)
    else:
        return ParseResult(state, ParseResultType.SUCCESS, parser_node.Numeric(number_part.value), number_part.next)


@debug_wrapper
def parse_number(state: ParseState):
    """
    Number -> Float | Integer
    """
    # part = get_choose(state,
    #                   lambda x: parse_integer(x),
    #                   lambda x: parse_float(x))

    float_part = parse_float(state)

    if float_part.type == ParseResultType.FAILURE or float_part.value is None:
        integer_part = parse_integer(state)

        if integer_part.type == ParseResultType.FAILURE or integer_part.value is None:
            state.raise_issue(Exception("Expected float or integer"), state)
            return ParseResult(state, ParseResultType.FAILURE, None, state)
        else:
            return ParseResult(state, ParseResultType.SUCCESS, parser_node.Number(integer_part.value), integer_part.next)
    else:
        return ParseResult(state, ParseResultType.SUCCESS, parser_node.Number(float_part.value), float_part.next)


@debug_wrapper
def parse_integer(state: ParseState):
    """
    Integer -> Digit+
    """
    # Get the parts
    integer_parts = get_one_or_more(state, lambda x: x.get_digit())

    # did it match?
    if integer_parts.type == ParseResultType.FAILURE or integer_parts.value is None:
        state.raise_issue(Exception("Expected one or more digits"), state)
        return ParseResult(state, ParseResultType.FAILURE, None, state)
        # raise Exception("Expected digit after")

    # join the list and parse it as an integer
    values: list[source_lexer.LexerToken] = []

    for part in integer_parts.value:
        if part.value is not None:
            values.append(part.value)

    value = int(''.join([part.token.c for part in values]))
    return ParseResult(state, ParseResultType.SUCCESS, parser_node.Integer(value), integer_parts.next)


@debug_wrapper
def parse_float(state: ParseState):
    """
    Float -> Digit+ '.' Digit+
    """
    # Get the parts
    integer_parts = get_one_or_more(state, lambda x: x.get_digit())

    # did it match?
    if integer_parts.type == ParseResultType.FAILURE or integer_parts.value == None:
        state.raise_issue(Exception("Expected one or more digits"), state)
        return ParseResult(state, ParseResultType.FAILURE, None, state)

    decimal_part = integer_parts.next.get_char('.')

    # did it match?
    if decimal_part.type == ParseResultType.FAILURE:
        integer_parts.next.raise_issue(Exception("Expected '.'"), state)
        return ParseResult(state, ParseResultType.FAILURE, None, state)

    # Get the parts
    remainder_parts = get_one_or_more(
        decimal_part.next, lambda x: x.get_digit())

    # did it match?
    if remainder_parts.type == ParseResultType.FAILURE or remainder_parts.value == None:
        decimal_part.next.raise_issue(
            Exception("Expected one or more digits"), state)
        return ParseResult(state, ParseResultType.FAILURE, None, state)

    # join the parts and parse it as an integer
    integer_values: list[source_lexer.LexerToken] = []

    for part in integer_parts.value:
        if part.value is not None:
            integer_values.append(part.value)

    remainder_values: list[source_lexer.LexerToken] = []

    for part in remainder_parts.value:
        if part.value is not None:
            remainder_values.append(part.value)

    value = float(''.join([part.token.c for part in integer_values]) +
                  '.' + ''.join([part.token.c for part in remainder_values]))
    return ParseResult(state, ParseResultType.SUCCESS, parser_node.Float(value), remainder_parts.next)


@debug_wrapper
def parse_paren_group(state: ParseState):
    """
    ParenGroup -> '(' \\s* BitwiseShift \\s* ')'
    """
    open_paren_part = state.get_char('(')

    # did it match?
    if open_paren_part.type == ParseResultType.FAILURE:
        state.raise_issue(Exception("Expected '('"), state)
        return ParseResult(state, ParseResultType.FAILURE, None, state)

    leading_whitespace_part = get_zero_or_more(
        open_paren_part.next, lambda x: x.get_whitespace())

    # did it match?
    if leading_whitespace_part.type == ParseResultType.FAILURE:
        return ParseResult(state, ParseResultType.FAILURE, None, state)

    content = parse_bitwise_shift(leading_whitespace_part.next)

    # did it match?
    if content.type == ParseResultType.FAILURE or content.value is None:
        leading_whitespace_part.next.raise_issue(
            Exception("Expected bitwise shift"), state)
        return ParseResult(state, ParseResultType.FAILURE, None, state)

    trailing_whitespace_part = get_zero_or_more(
        content.next, lambda x: x.get_whitespace())

    # did it match?
    if trailing_whitespace_part.type == ParseResultType.FAILURE:
        return ParseResult(state, ParseResultType.FAILURE, None, state)

    close_paren_part = trailing_whitespace_part.next.get_char(')')

    # did it match?
    if close_paren_part.type == ParseResultType.FAILURE:
        trailing_whitespace_part.next.raise_issue(
            Exception("Expected ')'"), state)
        return ParseResult(state, ParseResultType.FAILURE, None, state)

    return ParseResult(state, ParseResultType.SUCCESS, parser_node.ParenGroup(content.value), close_paren_part.next)


def parse(lexer_tokens: list[source_lexer.LexerToken]):
    """
    Parse the lexed tokens into an AST
    """
    state = ParseState(lexer_tokens)
    return parse_expresion(state)

from typing import Optional, Union
from functools import reduce

# import input_tokens
import source_lexer

"""
Expresion -> '=' AdditionOrSubtraction $
AdditionOrSubtraction -> MultiplicationOrDivision (('+' | '-') MultiplicationOrDivision)*
MultiplicationOrDivision -> Numeric (('*' | '/' | '%') Numeric)*
Numeric -> Number | ParenGroup
Number -> Float | Integer
Integer -> Digit+
Float -> Digit+ '.' Digit+
ParenGroup -> '(' AdditionOrSubtraction ')'
"""


class ExecNode:
    def __init__(self) -> None:
        pass

    def exec(self) -> Optional[int | float]:
        return None

    def __str__(self) -> str:
        return f"exec()"


class Expresion(ExecNode):
    value: 'AdditionOrSubtraction'

    def __init__(self, value: 'AdditionOrSubtraction') -> None:
        super().__init__()
        self.value = value

    def exec(self) -> Optional[int | float]:
        return self.value.exec()

    def __str__(self) -> str:
        return f"Expresion({self.value})"


class AdditionOrSubtractionPart:
    operator: source_lexer.LexerToken
    right: 'MultiplicationOrDivision'

    def __init__(self, operator: source_lexer.LexerToken, right: 'MultiplicationOrDivision') -> None:
        super().__init__()
        self.operator = operator
        self.right = right

    def exec_part(self, left_value: Optional[int | float]) -> Optional[int | float]:
        right_value = self.right.exec()

        if left_value is not None and right_value is not None:
            if self.operator.plus:
                return left_value + right_value
            elif self.operator.minus:
                return left_value - right_value
            else:
                raise Exception("Unknown operator type encountered")
        elif left_value is None:
            raise Exception("left operand returned None")
        else:
            raise Exception("right operand returned None")

    def __str__(self) -> str:
        return f"{self.operator}({self.right})"


class AdditionOrSubtraction(ExecNode):
    start: 'MultiplicationOrDivision'
    rest: list[AdditionOrSubtractionPart]

    def __init__(self, start: 'MultiplicationOrDivision', rest: list[AdditionOrSubtractionPart]) -> None:
        super().__init__()
        self.start = start
        self.rest = rest

    def exec(self) -> Optional[int | float]:
        result = reduce(lambda x, y: y.exec_part(x),
                        self.rest, self.start.exec())
        return result

    def __str__(self) -> str:
        return f"AdditionOrSubtraction({self.start}{',' if len(self.rest) > 0 else ''}{','.join([str(part) for part in self.rest])})"


class MultiplicationOrDivisionPart:
    operator: source_lexer.LexerToken
    right: 'Numeric'

    def __init__(self, operator: source_lexer.LexerToken, right: 'Numeric') -> None:
        super().__init__()
        self.operator = operator
        self.right = right

    def exec_part(self, left_value: Optional[int | float]) -> Optional[int | float]:
        right_value = self.right.exec()

        if left_value is not None and right_value is not None:
            if self.operator.multiply:
                return left_value * right_value
            elif self.operator.divide:
                return left_value / right_value
            elif self.operator.percent:
                return left_value % right_value
            else:
                raise Exception("Unknown operator type encountered")
        elif left_value is None:
            raise Exception("left operand returned None")
        else:
            raise Exception("right operand returned None")

    def __str__(self) -> str:
        return f"{self.operator}({self.right})"


class MultiplicationOrDivision(ExecNode):
    start: 'Numeric'
    rest: list[MultiplicationOrDivisionPart]

    def __init__(self, start: 'Numeric', rest: list[MultiplicationOrDivisionPart]) -> None:
        super().__init__()
        self.start = start
        self.rest = rest

    def exec(self) -> Optional[int | float]:
        result = reduce(lambda x, y: y.exec_part(x),
                        self.rest, self.start.exec())
        return result

    def __str__(self) -> str:
        return f"MultiplicationOrDivision({self.start}{',' if len(self.rest) > 0 else ''}{','.join([str(part) for part in self.rest])})"


class Numeric(ExecNode):
    number_or_paren_group: Union['Number', 'ParenGroup']

    def __init__(self, number_or_paren_group: Union['Number', 'ParenGroup']) -> None:
        super().__init__()
        self.number_or_paren_group = number_or_paren_group

    def exec(self) -> Optional[int | float]:
        return self.number_or_paren_group.exec()

    def __str__(self) -> str:
        return f"Numeric({self.number_or_paren_group})"


class Number(ExecNode):
    integer_or_float: Union['Integer', 'Float']

    def __init__(self, integer_or_float: Union['Integer', 'Float']) -> None:
        super().__init__()
        self.integer_or_float = integer_or_float

    def exec(self) -> Optional[int | float]:
        return self.integer_or_float.exec()

    def __str__(self) -> str:
        return f"Number({self.integer_or_float})"


class Integer(ExecNode):
    value: int

    def __init__(self, value: int) -> None:
        super().__init__()
        self.value = value

    def exec(self) -> Optional[int | float]:
        return self.value

    def __str__(self) -> str:
        return f"Integer({self.value})"


class Float(ExecNode):
    value: float

    def __init__(self, value: float) -> None:
        super().__init__()
        self.value = value

    def exec(self) -> Optional[int | float]:
        return self.value

    def __str__(self) -> str:
        return f"Float({self.value})"


class ParenGroup(ExecNode):
    content: AdditionOrSubtraction

    def __init__(self, content: AdditionOrSubtraction) -> None:
        super().__init__()
        self.content = content

    def exec(self) -> Optional[int | float]:
        return self.content.exec()

    def __str__(self) -> str:
        return f"({self.content})"

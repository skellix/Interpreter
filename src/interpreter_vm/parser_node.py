from typing import Union

import basic_interpreter.source_lexer as source_lexer
from stack_executer.stack_executer import *
import interpreter_vm.interpreter_operations as interpreter_operations

"""
Expresion -> '=' AdditionOrSubtraction $
AdditionOrSubtraction -> MultiplicationOrDivision (('+' | '-') MultiplicationOrDivision)*
MultiplicationOrDivision -> Exponentiation (('*' | '/' | '%') Exponentiation)*
Exponentiation -> Numeric ('**' Numeric)*
Numeric -> Number | ParenGroup
Number -> Float | Integer
Integer -> Digit+
Float -> Digit+ '.' Digit+
ParenGroup -> '(' AdditionOrSubtraction ')'
"""


class ExecNode:
    def __init__(self) -> None:
        pass

    def generate_opcodes(self, output: list[Operation]):
        pass

    def __str__(self) -> str:
        return f"exec()"


class Expresion(ExecNode):
    def __init__(self, value: 'AdditionOrSubtraction') -> None:
        super().__init__()
        self.value = value

    def generate_opcodes(self, output: list[Operation]):
        self.value.generate_opcodes(output)
        output.append(interpreter_operations.Return())

    def __str__(self) -> str:
        return f"Expresion({self.value})"


class AdditionOrSubtractionPart:
    def __init__(self, operator: source_lexer.LexerToken, right: 'MultiplicationOrDivision') -> None:
        super().__init__()
        self.operator = operator
        self.right = right

    def generate_opcodes(self, output: list[Operation]):
        self.right.generate_opcodes(output)

        if self.operator.plus:
            output.append(interpreter_operations.Add())
        elif self.operator.minus:
            output.append(interpreter_operations.Subtract())
        else:
            raise Exception("Unknown operator encountered in AdditionOrSubtractionPart")

    def __str__(self) -> str:
        return f"{self.operator}({self.right})"


class AdditionOrSubtraction(ExecNode):
    def __init__(self, start: 'MultiplicationOrDivision', rest: list[AdditionOrSubtractionPart]) -> None:
        super().__init__()
        self.start = start
        self.rest = rest

    def generate_opcodes(self, output: list[Operation]):
        self.start.generate_opcodes(output)

        for part in self.rest:
            part.generate_opcodes(output)

    def __str__(self) -> str:
        return f"AdditionOrSubtraction({self.start}{',' if len(self.rest) > 0 else ''}{','.join([str(part) for part in self.rest])})"


class MultiplicationOrDivisionPart:
    def __init__(self, operator: source_lexer.LexerToken, right: 'Exponentiation') -> None:
        super().__init__()
        self.operator = operator
        self.right = right

    def generate_opcodes(self, output: list[Operation]):
        self.right.generate_opcodes(output)

        if self.operator.multiply:
            output.append(interpreter_operations.Multiply())
        elif self.operator.divide:
            output.append(interpreter_operations.Divide())
        elif self.operator.percent:
            output.append(interpreter_operations.Modulus())
        else:
            raise Exception("Unknown operator encountered in MultiplicationOrDivisionPart")

    def __str__(self) -> str:
        return f"{self.operator}({self.right})"


class MultiplicationOrDivision(ExecNode):
    def __init__(self, start: 'Exponentiation', rest: list[MultiplicationOrDivisionPart]) -> None:
        super().__init__()
        self.start = start
        self.rest = rest

    def generate_opcodes(self, output: list[Operation]):
        self.start.generate_opcodes(output)

        for part in self.rest:
            part.generate_opcodes(output)

    def __str__(self) -> str:
        return f"MultiplicationOrDivision({self.start}{',' if len(self.rest) > 0 else ''}{','.join([str(part) for part in self.rest])})"


class ExponentiationPart:
    def __init__(self, operator: source_lexer.LexerToken, right: 'Numeric') -> None:
        super().__init__()
        self.operator = operator
        self.right = right

    def generate_opcodes(self, output: list[Operation]):
        # Right to left
        self.right.generate_opcodes(output)

        if self.operator.multiply:
            output.append(interpreter_operations.Multiply())
        elif self.operator.divide:
            output.append(interpreter_operations.Divide())
        elif self.operator.percent:
            output.append(interpreter_operations.Modulus())
        else:
            raise Exception("Unknown operator encountered in ExponentiationPart")

    def __str__(self) -> str:
        return f"{self.operator}({self.right})"


class Exponentiation(ExecNode):
    def __init__(self, start: 'Numeric', rest: list[ExponentiationPart]) -> None:
        super().__init__()
        self.start = start
        self.rest = rest

    def generate_opcodes(self, output: list[Operation]):
        # Right to left
        (reversed_start, reversed_rest) = self.get_reversed_order()
        reversed_start.generate_opcodes(output)

        for part in reversed_rest:
            part.generate_opcodes(output)
    
    def get_reversed_order(self) -> tuple['Numeric', list[ExponentiationPart]]:
        if len(self.rest) == 0:
            return (self.start, [])
        
        start: Numeric = self.rest[-1].right
        rest: list[ExponentiationPart] = []
        previous_operator: source_lexer.LexerToken = self.rest[-1].operator
        
        for i, item in enumerate(self.rest):
            if i == 0:
                start = item.right
                previous_operator = item.operator
            else:
                rest.append(ExponentiationPart(previous_operator, item.right))
        
        rest.append(ExponentiationPart(previous_operator, self.start))

        return (start, rest)


    def __str__(self) -> str:
        return f"Exponentiation({self.start}{',' if len(self.rest) > 0 else ''}{','.join([str(part) for part in self.rest])})"


class Numeric(ExecNode):
    def __init__(self, number_or_paren_group: Union['Number', 'ParenGroup']) -> None:
        super().__init__()
        self.number_or_paren_group = number_or_paren_group

    def generate_opcodes(self, output: list[Operation]):
        self.number_or_paren_group.generate_opcodes(output)

    def __str__(self) -> str:
        return f"Numeric({self.number_or_paren_group})"


class Number(ExecNode):
    def __init__(self, integer_or_float: Union['Integer', 'Float']) -> None:
        super().__init__()
        self.integer_or_float = integer_or_float

    def generate_opcodes(self, output: list[Operation]):
        self.integer_or_float.generate_opcodes(output)

    def __str__(self) -> str:
        return f"Number({self.integer_or_float})"


class Integer(ExecNode):
    def __init__(self, value: int) -> None:
        super().__init__()
        self.value = value

    def generate_opcodes(self, output: list[Operation]):
        output.append(interpreter_operations.Integer(self.value))

    def __str__(self) -> str:
        return f"Integer({self.value})"


class Float(ExecNode):
    def __init__(self, value: float) -> None:
        super().__init__()
        self.value = value

    def generate_opcodes(self, output: list[Operation]):
        output.append(interpreter_operations.Float(self.value))

    def __str__(self) -> str:
        return f"Float({self.value})"


class ParenGroup(ExecNode):
    def __init__(self, content: AdditionOrSubtraction) -> None:
        super().__init__()
        self.content = content

    def generate_opcodes(self, output: list[Operation]):
        self.content.generate_opcodes(output)

    def __str__(self) -> str:
        return f"({self.content})"

def compile_node(node: ExecNode):
    output: list[Operation] = []
    node.generate_opcodes(output)
    return output
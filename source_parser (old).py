from typing import Optional, Union

# import input_tokens
import basic_interpreter.source_lexer as source_lexer

"""
Expresion -> '=' Numeric
MultiplicationOrDivision -> AdditionOrSubtraction (('*' | '/' | '%') AdditionOrSubtraction)*
AdditionOrSubtraction -> Numeric (('+' | '-') Numeric)*
Numeric -> Number | ParenGroup
Number -> Integer | Float
Integer -> Digit+
Float -> Digit+ '.' Digit+
ParenGroup -> '(' MultiplicationOrDivision ')'
"""

class ParserNode:
    token: source_lexer.LexerToken
    next: Optional['ParserNode']
    integer: Optional['IntegerNode'] = None
    zero_or_more_whitespace: Optional['ParserNode'] = None
    add_operator: Optional['AddOperatorNode'] = None
    lr_operator: Optional['LrOperatorNode'] = None
    expression: Optional['ExpressionNode'] = None
    
    def __init__(self, token: source_lexer.LexerToken) -> None:
        self.token = token

    def __str__(self) -> str:
        return f"node({self.token})"
    
class ExecutableNode:
    next: Optional['ParserNode'] = None

    def __init__(self) -> None:
        pass

    def exec(self) -> Optional[int]:
        return None

    def __str__(self) -> str:
        return f"node()"

class ExpressionNode(ExecutableNode):
    def __init__(self) -> None:
        super().__init__()

    def exec(self) -> Optional[int]:
        return 0

    def __str__(self) -> str:
        return f"expression()"

class IntegerNode(ExpressionNode):
    value: int

    def __init__(self) -> None:
        super().__init__()

    def exec(self):
        return self.value

    def __str__(self) -> str:
        return f"integer({self.value})"

class LrOperatorNode(ExpressionNode):
    left: ExpressionNode
    right: ExpressionNode

    def __init__(self) -> None:
        super().__init__()

    def exec(self) -> Optional[int]:
        return 0

    def __str__(self) -> str:
        return f"lr({self.left},{self.right})"

class AddOperatorNode(LrOperatorNode):
    def __init__(self) -> None:
        super().__init__()

    def exec(self) -> Optional[int]:
        left_result = self.left.exec()
        right_result = self.right.exec()

        if left_result is not None and right_result is not None:
            return left_result + right_result
        else:
            return None

    def __str__(self) -> str:
        return f"add({self.left},{self.right})"

class SubtractOperatorNode(LrOperatorNode):
    def __init__(self) -> None:
        super().__init__()

    def exec(self) -> Optional[int]:
        left_result = self.left.exec()
        right_result = self.right.exec()

        if left_result is not None and right_result is not None:
            return left_result - right_result
        else:
            return None

    def __str__(self) -> str:
        return f"subtract({self.left},{self.right})"
    
class AddOrSubtractOperatorNode(ExpressionNode):
    node: Union[AddOperatorNode, SubtractOperatorNode]

    def __init__(self) -> None:
        super().__init__()

    def exec(self) -> Optional[int]:
        return 0

    def __str__(self) -> str:
        return f"addOrSubtract({self.node})"

class AddOrSubtractListNode(ExpressionNode):
    items: list[AddOrSubtractOperatorNode]

    def __init__(self) -> None:
        super().__init__()

    def exec(self) -> Optional[int]:
        return 0

    def __str__(self) -> str:
        return f"addOrSubtractList({''.join([str(item) for item in self.items])})"

def parse_integer(parser_node: ParserNode) -> Optional[IntegerNode]:
    result = IntegerNode()
    current_node = parser_node
    digits: list[str] = []

    while current_node.token.digit and current_node.next is not None:
        # print(f"appending {current_node.token}")
        digits.append(current_node.token.token.c)
        current_node = result.next = current_node.next
    
    if len(digits) == 0:
        return None

    try:
        result.value = int(''.join(digits))
    except ValueError as e:
        print(f'Unable to convert digits to integer at {parser_node.token.token.offset}')
        raise e
    
    return result

def parse_zero_or_more_whitespace(parser_node: ParserNode) -> Optional[ParserNode]:
    current_node = parser_node

    while current_node.token.whitespace and current_node.next is not None:
        current_node = parser_node.zero_or_more_whitespace = current_node.next

    return current_node

def parse(lexer_tokens: list[source_lexer.LexerToken]) -> list[ParserNode]:
    parser_nodes = [ParserNode(token) for token in lexer_tokens]
    
    next: Optional[ParserNode] = None

    for i in range(len(parser_nodes) - 1, -1, -1):
        parser_node = parser_nodes[i]
        parser_node.next = next

        parser_node.integer = parse_integer(parser_node)
        parser_node.zero_or_more_whitespace = parse_zero_or_more_whitespace(parser_node)

        next = parser_node
        # print(f"{i} = {parser_node}")
    
    return parser_nodes
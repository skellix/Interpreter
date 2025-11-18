from stack_executer.stack_executer import *


class Add(Operation):
    def __init__(self) -> None:
        super().__init__()

    def eval(self, state: State) -> None:
        right_value = state.pop_result()

        if not isinstance(right_value, int) and not isinstance(right_value, float):
            raise Exception("Expected right operand of Add to be a Number")

        left_value = state.pop_result()

        if not isinstance(left_value, int) and not isinstance(left_value, float):
            raise Exception("Expected left operand of Add to be a Number")

        state.push_result(left_value + right_value)

    def __str__(self) -> str:
        return f"Add"


class Subtract(Operation):
    def __init__(self) -> None:
        super().__init__()

    def eval(self, state: State) -> None:
        right_value = state.pop_result()

        if not isinstance(right_value, int) and not isinstance(right_value, float):
            raise Exception(
                "Expected right operand of Subtract to be a Number")

        left_value = state.pop_result()

        if not isinstance(left_value, int) and not isinstance(left_value, float):
            raise Exception("Expected left operand of Subtract to be a Number")

        state.push_result(left_value - right_value)

    def __str__(self) -> str:
        return f"Subtract"


class Multiply(Operation):
    def __init__(self) -> None:
        super().__init__()

    def eval(self, state: State) -> None:
        right_value = state.pop_result()

        if not isinstance(right_value, int) and not isinstance(right_value, float):
            raise Exception(
                "Expected right operand of Multiply to be a Number")

        left_value = state.pop_result()

        if not isinstance(left_value, int) and not isinstance(left_value, float):
            raise Exception("Expected left operand of Multiply to be a Number")

        state.push_result(left_value * right_value)

    def __str__(self) -> str:
        return f"Multiply"


class Divide(Operation):
    def __init__(self) -> None:
        super().__init__()

    def eval(self, state: State) -> None:
        right_value = state.pop_result()

        if not isinstance(right_value, int) and not isinstance(right_value, float):
            raise Exception("Expected right operand of Divide to be a Number")

        left_value = state.pop_result()

        if not isinstance(left_value, int) and not isinstance(left_value, float):
            raise Exception("Expected left operand of Divide to be a Number")

        state.push_result(left_value / right_value)

    def __str__(self) -> str:
        return f"Divide"


class Modulus(Operation):
    def __init__(self) -> None:
        super().__init__()

    def eval(self, state: State) -> None:
        right_value = state.pop_result()

        if not isinstance(right_value, int) and not isinstance(right_value, float):
            raise Exception("Expected right operand of Modulus to be a Number")

        left_value = state.pop_result()

        if not isinstance(left_value, int) and not isinstance(left_value, float):
            raise Exception("Expected left operand of Modulus to be a Number")

        state.push_result(left_value % right_value)

    def __str__(self) -> str:
        return f"Modulus"


class LeftShift(Operation):
    def __init__(self) -> None:
        super().__init__()

    def eval(self, state: State) -> None:
        right_value = state.pop_result()

        if not isinstance(right_value, int):
            raise Exception(
                "Expected right operand of LeftShift to be an Integer")

        left_value = state.pop_result()

        if not isinstance(left_value, int):
            raise Exception(
                "Expected left operand of LeftShift to be an Integer")

        state.push_result(left_value << right_value)

    def __str__(self) -> str:
        return f"LeftShift"


class RightShift(Operation):
    def __init__(self) -> None:
        super().__init__()

    def eval(self, state: State) -> None:
        right_value = state.pop_result()

        if not isinstance(right_value, int):
            raise Exception(
                "Expected right operand of RightShift to be an Integer")

        left_value = state.pop_result()

        if not isinstance(left_value, int):
            raise Exception(
                "Expected left operand of RightShift to be an Integer")

        state.push_result(left_value >> right_value)

    def __str__(self) -> str:
        return f"RightShift"


class Integer(Operation):
    def __init__(self, value: int) -> None:
        super().__init__()
        self.value = value

    def eval(self, state: State) -> None:
        state.push_result(self.value)

    def __str__(self) -> str:
        return f"Integer {self.value}"


class Float(Operation):
    def __init__(self, value: float) -> None:
        super().__init__()
        self.value = value

    def eval(self, state: State) -> None:
        state.push_result(self.value)

    def __str__(self) -> str:
        return f"Float {self.value}"


class Return(Operation):
    def __init__(self) -> None:
        super().__init__()

    def eval(self, state: State) -> None:
        if state.callStack is None:
            raise Exception("The code is not running")

        # result = state.callStack.resultStack.pop()
        state.callStack = state.callStack.next

        if state.callStack is None:
            state.running = False
            # state.push_result(result)
        else:
            ...

    def __str__(self) -> str:
        return f"Return"


def code_to_string(code: list[Operation]):
    index_width = len(str(len(code)))
    return "\n".join([f"  {str(i).rjust(index_width, " ")}: {step}" for i, step in enumerate(code)])

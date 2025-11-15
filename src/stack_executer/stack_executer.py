from typing import Any, Callable, Optional


class Locals(dict[str, Any]):
    def __init__(self):
        super().__init__()

    def _(self):
        return self["_"]


class CallStackItem:
    def __init__(self, programIndex: int, next: Optional['CallStackItem'] = None):
        self.programIndex = programIndex
        self.resultStack: list[Any] = []
        self.locals = Locals()
        self.next = next


Breakpoint = Callable[['State', Callable[[], None]], None]


class Operation:
    def __init__(self) -> None:
        pass

    def eval(self, state: State) -> None:
        pass


class State:
    def __init__(self, code: list[Operation]):
        self.code = code
        self.env: Locals = Locals()
        self.callStack: Optional[CallStackItem] = None
        self.resultStack: list[Any] = []
        self.breakpoints: list[list[list[Breakpoint]]] = []
        self.running: bool = False

    def init_code_start(self):
        self.running = True
        self.push_call(-1)

    def push_call(self, programIndex: int):
        self.callStack = CallStackItem(programIndex, self.callStack)

    def pop_call(self):
        self.callStack = self.callStack.next if self.callStack is not None else None

    def push_result(self, result: Any):
        self.resultStack.append(result)
    
    def pop_result(self):
        try:
            return self.resultStack.pop()
        except IndexError:
            raise Exception("Stack index underflow")
    
    def move_to_next_operation(self):
        if self.callStack is None:
            raise Exception("The code is not running")
        
        self.callStack.programIndex += 1
    
    def get_operation(self):
        if self.callStack is None:
            raise Exception("The code is not running")
        
        return self.code[self.callStack.programIndex]
    
    def line_string(self):
        if self.callStack is None:
            raise Exception("The code is not running")

        return f"{self.callStack.programIndex}: {self.get_operation()}"

def execute_code(code: list[Operation]):
    state = State(code)
    state.init_code_start()

    while state.running:
        state.move_to_next_operation()
        operation = state.get_operation()

        print(state.line_string())

        try:
            operation.eval(state)
        except Exception as e:
            state.running = False
            print(f"Exception encountered while running: {e}")
    
    return state.resultStack.pop() if len(state.resultStack) > 0 else None
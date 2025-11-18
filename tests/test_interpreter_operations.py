import stack_executer.stack_executer as stack_executer
import interpreter_vm.interpreter_operations as interpreter_operations

def test_integer():
    target: int = 1
    operation = interpreter_operations.Integer(target)
    state = stack_executer.State([operation])
    state.init_code_start()
    operation.eval(state)

    assert len(state.resultStack) > 0

    result = state.resultStack.pop()
    assert isinstance(result, int)
    assert result == target


def test_float():
    target: float = 3.14
    operation = interpreter_operations.Float(target)
    state = stack_executer.State([operation])
    state.init_code_start()
    operation.eval(state)

    assert len(state.resultStack) > 0

    result = state.resultStack.pop()
    assert isinstance(result, float)
    assert result == target
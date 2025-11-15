import parser_operation

def test_getChar():
    result = parser_operation.rule("foo",
                      parser_operation.getChar("a"))
    
    assert isinstance(result.steps[0], parser_operation.TestCharacterOperation) and result.steps[0].target == "a"

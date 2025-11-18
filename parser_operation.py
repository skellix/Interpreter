from parser_base import *


class SuccessOperation(CompiledOperation):
    def eval(self, state: State):
        callStack = state.callStack

        if callStack is not None:
            stepStack = callStack.stepStack
            result = callStack.locals._

            if stepStack is not None:
                index = stepStack.index
                parser = state.parsers[callStack.parserIndex]
                rule = parser.rules[callStack.ruleIndex]

                callStack = state.callStack = callStack.next

                # resultIndex = index.indexes[rule.ruleName]
                resultIndex = stepStack.index.indexes[rule.qualifiedName]
                callStack.resultType = resultIndex.type = ResultType.Positive
                callStack.locals._ = resultIndex.result = result
                stepStack.index = resultIndex.next = index

                if index and index.index > state.longestMatchIndex:
                    state.longestMatchIndex = index.index
            else:
                state.resultType = ResultType.Positive
                state.result = result
                # state.resultIndex = index
        else:
            state.resultType = ResultType.Positive
            state.result = None
            # state.resultIndex = None

    def __str__(self):
        return "success"


class FailOperation(CompiledOperation):
    def eval(self, state: State):
        callStack = state.callStack

        if callStack is not None:
            stepStack = callStack.stepStack
            result = callStack.locals._

            if stepStack is not None:
                index = stepStack.index
                parser = state.parsers[callStack.parserIndex]
                rule = parser.rules[callStack.ruleIndex]

                callStack = state.callStack = callStack.next

                # resultIndex = index.indexes[rule.ruleName]
                resultIndex = stepStack.index.indexes[rule.qualifiedName]
                callStack.resultType = resultIndex.type = ResultType.Negative
                callStack.locals._ = resultIndex.result = result
                stepStack.index = resultIndex.next = index

                if index and index.index > state.longestMatchIndex:
                    state.longestMatchIndex = index.index
            else:
                state.resultType = ResultType.Negative
                state.result = result
                # state.resultIndex = index
        else:
            state.resultType = ResultType.Negative
            state.result = None
            # state.resultIndex = None

    def __str__(self):
        return "fail"


class ReturnOperation(CompiledOperation):
    def eval(self, state: State):
        callStack = state.callStack
        state.callStack = callStack.next if callStack is not None else None

    def __str__(self):
        return "return"


class TakeOperation(CompiledOperation):
    def eval(self, state: State):
        callStack = state.callStack

        if callStack is not None:
            stepStack = callStack.stepStack

            if stepStack is not None and state.callStack is not None and state.callStack.stepStack is not None:
                callStack.locals._ = stepStack.index.token

                if stepStack.index.next is not None:
                    stepStack = state.callStack.stepStack = StepStackItem(
                        stepStack.stepIndex + 1, stepStack.index.next, stepStack)
                    # callStack.locals._ = stepStack.index.token

    def __str__(self):
        return "take"


class JumpOperation(CompiledOperation):
    def __init__(self, targetIndex: int):
        super().__init__()
        self.targetIndex = targetIndex

    def eval(self, state: State):
        if state.callStack is not None and state.callStack.stepStack is not None:
            state.callStack.stepStack.stepIndex = self.targetIndex

    def offset(self, indexOffset: int):
        self.targetIndex += indexOffset

    def clone(self) -> CompiledOperation:
        return JumpOperation(self.targetIndex)

    def __str__(self):
        return f"jump {self.targetIndex}"


class JumpIfNegativeOperation(JumpOperation):
    def __init__(self, targetIndex: int):
        super().__init__(targetIndex)

    def eval(self, state: State):
        callStack = state.callStack

        if callStack is not None:
            stepStack = callStack.stepStack

            if stepStack is not None:
                if callStack.resultType == ResultType.Negative:
                    callStack.stepStack = StepStackItem(
                        self.targetIndex, stepStack.index, stepStack)
                else:
                    callStack.stepStack = StepStackItem(
                        stepStack.stepIndex + 1, stepStack.index, stepStack)

    def clone(self) -> CompiledOperation:
        return JumpIfNegativeOperation(self.targetIndex)

    def __str__(self):
        return f"jump if negative {self.targetIndex}"


class JumpLabel:
    def __init__(self, targetIndex: int = -1):
        self.targetIndex = targetIndex
        self.calls: list[JumpOperation] = []

    def jump(self):
        call = JumpOperation(self.targetIndex)
        self.calls.append(call)
        return call

    def jumpIfNegative(self):
        call = JumpIfNegativeOperation(self.targetIndex)
        self.calls.append(call)
        return call

    def setTargetIndex(self, targetIndex: int):
        self.targetIndex = targetIndex

        for call in self.calls:
            call.targetIndex = targetIndex


class SetOperation(CompiledOperation):
    def __init__(self, identifier: str):
        super().__init__()
        self.identifier = identifier

    def eval(self, state: State):
        callStack = state.callStack

        if callStack is not None and callStack.stepStack is not None:
            stepStack = callStack.stepStack

            callStack.locals[self.identifier] = callStack.locals._
            callStack.stepStack = StepStackItem(
                stepStack.stepIndex + 1, stepStack.index, stepStack)

    def __str__(self):
        return "set " + self.identifier


class TestCharacterOperation(CompiledOperation):
    def __init__(self, target: str):
        super().__init__()
        self.target = target

    def eval(self, state: State):
        if state.callStack is not None:
            callStack = state.callStack
            stepStack = callStack.stepStack

            if stepStack is not None:
                if stepStack.index.token == self.target:
                    callStack.resultType = ResultType.Positive
                    callStack.locals._ = stepStack.index.token
                else:
                    callStack.resultType = ResultType.Negative

                callStack.stepStack = StepStackItem(
                    stepStack.stepIndex + 1, stepStack.index, stepStack)

    def __str__(self):
        return f"test '{self.target}'"


class TestEndOperation(CompiledOperation):
    def __init__(self):
        super().__init__()

    def eval(self, state: State):
        if state.callStack is not None:
            callStack = state.callStack
            stepStack = callStack.stepStack

            if stepStack is not None:
                if stepStack.index.next is None:
                    callStack.resultType = ResultType.Positive
                    callStack.locals._ = stepStack.index.token
                else:
                    callStack.resultType = ResultType.Negative

                callStack.stepStack = StepStackItem(
                    stepStack.stepIndex + 1, stepStack.index, stepStack)

    def __str__(self):
        return f"test $"


class ZeroOrMoreInitOperation(CompiledOperation):
    def __init__(self):
        self.index: Index
        self.findMore: bool
        self.lastIndex: Optional[Index]

    def eval(self, state: State):
        self.index = state.index
        self.findMore = True
        self.lastIndex = None

        callStack = state.callStack

        if callStack is not None:
            stepStack = callStack.stepStack

            if stepStack is not None:
                callStack.stepStack = StepStackItem(
                    stepStack.stepIndex + 1, stepStack.index, stepStack)

    def __str__(self):
        return "zeroOrMore init"


class ZeroOrMoreTestOperation(CompiledOperation):
    def __init__(self):
        self.index: Index
        self.findMore: bool

    def eval(self, state: State):
        callStack = state.callStack

        if callStack is not None:
            parser = state.parsers[callStack.parserIndex]
            rule = parser.rules[callStack.ruleIndex]
            stepStack = callStack.stepStack

            if stepStack is not None:
                varContext = rule.steps[stepStack.stepIndex - 1]

                if isinstance(varContext, ZeroOrMoreInitOperation):
                    if varContext.findMore:
                        if varContext.lastIndex == stepStack.index:
                            state.running = False
                            raise Exception("Loop did not advance")

                        varContext.lastIndex = stepStack.index
                        callStack.resultType = ResultType.Positive
                        callStack.stepStack = StepStackItem(
                            stepStack.stepIndex + 1, stepStack.index, stepStack)

                    else:
                        varContext.lastIndex = None
                        callStack.resultType = ResultType.Negative
                        callStack.stepStack = StepStackItem(
                            stepStack.stepIndex + 1, stepStack.index, stepStack.next)

    def __str__(self):
        return "zeroOrMore test"


class FindMoreOperation(CompiledOperation):
    def eval(self, state: State):
        callStack = state.callStack

        if callStack is not None:
            parser = state.parsers[callStack.parserIndex]
            rule = parser.rules[callStack.ruleIndex]

            stepStack = callStack.stepStack

            if stepStack is not None:
                index = stepStack.index
                step = rule.steps[stepStack.stepIndex]

                while True:
                    if isinstance(step, ZeroOrMoreTestOperation):
                        varContext = rule.steps[stepStack.stepIndex - 1]

                        if isinstance(varContext, ZeroOrMoreInitOperation):
                            varContext.findMore = True
                            stepStack.index = index
                            break

                    else:
                        stepStack = stepStack.next

                    if stepStack is not None:
                        step = rule.steps[stepStack.stepIndex]
                    else:
                        break

                callStack.stepStack = stepStack

    def __str__(self):
        return "find more"


class NoMoreOperation(CompiledOperation):
    def eval(self, state: State):
        callStack = state.callStack

        if callStack is not None:
            parser = state.parsers[callStack.parserIndex]
            rule = parser.rules[callStack.ruleIndex]

            stepStack = callStack.stepStack

            if stepStack is not None:
                index = stepStack.index
                step = rule.steps[stepStack.stepIndex]

                while True:
                    if isinstance(step, ZeroOrMoreTestOperation):
                        varContext = rule.steps[stepStack.stepIndex - 1]

                        if isinstance(varContext, ZeroOrMoreInitOperation):
                            varContext.findMore = False
                            stepStack.index = index
                            break

                    else:
                        stepStack = stepStack.next

                    if stepStack is not None:
                        step = rule.steps[stepStack.stepIndex]
                    else:
                        break

                callStack.stepStack = stepStack

    def __str__(self):
        return "no more"


class CallOperation(CompiledOperation):
    def __init__(self, rulePath: list[str]):
        super().__init__()
        self.rulePath = rulePath
        self.parserIndex: int = -1
        self.ruleIndex: int = -1
        self.rule: Rule
        self.firstIndex: Index

    def eval(self, state: State):
        callStack = state.callStack

        if callStack is not None:
            stepStack = callStack.stepStack

            if stepStack is not None:
                if self.ruleIndex == -1:
                    ruleReference = resolveRuleFromPath(
                        state.parsers, callStack.parserIndex, callStack.ruleIndex, self.rulePath)
                    self.parserIndex = ruleReference.parserIndex
                    self.ruleIndex = ruleReference.ruleIndex
                    self.rule = ruleReference.rule

                index0 = stepStack.index
                result = index0.indexes[self.rule.qualifiedName]

                # heads = index0.heads

                # TODO: update parser to handle left recursion with the grow algorithm

                if result.type == ResultType.Unparsed:
                    result.type = ResultType.Parsing
                    result.next = index0
                    self.firstIndex = index0

                    if state.callStack is not None:
                        state.callStack.stepStack = StepStackItem(
                            stepStack.stepIndex + 1, stepStack.index, stepStack)

                        callStack = state.callStack = CallStackItem(
                            self.parserIndex, self.ruleIndex, callStack)
                        # callStack = state.callStack = CallStackItem()
                        state.callStack.stepStack = StepStackItem(
                            0, stepStack.index, callStack.stepStack)
                elif result.type == ResultType.Parsing:
                    raise Exception("grow needed, but not yet implemented")
                else:
                    if state.callStack is not None:
                        state.callStack.stepStack = StepStackItem(
                            stepStack.stepIndex + 1, result.next, stepStack)
                        state.callStack.locals["_"] = result.result
                        state.callStack.resultType = result.type

    def __str__(self):
        return "call " + ".".join(self.rulePath)


def resolveRuleFromPath(parsers: Parsers, startParserIndex: int, startRuleIndex: int, rulePath: list[str]) -> RuleReference:
    startParser = parsers[startParserIndex]

    if len(rulePath) == 0:
        startRule = startParser.rules[startRuleIndex]

        raise Exception("Empty path found in rule " + startRule.qualifiedName)

    currentParserIndex = startParserIndex
    currentParser = startParser
    currentPathIndex: int = 0

    while currentPathIndex < len(rulePath) - 1:
        pathItem = rulePath[currentPathIndex]

        if not pathItem in currentParser.importsMapping.keys():
            # if !(pathItem in currentParser.importsMapping):
            startRule = startParser.rules[startRuleIndex]

            raise Exception(
                f"Rule not found for path {".".join(rulePath)} in rule {startRule.qualifiedName}")

        nextParserIndex = currentParser.importsMapping[pathItem]

        if nextParserIndex >= len(parsers):
            raise Exception(
                f"Parser index out of range in import: {nextParserIndex} >= {len(parsers)}")

        nextParser = parsers[nextParserIndex]

        currentParser = nextParser
        currentParserIndex = nextParserIndex
        # ++ currentPathIndex
        currentPathIndex += 1

    lastPathItem = rulePath[currentPathIndex]
    resultRuleIndex: int = -1
    resultRule: Optional[Rule] = None

    for i, rule in enumerate(currentParser.rules):
        if rule.ruleName == lastPathItem:
            resultRuleIndex = i
            resultRule = rule
            break

    if resultRule is None:
        startRule = startParser.rules[startRuleIndex]

        raise Exception(
            f"Rule not found for path {".".join(rulePath)} in rule {startRule.qualifiedName}")

    return RuleReference(
        currentParserIndex,
        resultRuleIndex,
        currentParser,
        resultRule
    )


# IntermediateCall = Callable[[list[CompiledOperation], list[CompiledOperation], list[CompiledOperation]], None]
IntermediateCall = Callable[['IntermediateCall',
                             'IntermediateCall', list[CompiledOperation]], None]
# IntermediateCall = Callable[[list[CompiledOperation], list[CompiledOperation]], list[CompiledOperation]] | partial[list[CompiledOperation]]
# IntermediateCall = partial[list[CompiledOperation]]

# def _success() -> list[CompiledOperation]:
#     return [SuccessOperation()]


# def _fail() -> list[CompiledOperation]:
#     return [FailOperation()]


def noop() -> IntermediateCall:
    return lambda positive, negative, output: None


def success() -> IntermediateCall:
    def _success(positive: IntermediateCall, negative: IntermediateCall, output: list[CompiledOperation]):
        output.append(SuccessOperation())
    return _success


def fail() -> IntermediateCall:
    def _fail(positive: IntermediateCall, negative: IntermediateCall, output: list[CompiledOperation]):
        output.append(FailOperation())
    return _fail


# def doChoice(destination: list[CompiledOperation], positive: list[CompiledOperation], negative: list[CompiledOperation]):
#     fail_label = JumpLabel()
#     destination.append(fail_label.jumpIfNegative())
#     destination.extend(positive)
#     fail_label.setTargetIndex(len(destination))
#     destination.extend(negative)


def sequence(*steps: IntermediateCall) -> IntermediateCall:
    def _each(positive: IntermediateCall, negative: IntermediateCall, output: list[CompiledOperation]):
        fail_label = JumpLabel()

        for step in steps:
            after_step_label = JumpLabel()
            step(lambda positive, negative, output: output.append(after_step_label.jump(
            )), lambda positive, negative, output: output.append(fail_label.jump()), output)
            after_step_label.setTargetIndex(len(output))

        positive(noop(), noop(), output)
        fail_label.setTargetIndex(len(output))
        negative(noop(), noop(), output)
    return _each


def choose(*choices: IntermediateCall) -> IntermediateCall:
    def _choose(positive: IntermediateCall, negative: IntermediateCall, output: list[CompiledOperation]):
        success_label = JumpLabel()

        for choice in choices:
            after_choice_label = JumpLabel()
            choice(lambda positive, negative, output: output.append(success_label.jump(
            )), lambda positive, negative, output: output.append(after_choice_label.jump()), output)
            after_choice_label.setTargetIndex(len(output))

        negative(noop(), noop(), output)
        success_label.setTargetIndex(len(output))
        positive(noop(), noop(), output)
    return _choose


def optional(step: IntermediateCall) -> IntermediateCall:
    def _each(positive: IntermediateCall, negative: IntermediateCall, output: list[CompiledOperation]):
        after_step_label = JumpLabel()
        step(lambda positive, negative, output: output.append(after_step_label.jump()),
             lambda positive, negative, output: output.append(after_step_label.jump()), output)
        after_step_label.setTargetIndex(len(output))
        positive(noop(), noop(), output)
    return _each


def zeroOrMore(step: IntermediateCall) -> IntermediateCall:
    def _zeroOrMore(positive: IntermediateCall, negative: IntermediateCall, output: list[CompiledOperation]):
        output.append(ZeroOrMoreInitOperation())
        output.append(ZeroOrMoreTestOperation())

        end_label = JumpLabel()
        output.append(end_label.jumpIfNegative())

        step(lambda positive, negative, output: output.append(FindMoreOperation()),
             lambda positive, negative, output: output.append(NoMoreOperation()), output)

        end_label.setTargetIndex(len(output))
        positive(noop(), noop(), output)
    return _zeroOrMore


def oneOrMore(step: IntermediateCall) -> IntermediateCall:
    return sequence(step,
                    zeroOrMore(step))


def getChar(target: str):
    def _getChar(positive: IntermediateCall, negative: IntermediateCall, output: list[CompiledOperation]):
        fail_label = JumpLabel()

        output.append(TestCharacterOperation(target))
        output.append(fail_label.jumpIfNegative())
        output.append(TakeOperation())
        positive(noop(), noop(), output)
        fail_label.setTargetIndex(len(output))
        negative(noop(), noop(), output)
    return _getChar


def getEnd():
    def _getEnd(positive: IntermediateCall, negative: IntermediateCall, output: list[CompiledOperation]):
        fail_label = JumpLabel()

        output.append(TestEndOperation())
        output.append(fail_label.jumpIfNegative())
        # output.append(TakeOperation()) # we don't take the end token so we can check it again if we need
        positive(noop(), noop(), output)
        fail_label.setTargetIndex(len(output))
        negative(noop(), noop(), output)
    return _getEnd


def call(rulePath: list[str]):
    def _call(positive: IntermediateCall, negative: IntermediateCall, output: list[CompiledOperation]):
        output.append(CallOperation(rulePath))
        
        fail_label = JumpLabel()

        output.append(fail_label.jumpIfNegative())
        positive(noop(), noop(), output)
        fail_label.setTargetIndex(len(output))
        negative(noop(), noop(), output)
    return _call


def rule(name: str, *steps: IntermediateCall) -> Rule:
    result_steps: list[CompiledOperation] = []
    sequence(*steps)(success(), fail(), result_steps)

    return Rule(
        name,
        result_steps,
        name
    )


def generateTestParser():
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
    parser = NamedParser("testParser", [
        rule("Expresion",
             getChar("="),
             call(["AdditionOrSubtraction"]),
             getEnd()),
        rule("AdditionOrSubtraction",
             call(["MultiplicationOrDivision"]),
             zeroOrMore(
                 sequence(
                     choose(
                         getChar("+"),
                         getChar("-")),
                     call(["MultiplicationOrDivision"])))),
        rule("MultiplicationOrDivision",
             call(["Numeric"]),
             zeroOrMore(
                 sequence(
                     choose(
                         getChar("*"),
                         getChar("/"),
                         getChar("%")),
                     call(["Numeric"])))),
        rule("Numeric",
             choose(
                 call(["Number"]),
                 call(["ParenGroup"]))),
        rule("Number",
             choose(
                 call(["Float"]),
                 call(["Integer"]))),
        rule("Integer",
             oneOrMore(
                 choose(
                     getChar("0"),
                     getChar("1"),
                     getChar("2"),
                     getChar("3"),
                     getChar("4"),
                     getChar("5"),
                     getChar("6"),
                     getChar("7"),
                     getChar("8"),
                     getChar("9")))),
        rule("Float",
             oneOrMore(
                 choose(
                     getChar("0"),
                     getChar("1"),
                     getChar("2"),
                     getChar("3"),
                     getChar("4"),
                     getChar("5"),
                     getChar("6"),
                     getChar("7"),
                     getChar("8"),
                     getChar("9"))),
             getChar("."),
             oneOrMore(
                 choose(
                     getChar("0"),
                     getChar("1"),
                     getChar("2"),
                     getChar("3"),
                     getChar("4"),
                     getChar("5"),
                     getChar("6"),
                     getChar("7"),
                     getChar("8"),
                     getChar("9")))),
        rule("ParenGroup",
             getChar("("),
             call(["AdditionOrSubtraction"]),
             getChar(")"))
    ])

    return parser


def test():
    def testGetChar():
        result = rule("foo",
                      getChar("a"))

        print(result)

    def testOptional():
        result = rule("foo",
                      optional(getChar("a")))

        print(result)

    def testChoose():
        result = rule("foo",
                      choose(
                          getChar("a"),
                          getChar("b")))

        print(result)

    for test in [testGetChar, testOptional, testChoose]:
        try:
            print(f"[testing {test.__name__}...]")
            test()
            print(f"[test {test.__name__} success]")
        except Exception:
            print(f"[test {test.__name__} failed]")


if __name__ == "__main__":
    test()

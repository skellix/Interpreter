from enum import Enum
from typing import Any, Callable, Optional


InvolvedSet = list['Rule']


class Head:
    def __init__(self, rule: 'Rule'):
        self.rule = rule
        self.heads: list[InvolvedSet] = []
        self.evalSet: list['Rule'] = []


class CallStack:

    def __init__(self, rule: 'Rule', next: 'CallStack'):
        self.rule = rule
        self.next = next


RuleIndexes = dict[str, 'RuleIndex']


class Index:
    def __init__(self, index: int, token: Any, line: int, column: int):
        self.callStack: Optional[CallStack] = None
        self.heads: Optional[Head] = None

        self.indexes: RuleIndexes = {}

        self.index = index
        self.token = token
        self.line = line
        self.column = column
        self.next: Optional['Index']


class ResultType(Enum):
    Unparsed = 0
    Parsing = 1
    Positive = 2
    Negative = 3


class RuleIndex:
    def __init__(self,
                 head: Head,
                 result: Any,
                 next: Index):
        self.head = head
        self.type: ResultType = ResultType.Unparsed
        self.result = result
        self.next = next


class Rule:
    def __init__(self,
                 ruleName: str,
                 steps: list['CompiledOperation'],
                 qualifiedName: str,
                 growRuleIndex: Optional[int] = None,
                 sourceName: Optional[str] = None,
                 source: Optional[str] = None,
                 sourceMapping: list['SourceMapping'] = []):
        self.ruleName = ruleName
        self.steps = steps
        self.qualifiedName = qualifiedName
        self.growRuleIndex = growRuleIndex
        self.sourceName = sourceName
        self.source = source
        self.sourceMapping = sourceMapping

    def __str__(self) -> str:
        index_width = len(str(len(self.steps)))
        return f"rule {self.qualifiedName}:\n{"\n".join([f"  {str(i).rjust(index_width, " ")}: {step}" for i, step in enumerate(self.steps)])}"


Rules = list[Rule]


class NamedParser:
    def __init__(self, parserName: str, rules: Rules):
        self.parserName = parserName
        self.rules = rules
        self.importsMapping: dict[str, int] = {}
        self.qualifiedName = parserName


Parsers = list[NamedParser]


class StepStackItem:
    def __init__(self, stepIndex: int, index: Index, next: Optional['StepStackItem']):
        self.stepIndex = stepIndex
        self.index = index
        self.next = next


class Locals(dict[str, Any]):
    def __init__(self):
        super().__init__()

    def _(self):
        return self["_"]


class CallStackItem:
    def __init__(self, parserIndex: int, ruleIndex: int, next: 'CallStackItem'):
        self.parserIndex = parserIndex
        self.ruleIndex = ruleIndex
        self.operationIndex: int = 0

        self.resultType: ResultType = ResultType.Negative
        self.locals = Locals()

        self.stepStack: Optional[StepStackItem] = None
        self.next = next


Breakpoint = Callable[['State', Callable[[], None]], None]


class State:
    def __init__(self):
        self.parsers: Parsers
        self.env: Locals
        # self.rules: Parser
        self.index: Index
        self.callStack: Optional[CallStackItem] = None
        self.result: Any
        self.resultType: ResultType = ResultType.Negative
        self.resultIndex: Index
        self.breakpoints: list[list[list[Breakpoint]]]
        self.running = True
        self.longestMatchIndex: int


class CompiledOperation:
    def eval(self, state: State):
        ...

    def clone(self) -> 'CompiledOperation':
        ...

    def offset(self, indexOffset: int):
        ...

class RuleReference:
    def __init__(self,
                 parserIndex: int,
                 ruleIndex: int,
                 parser: NamedParser,
                 rule: Rule):
        self.parserIndex = parserIndex
        self.ruleIndex = ruleIndex
        self.parser = parser
        self.rule = rule


class SourceMapping(list[CompiledOperation]):
    def __init__(self, line: Optional[int] = None, column: Optional[int] = None, operations: Optional[list[CompiledOperation]] = None):
        super().__init__()
        self.offset: int
        self.line: Optional[int]
        self.column: Optional[int]
        self.children: list['SourceMapping']

        if operations is not None and isinstance(operations, 'SourceMapping'):
            operations.offset = 0
            operations.line = line
            operations.column = column

            return operations

        else:
            self.offset = 0
            self.line = line
            self.column = column
            self.children = []

            if operations is not None:
                for operation in operations:
                    self.insert(0, operation)

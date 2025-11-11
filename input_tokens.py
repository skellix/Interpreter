class InputToken:
    """
    This is the basic input token that our syntax will process
    """

    c: str
    offset: int

    def __init__(self, c: str, offset: int) -> None:
        self.c = c
        self.offset = offset

    def __str__(self) -> str:
        return f"{self.offset}:{self.c}"


class EndOfStream(InputToken):
    """
    This token represents the end of the input stream
    """
    def __init__(self, offset: int) -> None:
        super().__init__("", offset)


def tokenize(source: str) -> list[InputToken]:
    """
    Convert the source into a list of input tokens for processing
    """
    result = [InputToken(c, offset) for offset, c in enumerate(source)]
    result.append(EndOfStream(len(source)))
    return result

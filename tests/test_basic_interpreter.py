from io import SEEK_SET, SEEK_END

import basic_interpreter.input_tokens as input_tokens
import basic_interpreter.source_lexer as source_lexer
import basic_interpreter.source_parser as source_parser

def read_source(source_name: str) -> str:
    with open(source_name) as file:
        file_end = file.seek(0, SEEK_END)
        file.seek(0, SEEK_SET)
        return file.read(file_end + 1)

def test():
    # print("Reading source")
    source_name = "src.src"
    source = read_source(source_name)

    tokens = input_tokens.tokenize(source)
    # [print(input_token) for input_token in tokens]

    lexer_tokens = source_lexer.lex(tokens)
    # [print(lexer_token) for lexer_token in lexer_tokens]

    parser_result = source_parser.parse(lexer_tokens)

    if parser_result.type != source_parser.ParseResultType.SUCCESS or parser_result.value is None:
        print("parse failed")
        print("issues:")
        [print(issue) for issue in parser_result.start.get_last_issues()]
        return

    print("parse result:")
    print(parser_result.value)

    # print("issues:")
    # [print(issue) for issue in parser_result.start.issues.issues]

    print("running...")
    run_result = parser_result.value.exec()

    print(f"result: {run_result}")
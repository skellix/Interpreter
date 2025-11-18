from io import SEEK_SET, SEEK_END

import basic_interpreter.input_tokens as input_tokens
import basic_interpreter.source_lexer as source_lexer
import interpreter_vm.source_parser as source_parser
import interpreter_vm.parser_node as parser_node
import interpreter_vm.interpreter_operations as interpreter_operations
import stack_executer.stack_executer as stack_executer


def read_source(source_name: str) -> str:
    with open(source_name) as file:
        file_end = file.seek(0, SEEK_END)
        file.seek(0, SEEK_SET)
        return file.read(file_end + 1)


def main():
    # print("Reading source")
    source_name = "src2.src"
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

    print("compiling...")
    code = parser_node.compile_node(parser_result.value)

    print(interpreter_operations.code_to_string(code))

    print("running...")

    run_result = stack_executer.execute_code(code)

    print(f"result: {run_result}")


if __name__ == "__main__":
    main()

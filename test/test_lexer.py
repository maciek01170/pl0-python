import utils
from lexer import lexer

if __name__ == "__main__":
    code = utils.get_input()
    lexer.input(code)

    while True:
        tok = lexer.token()
        if not tok: break

        print(tok)

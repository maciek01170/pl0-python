import sys


def get_input():
    if len(sys.argv) <= 1:
        code = sys.stdin.read()
    else:
        with open(sys.argv[1]) as fp:
            code = fp.read()
    return code

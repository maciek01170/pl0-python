import lexer
import utils
from symtab import Symtab


class ParseError(Exception):
    pass

class SymbolParser:
    def __init__(self, lex):
        self.lex = lex
        self.sym = None
        self.source = None

    def input(self, data):
        self.source = "<input>"
        self.lex.input(data)
        self.sym = self.lex.token()

    def get_sym(self):
        # Get the next token
        self.sym = self.lex.token()
        return self.sym

    def is_sym(self, name):
        return self.sym and self.sym.type == name

    # Raises an exception if the current symbol is not the one expected.
    def expect_sym(self, name):
        if self.is_sym(name):
            return self.sym
        elif self.sym:
            args = (self.source, self.sym.lineno, self.sym.lexpos, name, self.sym.type, self.sym.value,)
            raise ParseError('%s[%d:%d]: Expected %s but got %s (%s)' % args)
        else:
            args = (self.source, self.lex.lineno, self.lex.lexpos, name,)
            raise ParseError('%s[%d:%d]: Expected %s but got none' % args)

    def required(self, result, name):
        if result:
            return result
        else:
            self.expect_sym("~%s" % name)


# program = block "." .
#
# block = [ "const" ident "=" number {"," ident "=" number} ";"]
#         [ "var" ident {"," ident} ";"]
#         { "procedure" (ident | ident "(" ident " {"," ident} ")" ";" block ";" } statement .
#
# statement = [ ident ":=" expression | "call" ident call_params|
#             "begin" statement {";" statement } "end" |
#             "if" condition "then" statement |
#             "while" condition "do" statement ].
#
# call_params  = empty | '(' expression { ',' expression } ')'
# condition = "odd" expression |
#             expression ("="|"#"|"<"|"<="|">"|">=") expression .
#
# expression = [ "+"|"-"] term { ("+"|"-") term}.
#
# term = factor {("*"|"/") factor}.
#
# factor = ident | number | "(" expression ")".

class Parser(SymbolParser):

    def __init__(self):
        SymbolParser.__init__(self, lexer.create())
        self.symtab = Symtab()

    def p_program(self):
        block = self.required(self.p_block(), 'block')
        self.expect_sym('DOT')
        self.get_sym()

        return 'PROGRAM', block,

    def p_block(self):
        const_decl = self.p_const_decl()
        var_decl = self.p_var_decl()
        procedures_decl = self.p_procedures_decl()
        statement = self.p_statement()

        return 'BLOCK', const_decl, var_decl, procedures_decl, statement,

    def p_const_decl(self):
        if self.is_sym('CONST'):
            constants = ['CONSTANTS']

            while True:
                const_def = (self.sym.name, 'CONST')
                self.get_sym()

                assignment = self.p_const_assign()

                if assignment:
                    constants.append(assignment)

                if self.is_sym('EOS'):
                    self.get_sym()
                    self.symtab.new_symbol(self.sym.value, const_def)
                    return constants

                self.expect_sym('COMMA')
        else:
            return None

    def p_const_assign(self):
        if self.is_sym('NAME'):
            name = self.sym.value

            self.get_sym()
            self.expect_sym('ASSIGN')

            self.get_sym()
            self.expect_sym('NUMBER')
            value = self.sym.value

            self.get_sym()

            return 'DEFINE', name, value,
        else:
            return None

    def p_var_decl(self):
        if self.is_sym('VAR'):
            names = ['VARIABLES']

            while True:
                self.get_sym()
                self.expect_sym('NAME')

                names.append(('NAME', self.sym.value,))

                self.get_sym()

                if self.is_sym('EOS'):
                    self.get_sym()
                    return names

                self.expect_sym('COMMA')
        else:
            return None

    def p_procedure_decl_params(self):
        if self.is_sym('LPAREN'):
            params = ['PARAMETERS']
            self.get_sym()
            while True:
                self.expect_sym('NAME')
                params.append(('NAME', self.sym.value,))
                self.symtab.new_symbol(self.sym.value, params)

                self.get_sym()

                if self.is_sym('RPAREN'):
                    self.get_sym()
                    return params

                self.expect_sym('COMMA')
                self.get_sym()
        else:
            return None


    def p_procedures_decl(self):
        procedures = ['PROCEDURES']

        while self.is_sym('PROCEDURE'):
            self.symtab.new_frame()
            self.get_sym()
            self.expect_sym('NAME')
            name = self.sym.value

            self.get_sym()
            params = self.p_procedure_decl_params()
            self.symtab.new_symbol(('PROCEDURE', (name, len(params) if params else 0), ),name)

            self.expect_sym('EOS')

            self.get_sym()
            block = self.p_block()

            self.expect_sym('EOS')

            if params:
                procedures.append(('PROCEDURE', name, params, block,))
            else:
                procedures.append(('PROCEDURE', name, block,))

            self.get_sym()

        if len(procedures) > 1:
            return procedures
        else:
            return None

    def p_statement(self):
        if self.is_sym('NAME'):
            return self.p_statement_assign()
        elif self.is_sym('CALL'):
            return self.p_statement_call()
        elif self.is_sym('BEGIN'):
            return self.p_statement_begin()
        elif self.is_sym('IF'):
            return self.p_statement_if()
        elif self.is_sym('WHILE'):
            return self.p_statement_while()
        elif self.is_sym('PRINT'):
            return self.p_statement_print()
        else:
            # Raise an exception since we didn't find a valid statement.
            self.expect_sym('~statement')

    def p_statement_assign(self):
        if self.is_sym('NAME'):
            name = ('NAME', self.sym.value,)

            self.get_sym()
            self.expect_sym('UPDATE')

            self.get_sym()
            expression = self.p_expression()

            return 'SET', name, expression,
        else:
            return None

    def p_statement_print(self):
        if self.is_sym('PRINT'):
            self.get_sym()

            expression = self.required(self.p_expression(), 'print-expression')

            return 'PRINT', expression
        else:
            return None

    def p_statement_call_params(self):
        if self.is_sym('LPAREN'):
            params = ['CALL_PARAMETERS']
            self.get_sym()
            while True:
                expr = self.required(self.p_expression(), 'expression')
                params.append(('PARAMETER', expr, ))

                if self.is_sym('RPAREN'):
                    self.get_sym()
                    return params
                self.expect_sym('COMMA')
                self.get_sym()
        else:
            return None

    def p_statement_call(self):
        if self.is_sym('CALL'):
            self.get_sym()
            self.expect_sym('NAME')
            name_value = self.sym.value
            self.get_sym()
            params = self.p_statement_call_params()

            if params:
                call = ('CALL', name_value, params)
            else:
                call = ('CALL', name_value)

            return call
        else:
            return None

    def p_statement_begin(self):
        if self.is_sym('BEGIN'):
            statements = ['BEGIN']

            while True:
                self.get_sym()
                statement = self.p_statement()

                if statement:
                    statements.append(statement)

                if self.is_sym('END'):
                    self.get_sym()
                    return statements

                self.expect_sym('EOS')
        else:
            return None

    def p_statement_if(self):
        if self.is_sym('IF'):
            self.get_sym()
            condition = self.p_condition()

            self.expect_sym('THEN')
            self.get_sym()

            statement = self.p_statement()

            return 'IF', condition, statement,
        else:
            return None

    def p_statement_while(self):
        if self.is_sym('WHILE'):
            self.get_sym()

            condition = self.p_condition()

            self.expect_sym('DO')
            self.get_sym()

            statement = self.p_statement()

            return 'WHILE', condition, statement
        else:
            return None

    def p_condition(self):
        odd = False

        if self.is_sym('ODD'):
            odd = True
            self.get_sym()

        lhs = self.p_expression()

        if odd:
            return 'ODD', lhs

        elif self.sym.type in ['LT', 'LTE', 'GT', 'GTE', 'E', 'NE']:
            op = self.sym.type
            self.get_sym()

            rhs = self.p_expression()

            return 'CONDITION', lhs, op, rhs,
        else:
            self.expect_sym('~comparison-operator')

    def p_term_op(self):
        if self.is_sym('PLUS'):
            self.get_sym()

            return 'PLUS'
        elif self.is_sym('MINUS'):
            self.get_sym()

            return 'MINUS'
        else:
            return None

    def p_expression(self):
        sign = self.p_term_op()

        expression = ['EXPRESSION', sign]
        lhs = self.required(self.p_term(), 'lhs-term')

        expression.append(lhs)

        while True:
            operator = self.p_term_op()

            if not operator:
                return expression

            operand = self.required(self.p_term(), 'rhs-term')

            expression.append((operator, operand,))

    def p_factor_op(self):
        if self.is_sym('TIMES'):
            self.get_sym()

            return 'TIMES'
        elif self.is_sym('DIVIDE'):
            self.get_sym()

            return 'DIVIDE'
        else:
            return None

    def p_term(self):
        expression = ['TERM']
        lhs = self.required(self.p_factor(), 'lhs-factor')

        expression.append(lhs)

        while True:
            operator = self.p_factor_op()

            if not operator:
                return expression

            operand = self.required(self.p_factor(), 'rhs-factor')

            expression.append((operator, operand,))

    def p_factor(self):
        if self.is_sym('NAME'):
            value = self.sym.value
            self.get_sym()
            return 'NAME', value
        elif self.is_sym('NUMBER'):
            value = self.sym.value
            self.get_sym()
            return 'NUMBER', value
        elif self.is_sym('LPAREN'):
            self.get_sym()
            expression = self.required(self.p_expression(), 'expression')

            self.expect_sym('RPAREN')

            self.get_sym()
            return expression



def is_flat(tree):
    if tree is None:
        return False

    for val in tree:
        if type(val) in (list, dict, tuple):
            return False
    return True

def print_tree(tree, depth = 0):
    if is_flat(tree):
        print("  " * depth + str(tree))
    elif type(tree) == list or type(tree) == tuple:
        print_tree(tree[0], depth)
        for val in tree[1:]:
            print_tree(val, depth+1)
    elif type(tree) == dict:
        for key, val in tree.items():
            print("  " * depth + str(key))
            print_tree(val, depth+1)
    elif tree is None:
        pass
    else:
        print("  " * depth + str(tree))


if __name__ == "__main__":
    p = Parser()
    code = utils.get_input()
    p.input(code)

    result = p.p_program()

    # print `result`
    print_tree(result)

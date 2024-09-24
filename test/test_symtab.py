from symtab import Symtab


if __name__ == '__main__':
    symtab = Symtab()

    symtab.new_symbol('aa', ('VARIABLE', 'a', ))
    symtab.new_symbol('bb', ('VARIABLE', 'bb', ))

    symtab.new_frame()
    symtab.new_symbol('aa', ('VARIABLE', 'a', ))
    symtab.new_symbol('bb', ('VARIABLE', 'bb', ))


    pass
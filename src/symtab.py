

class SymbtabItem:
    def __init__(self, name, item_content, parent = None):
        self.parent = None
        self.content = {name: item_content}


class Symtab:
    def __init__(self):
        self.idx = 0
        self.content = [{'parent': None, 'symtab': {}}]

    def new_symtab_item(self):
        self.content.append({'parent': None, 'symtab': {}})

    def new_symbol(self,name, item_content):
        self.content[self.idx]['symtab'][name] = SymbtabItem(name, item_content)

    def new_frame(self):
        self.content.append({'parent': self.content[-1], 'symtab': []})
        self.idx += 1
        return self.idx

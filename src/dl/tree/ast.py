from dl.tree.nodes import Node

class AST:
    
    def __init__(self, root: Node):
        self.root = root
        
    def __str__(self):
        return self.__str_ast(self.root)

    def __str_ast(self, node, ident: str = ''):
        strList = [str(node)]
        for n in node or []:
            strList.append(f'\n{ident}\\--> ')
            strList.append(self.__str_ast(n, f'{ident}     '))
        return ''.join(strList)

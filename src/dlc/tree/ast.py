from dlc.tree.nodes import Node

class AST:
    
    def __init__(self, root: Node):
        self.root = root
        
    def __str__(self):
        self.str_tree = ['.\n']
        return self.__str_ast(self.root)

    def __str_ast(self, node, prefix:str='', is_last=True):
        connector = '└───' if is_last else '├───'
        self.str_tree.append(f'{prefix}{connector}{str(node)}\n')
        new_prefix = f'{prefix}{"    " if is_last else "│   "}'
        for i, n in enumerate(node) or []:
            self.__str_ast(n, new_prefix, i==len(node)-1)
        return ''.join(self.str_tree)

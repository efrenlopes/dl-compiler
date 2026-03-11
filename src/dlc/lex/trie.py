from dlc.lex.tag import Tag


class TrieNode:
    
    def __init__(self) -> None:
        self.children = {}
        self.tag = None
    

class Trie:

    def __init__(self) -> None:
        self.root = TrieNode()

    #Considera prefix-closed
    def insert(self, tag: Tag, lexeme: str) -> None:
        node = self.root
        for c in lexeme:
            node = node.children.setdefault(c, TrieNode())
        node.tag = tag


    def __str__(self) -> str:
        self.str_tree = ['.\n']
        self.__str_trie(self.root, '', '')
        return ''.join(self.str_tree)


    def __str_trie(self, node:TrieNode, prefix:str, lexeme:str, is_last:bool = True) -> None:
        connector = '└───' if is_last else '├───'
        label = f"'{lexeme}'" if lexeme else '.'
        if node.tag:
            label += f' <{node.tag}>'
        self.str_tree.append(f'{prefix}{connector}{label}\n')
        new_prefix = f'{prefix}{"    " if is_last else "│   "}'
        children = list(node.children.items())
        for i, (char, child) in enumerate(children):
            self.__str_trie(child, new_prefix, lexeme + char, i == len(children) - 1)

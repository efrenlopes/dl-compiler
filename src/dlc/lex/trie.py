from dlc.lex.tag import Tag


class TrieNode:
    
    def __init__(self) -> None:
        self.children = {}
        self.tag = None


class Trie:

    def __init__(self) -> None:
        self.root = TrieNode()

    #Considera prefix-closed
    def insert(self, tag: Tag) -> None:
        node = self.root
        for c in tag.value:
            node = node.children.setdefault(c, TrieNode())
        node.tag = tag

    def print_tree(self) -> None:
        print("(root)")
        children = list(self.root.children.items())
        for i, (char, node) in enumerate(children):
            last = i == len(children) - 1
            self._print_node(char, node, "", last)

    def _print_node(self, char, node, prefix, last):
        branch = "└ " if last else "├ "
        token_str = f"  ({node.tag})" if node.tag else ""

        print(f"{prefix}{branch}'{char}'{token_str}")

        new_prefix = prefix + ("  " if last else "│ ")

        children = list(node.children.items())
        for i, (c, child) in enumerate(children):
            child_last = i == len(children) - 1
            self._print_node(c, child, new_prefix, child_last)


if __name__ == '__main__':
    trie = Trie()
    trie.insert(Tag.ASSIGN)
    trie.insert(Tag.EQ)
    trie.insert(Tag.EQ_EQ)
    trie.insert(Tag.LE)
    trie.print_tree()

    print(Tag.UNKNOWN)

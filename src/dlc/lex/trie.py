"""Trie data structure for lexical analysis (prefix-closed).

The structure allows efficient recognition of multi-character operators
using the maximal-munch strategy.
"""
from __future__ import annotations

from dlc.lex.tag import Tag


class TrieNode:
    """A node in the Trie data structure.
    
    Attributes
    ----------
    tag : Tag or None
        The tag associated with this node if it represents the end of a lexeme.
    children : dict
        Dictionary mapping characters to child TrieNode instances.

    """
    
    tag: Tag
    children: dict[str, TrieNode]

    def __init__(self, tag: Tag) -> None:
        """Initialize an empty TrieNode."""
        self.tag = tag
        self.children = {}
    


class Trie:
    """A Trie (prefix tree) data structure for efficient lexeme storage and retrieval.
    
    Attributes
    ----------
    root : TrieNode
        The root node of the Trie.
    
    """

    root: TrieNode

    def __init__(self) -> None:
        """Initialize a Trie with an empty root node."""
        self.root = TrieNode(Tag.UNKNOWN)


    def insert(self, tag: Tag, lexeme: str) -> None:
        """Insert a lexeme with its associated tag into the Trie.
        
        Parameters
        ----------
        tag : Tag
            The tag associated with the lexeme.
        lexeme : str
            The lexeme string to insert into the Trie.

        """
        node = self.root
        for c in lexeme:
            node = node.children.setdefault(c, TrieNode(tag))

    def __str__(self) -> str:
        self.str_tree: list[str] = ['.\n']
        children = list(self.root.children.items())
        for i, (char, n) in enumerate(children):
            self.__str_trie(n, '', char, i == len(children) - 1)
        return ''.join(self.str_tree)

    def __str_trie(self, node: TrieNode, prefix: str,
                        lexeme: str, is_last: bool = True) -> None:
        connector = '└───' if is_last else '├───'
        label = f"'{lexeme}' <{node.tag}>"
        self.str_tree.append(f'{prefix}{connector}{label}\n')        
        new_prefix = f'{prefix}{"    " if is_last else "│   "}'
        children = list(node.children.items())
        for i, (char, child) in enumerate(children):
            self.__str_trie(child, new_prefix, lexeme + char, i == len(children) - 1)
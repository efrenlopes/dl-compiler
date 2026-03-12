from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from dlc.tree.nodes import (
        AssignNode,
        BinaryNode,
        BlockNode,
        ConvertNode,
        DeclNode,
        ElseNode,
        IfNode,
        LiteralNode,
        ProgramNode,
        ReadNode,
        UnaryNode,
        VarNode,
        WhileNode,
        WriteNode,
    )

T = TypeVar('T')

class Visitor[T](ABC):
    
    
    @abstractmethod
    def visit_program_node(self, node: ProgramNode) -> T: pass
    
    @abstractmethod
    def visit_block_node(self, node: BlockNode) -> T: pass
    
    @abstractmethod
    def visit_decl_node(self, node: DeclNode) -> T: pass
    
    @abstractmethod
    def visit_assign_node(self, node: AssignNode) -> T: pass
    
    @abstractmethod
    def visit_if_node(self, node: IfNode) -> T: pass

    @abstractmethod
    def visit_else_node(self, node: ElseNode) -> T: pass

    @abstractmethod
    def visit_while_node(self, node: WhileNode) -> T: pass

    @abstractmethod
    def visit_write_node(self, node: WriteNode) -> T: pass

    @abstractmethod
    def visit_read_node(self, node: ReadNode) -> T: pass

    @abstractmethod
    def visit_var_node(self, node: VarNode) -> T: pass
    
    @abstractmethod
    def visit_literal_node(self, node: LiteralNode) -> T: pass
    
    @abstractmethod
    def visit_binary_node(self, node: BinaryNode) -> T: pass

    @abstractmethod
    def visit_unary_node(self, node: UnaryNode) -> T: pass

    @abstractmethod
    def visit_convert_node(self, node: ConvertNode) -> T: pass

from abc import ABC, abstractmethod

class Visitor(ABC):
    
    @abstractmethod
    def visit_program_node(self, node): pass
    
    @abstractmethod
    def visit_block_node(self, node): pass
    
    @abstractmethod
    def visit_decl_node(self, node): pass
    
    @abstractmethod
    def visit_assign_node(self, node): pass
    
    @abstractmethod
    def visit_if_node(self, node): pass

    @abstractmethod
    def visit_while_node(self, node): pass

    @abstractmethod
    def visit_write_node(self, node): pass

    @abstractmethod
    def visit_read_node(self, node): pass

    @abstractmethod
    def visit_var_node(self, node): pass
    
    @abstractmethod
    def visit_literal_node(self, node): pass
    
    @abstractmethod
    def visit_binary_node(self, node): pass
    
    @abstractmethod
    def visit_convert_node(self, node): pass

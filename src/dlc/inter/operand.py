from abc import ABC, abstractmethod
from dlc.semantic.type import Type


class Operand(ABC):
    @property
    def is_temp(self): return False

    @property
    def is_const(self): return False

    @property
    def is_label(self): return False

    @abstractmethod
    def __str__(self):
        pass



class Temp(Operand):
    __count = -1
    
    def __init__(self, type: Type):
        self.type = type
        Temp.__count = Temp.__count + 1
        self.number = Temp.__count
    
    @property
    def name(self):
        return f'%{self.number}'
    
    @property
    def is_temp(self):
        return True
    
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return f'<ic_temp: {str(self)}>'



class Const(Operand):
    def __init__(self, type: Type, value):
        self.type = type
        self.value = value

    @property
    def is_const(self):
        return True

    def __str__(self):
        if self.type.is_boolean:
            return str(int(self.value))
        return str(self.value)
    
    def __repr__(self):
        return f'<ic_const: {str(self)}>'



class Label(Operand):
    __count = -1
    
    def __init__(self):
        super().__init__()
        Label.__count += 1
        self.number = Label.__count

    @property
    def is_label(self):
        return True

    @property
    def name(self):
        return f'L{self.number}'
    
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return f'<ic_label: {self.name}>'



class Empty(Operand):
    def __str__(self):
        return '<ic_empty>'
    

Operand.EMPTY = Empty()
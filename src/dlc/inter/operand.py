from abc import ABC, abstractmethod

from dlc.semantic.type import Type


class Operand(ABC):
    @property
    def is_temp(self) -> bool: return False

    @property
    def is_temp_version(self) -> bool: return False

    @property
    def is_phi(self) -> bool: return False

    @property
    def is_const(self) -> bool: return False

    @property
    def is_label(self) -> bool: return False

    @abstractmethod
    def __str__(self) -> str: pass



class Temp(Operand):
    __count = -1
    
    def __init__(self, type: Type, is_address: bool=False) -> None:
        Temp.__count = Temp.__count + 1
        self.number = Temp.__count
        self.type = type
        self.is_address = is_address
    
    @property
    def name(self) -> str:
        return f't{self.number}'
    
    @property
    def is_temp(self) -> bool:
        return True
    
    def __str__(self) -> str:
        return self.name
    
    def __repr__(self) -> str:
        return f'<ir_temp: {self.name}>'


    



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
        return f'<ir_const: {str(self)}>'



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
        return f'<ir_label: {self.name}>'



class Empty(Operand):
    def __str__(self):
        return '<ir_empty>'

    def __repr__(self):
        return str(self)


Operand.EMPTY = Empty()
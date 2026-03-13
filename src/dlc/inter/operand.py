from __future__ import annotations

from abc import ABC, abstractmethod
from typing import cast

from dlc.semantic.type import Type


class Operand(ABC):
    EMPTY: Operand
    RUNTIME_TYPES = bool | int | float
    
    @property
    def is_temp(self) -> bool: return False

    @property
    def is_temp_version(self) -> bool: return False

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
    def __init__(self, type: Type, value: Operand.RUNTIME_TYPES) -> None:
        self.type = type
        self.value = value

    @property
    def is_const(self) -> bool:
        return True

    def __str__(self) -> str:
        if self.type.is_boolean:
            return str(int(cast(bool, self.value)))
        return str(self.value)
    
    def __repr__(self) -> str:
        return f'<ir_const: {str(self)}>'



class Label(Operand):
    __count = -1
    
    def __init__(self) -> None:
        super().__init__()
        Label.__count += 1
        self.number = Label.__count

    @property
    def is_label(self) -> bool:
        return True

    @property
    def name(self) -> str:
        return f'L{self.number}'
    
    def __str__(self) -> str:
        return self.name
    
    def __repr__(self) -> str:
        return f'<ir_label: {self.name}>'


class Empty(Operand):
    def __str__(self) -> str:
        return '<ir_empty>'

    def __repr__(self) -> str:
        return str(self)


Operand.EMPTY = Empty()
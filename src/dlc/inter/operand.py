from __future__ import annotations

from abc import ABC, abstractmethod
from typing import cast

from dlc.semantic.type import Type


class Operand(ABC):
    EMPTY: Operand
    RUNTIME_TYPES = bool | int | float
    
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
    
    def __str__(self) -> str:
        return self.name
    
    def __repr__(self) -> str:
        return f'<ir_temp: {self.name}>'


    



class Const(Operand):
    def __init__(self, type: Type, value: Operand.RUNTIME_TYPES) -> None:
        self.type = type
        self.value = value

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
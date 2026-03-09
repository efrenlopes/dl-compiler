from abc import ABC, abstractmethod
from dlc.inter.basic_block import BasicBlock
from dlc.semantic.type import Type


class Operand(ABC):
    @property
    def is_temp(self): return False

    @property
    def is_temp_version(self): return False

    @property
    def is_phi(self): return False

    @property
    def is_const(self): return False

    @property
    def is_label(self): return False

    @abstractmethod
    def __str__(self):
        pass



class Temp(Operand):
    __count = -1
    
    def __init__(self, type: Type, is_address: bool=False):
        Temp.__count = Temp.__count + 1
        self.number = Temp.__count
        self.type = type
        self.is_address = is_address
    
    @property
    def name(self):
        return f't{self.number}'
    
    @property
    def is_temp(self):
        return True
    
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return f'<ir_temp: {self.name}>'


class TempVersion(Operand):
    
    def __init__(self, origin:Temp, version: int):
        self.origin = origin
        self.type = origin.type
        self.version = version
    
    @property
    def name(self):
        return f't{self.origin.number}_{self.version}'
    
    @property
    def is_temp_version(self):
        return True
    
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return f'<ir_temp_version: {self.name}>'




class Phi(Operand):
    def __init__(self):
        # BasicBlock para SSATempVersion
        self.paths = {} 

    def add_path(self, block: BasicBlock, value: Operand):
        self.paths[block] = value

    @property
    def is_phi(self):
        return True

    def __str__(self):
        # Formato amigável: [bb1: t1_v1, bb2: t1_v2]
        pairs = [f"{bb}: {ver}" for bb, ver in self.paths.items()]
        return f"[{', '.join(pairs)}]"

    def __repr__(self):
        return '<ir_phi>'
    



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
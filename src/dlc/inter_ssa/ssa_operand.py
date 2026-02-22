from abc import ABC, abstractmethod
from dlc.inter.basic_block import BasicBlock
from dlc.semantic.type import Type


class SSAOperand(ABC):
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



class SSATemp(SSAOperand):
    __count = -1
    
    def __init__(self, type: Type, is_address: bool=False):
        SSATemp.__count = SSATemp.__count + 1
        self.number = SSATemp.__count
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
        return f'<ic_temp: {self.name}>'


class SSATempVersion(SSAOperand):
    
    def __init__(self, origin:SSATemp, version: int):
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
        return f'<ic_temp_version: {self.name}>'




class SSAPhi(SSAOperand):
    def __init__(self):
        # BasicBlock para SSATempVersion
        self.paths = {} 

    def add_path(self, block: BasicBlock, version: SSATempVersion):
        self.paths[block] = version

    @property
    def is_phi(self):
        return True

    def __str__(self):
        # Formato amigável: [bb1: t1_v1, bb2: t1_v2]
        pairs = [f"{bb}: {ver}" for bb, ver in self.paths.items()]
        return f"[{', '.join(pairs)}]"

    def __repr__(self):
        return '<ic_phi>'
    



class SSAConst(SSAOperand):
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



class SSALabel(SSAOperand):
    __count = -1
    
    def __init__(self):
        super().__init__()
        SSALabel.__count += 1
        self.number = SSALabel.__count

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



class Empty(SSAOperand):
    def __str__(self):
        return '<ic_empty>'

    def __repr__(self):
        return str(self)


SSAOperand.EMPTY = Empty()

from dlc.inter.basic_block import BasicBlock
from dlc.inter.operand import Operand, Temp


class TempVersion(Operand):
    
    def __init__(self, origin:Temp, version: int) -> None:
        self.origin = origin
        self.type = origin.type
        self.version = version
    
    @property
    def name(self) -> str:
        return f't{self.origin.number}_{self.version}'
    
    @property
    def is_temp_version(self) -> bool:
        return True
    
    def __str__(self) -> str:
        return self.name
    
    def __repr__(self) -> str:
        return f'<ir_temp_version: {self.name}>'




class Phi(Operand):
    def __init__(self) -> None:
        self.paths = {} 

    def add_path(self, block: BasicBlock, value: Operand) -> None:
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

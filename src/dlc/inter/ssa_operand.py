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

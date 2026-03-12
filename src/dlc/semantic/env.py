from __future__ import annotations

from collections.abc import Iterable

from dlc.semantic.type import Type


class SymbolInfo:
    def __init__(self, type: Type, scope: int, declaration_line: int) -> None:
        self.type = type
        self.scope = scope
        self.declaration_line = declaration_line
        self.initialized = False
        self.used = False
        
        
class Env:
    __count = -1
    
    def __init__(self, prev_env: (Env | None) = None) -> None:
        self.__symbol_table: dict[str, SymbolInfo] = {}
        self.__prev_env = prev_env
        Env.__count += 1
        self.number = Env.__count
        
    def put(self, symbol_name: str, symbol_info: SymbolInfo) -> None:
        self.__symbol_table[symbol_name] = symbol_info
        
    def get(self, symbol_name: str) -> (SymbolInfo | None):
        env = self
        while env is not None:
            if symbol_name in env.__symbol_table:
                return env.__symbol_table[symbol_name]
            env = env.__prev_env
        return None
    
    def get_local(self, symbol_name: str) -> SymbolInfo | None:
        return self.__symbol_table.get(symbol_name)
    
    def var_list(self) -> Iterable[str]:
        return self.__symbol_table.keys()

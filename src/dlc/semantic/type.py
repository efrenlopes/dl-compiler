from __future__ import annotations

from enum import IntEnum, auto

from dlc.lex.tag import Tag


class TypeCategory(IntEnum):
    BOOLEAN = auto()
    INTEGRAL = auto()
    FLOATING = auto()
    UNDEF = auto()


class Type:
    BOOL: Type
    INT: Type
    REAL: Type
    UNDEF: Type

    MIN_INT  = -2147483648
    MAX_INT  = 2147483647
    MIN_REAL = 2.2250738585072014e-308
    MAX_REAL = 1.7976931348623157e+308

    def __init__(self, name: str, category: TypeCategory, 
                    byte_size: int, is_signed: bool, rank: int) -> None:
        self.name = name
        self.category = category
        self.size = byte_size
        self.is_signed = is_signed
        self.rank = rank
        
    @property
    def is_boolean(self) -> bool:
        return self.category == TypeCategory.BOOLEAN

    @property
    def is_integral(self) -> bool:
        return self.category == TypeCategory.INTEGRAL
    
    @property
    def is_float(self) -> bool:
        return self.category == TypeCategory.FLOATING

    @property
    def is_undef(self) -> bool:
        return self.category == TypeCategory.UNDEF

    @property
    def is_numeric(self) -> bool:
        return self.is_integral or self.is_float
    
    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f'<Type: {self.name}>'

    @staticmethod
    def tag_to_type(tag: Tag) -> Type:
        match tag:
            case Tag.INT | Tag.LIT_INT: 
                return Type.INT
            case Tag.REAL | Tag.LIT_REAL: 
                return Type.REAL
            case Tag.BOOL | Tag.LIT_TRUE | Tag.LIT_FALSE: 
                return Type.BOOL
            case _:
                return Type.UNDEF

    @staticmethod
    def common_type(t1: Type, t2: Type) -> Type:
        if t1 == t2:
            return t1
        #elif t1.is_undef or t2.is_undef:
        #    return Type.UNDEF #<<<<<<<<<<<<<<<<<<< observar isso
        elif t1.is_numeric and t2.is_numeric:
            return t1 if t1.rank > t2.rank else t2
        return Type.UNDEF


Type.BOOL   = Type('bool', TypeCategory.BOOLEAN,  4, False, 0)
Type.INT    = Type('int', TypeCategory.INTEGRAL, 4, True, 5)
Type.REAL   = Type('real', TypeCategory.FLOATING, 8, True, 9)
Type.UNDEF  = Type('undef', TypeCategory.UNDEF, 0, False, 0)
# -*- coding: utf-8 -*-
"""
Gilded Rose Refactored with Strategy Pattern and SOLID Principles
Applies Clean Code principles: semantic naming, single responsibility,
DRY (Don't Repeat Yourself), and Strategy Pattern for extensibility.
"""

from abc import ABC, abstractmethod
from typing import List
from inspect import signature as _mutmut_signature
from typing import Annotated
from typing import Callable
from typing import ClassVar


MutantDict = Annotated[dict[str, Callable], "Mutant"]


def _mutmut_trampoline(orig, mutants, call_args, call_kwargs, self_arg = None):
    """Forward call to original or mutated function, depending on the environment"""
    import os
    mutant_under_test = os.environ['MUTANT_UNDER_TEST']
    if mutant_under_test == 'fail':
        from mutmut.__main__ import MutmutProgrammaticFailException
        raise MutmutProgrammaticFailException('Failed programmatically')      
    elif mutant_under_test == 'stats':
        from mutmut.__main__ import record_trampoline_hit
        record_trampoline_hit(orig.__module__ + '.' + orig.__name__)
        result = orig(*call_args, **call_kwargs)
        return result
    prefix = orig.__module__ + '.' + orig.__name__ + '__mutmut_'
    if not mutant_under_test.startswith(prefix):
        result = orig(*call_args, **call_kwargs)
        return result
    mutant_name = mutant_under_test.rpartition('.')[-1]
    if self_arg is not None:
        # call to a class method where self is not bound
        result = mutants[mutant_name](self_arg, *call_args, **call_kwargs)
    else:
        result = mutants[mutant_name](*call_args, **call_kwargs)
    return result


class Item:
    """Represents an item in the Gilded Rose inventory."""
    
    def xǁItemǁ__init____mutmut_orig(self, name: str, sell_in: int, quality: int):
        self.name = name
        self.sell_in = sell_in
        self.quality = quality
    
    def xǁItemǁ__init____mutmut_1(self, name: str, sell_in: int, quality: int):
        self.name = None
        self.sell_in = sell_in
        self.quality = quality
    
    def xǁItemǁ__init____mutmut_2(self, name: str, sell_in: int, quality: int):
        self.name = name
        self.sell_in = None
        self.quality = quality
    
    def xǁItemǁ__init____mutmut_3(self, name: str, sell_in: int, quality: int):
        self.name = name
        self.sell_in = sell_in
        self.quality = None
    
    xǁItemǁ__init____mutmut_mutants : ClassVar[MutantDict] = {
    'xǁItemǁ__init____mutmut_1': xǁItemǁ__init____mutmut_1, 
        'xǁItemǁ__init____mutmut_2': xǁItemǁ__init____mutmut_2, 
        'xǁItemǁ__init____mutmut_3': xǁItemǁ__init____mutmut_3
    }
    
    def __init__(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁItemǁ__init____mutmut_orig"), object.__getattribute__(self, "xǁItemǁ__init____mutmut_mutants"), args, kwargs, self)
        return result 
    
    __init__.__signature__ = _mutmut_signature(xǁItemǁ__init____mutmut_orig)
    xǁItemǁ__init____mutmut_orig.__name__ = 'xǁItemǁ__init__'

    def __repr__(self) -> str:
        return f"{self.name}, {self.sell_in}, {self.quality}"


class QualityUpdater(ABC):
    """
    Abstract base class implementing Strategy Pattern for quality updates.
    Removes nested conditionals and provides semantic operations.
    """
    
    MINIMUM_QUALITY = 0
    MAXIMUM_QUALITY = 50
    
    @abstractmethod
    def update_quality(self, item: Item) -> None:
        """Update item quality according to item type rules."""
        pass
    
    @abstractmethod
    def update_sell_in(self, item: Item) -> None:
        """Update item sell_in value."""
        pass
    
    def xǁQualityUpdaterǁclamp_quality__mutmut_orig(self, quality: int) -> int:
        """Enforce quality boundaries [0, 50] - removes code duplication."""
        return max(self.MINIMUM_QUALITY, min(quality, self.MAXIMUM_QUALITY))
    
    def xǁQualityUpdaterǁclamp_quality__mutmut_1(self, quality: int) -> int:
        """Enforce quality boundaries [0, 50] - removes code duplication."""
        return max(None, min(quality, self.MAXIMUM_QUALITY))
    
    def xǁQualityUpdaterǁclamp_quality__mutmut_2(self, quality: int) -> int:
        """Enforce quality boundaries [0, 50] - removes code duplication."""
        return max(self.MINIMUM_QUALITY, None)
    
    def xǁQualityUpdaterǁclamp_quality__mutmut_3(self, quality: int) -> int:
        """Enforce quality boundaries [0, 50] - removes code duplication."""
        return max(min(quality, self.MAXIMUM_QUALITY))
    
    def xǁQualityUpdaterǁclamp_quality__mutmut_4(self, quality: int) -> int:
        """Enforce quality boundaries [0, 50] - removes code duplication."""
        return max(self.MINIMUM_QUALITY, )
    
    def xǁQualityUpdaterǁclamp_quality__mutmut_5(self, quality: int) -> int:
        """Enforce quality boundaries [0, 50] - removes code duplication."""
        return max(self.MINIMUM_QUALITY, min(None, self.MAXIMUM_QUALITY))
    
    def xǁQualityUpdaterǁclamp_quality__mutmut_6(self, quality: int) -> int:
        """Enforce quality boundaries [0, 50] - removes code duplication."""
        return max(self.MINIMUM_QUALITY, min(quality, None))
    
    def xǁQualityUpdaterǁclamp_quality__mutmut_7(self, quality: int) -> int:
        """Enforce quality boundaries [0, 50] - removes code duplication."""
        return max(self.MINIMUM_QUALITY, min(self.MAXIMUM_QUALITY))
    
    def xǁQualityUpdaterǁclamp_quality__mutmut_8(self, quality: int) -> int:
        """Enforce quality boundaries [0, 50] - removes code duplication."""
        return max(self.MINIMUM_QUALITY, min(quality, ))
    
    xǁQualityUpdaterǁclamp_quality__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁQualityUpdaterǁclamp_quality__mutmut_1': xǁQualityUpdaterǁclamp_quality__mutmut_1, 
        'xǁQualityUpdaterǁclamp_quality__mutmut_2': xǁQualityUpdaterǁclamp_quality__mutmut_2, 
        'xǁQualityUpdaterǁclamp_quality__mutmut_3': xǁQualityUpdaterǁclamp_quality__mutmut_3, 
        'xǁQualityUpdaterǁclamp_quality__mutmut_4': xǁQualityUpdaterǁclamp_quality__mutmut_4, 
        'xǁQualityUpdaterǁclamp_quality__mutmut_5': xǁQualityUpdaterǁclamp_quality__mutmut_5, 
        'xǁQualityUpdaterǁclamp_quality__mutmut_6': xǁQualityUpdaterǁclamp_quality__mutmut_6, 
        'xǁQualityUpdaterǁclamp_quality__mutmut_7': xǁQualityUpdaterǁclamp_quality__mutmut_7, 
        'xǁQualityUpdaterǁclamp_quality__mutmut_8': xǁQualityUpdaterǁclamp_quality__mutmut_8
    }
    
    def clamp_quality(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁQualityUpdaterǁclamp_quality__mutmut_orig"), object.__getattribute__(self, "xǁQualityUpdaterǁclamp_quality__mutmut_mutants"), args, kwargs, self)
        return result 
    
    clamp_quality.__signature__ = _mutmut_signature(xǁQualityUpdaterǁclamp_quality__mutmut_orig)
    xǁQualityUpdaterǁclamp_quality__mutmut_orig.__name__ = 'xǁQualityUpdaterǁclamp_quality'
    
    def xǁQualityUpdaterǁis_expired__mutmut_orig(self, item: Item) -> bool:
        """Semantic check for expiration - improves readability."""
        return item.sell_in < 0
    
    def xǁQualityUpdaterǁis_expired__mutmut_1(self, item: Item) -> bool:
        """Semantic check for expiration - improves readability."""
        return item.sell_in <= 0
    
    def xǁQualityUpdaterǁis_expired__mutmut_2(self, item: Item) -> bool:
        """Semantic check for expiration - improves readability."""
        return item.sell_in < 1
    
    xǁQualityUpdaterǁis_expired__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁQualityUpdaterǁis_expired__mutmut_1': xǁQualityUpdaterǁis_expired__mutmut_1, 
        'xǁQualityUpdaterǁis_expired__mutmut_2': xǁQualityUpdaterǁis_expired__mutmut_2
    }
    
    def is_expired(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁQualityUpdaterǁis_expired__mutmut_orig"), object.__getattribute__(self, "xǁQualityUpdaterǁis_expired__mutmut_mutants"), args, kwargs, self)
        return result 
    
    is_expired.__signature__ = _mutmut_signature(xǁQualityUpdaterǁis_expired__mutmut_orig)
    xǁQualityUpdaterǁis_expired__mutmut_orig.__name__ = 'xǁQualityUpdaterǁis_expired'
    
    def xǁQualityUpdaterǁdecrease_sell_in__mutmut_orig(self, item: Item) -> None:
        """Semantic method for sell_in decrement."""
        item.sell_in -= 1
    
    def xǁQualityUpdaterǁdecrease_sell_in__mutmut_1(self, item: Item) -> None:
        """Semantic method for sell_in decrement."""
        item.sell_in = 1
    
    def xǁQualityUpdaterǁdecrease_sell_in__mutmut_2(self, item: Item) -> None:
        """Semantic method for sell_in decrement."""
        item.sell_in += 1
    
    def xǁQualityUpdaterǁdecrease_sell_in__mutmut_3(self, item: Item) -> None:
        """Semantic method for sell_in decrement."""
        item.sell_in -= 2
    
    xǁQualityUpdaterǁdecrease_sell_in__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁQualityUpdaterǁdecrease_sell_in__mutmut_1': xǁQualityUpdaterǁdecrease_sell_in__mutmut_1, 
        'xǁQualityUpdaterǁdecrease_sell_in__mutmut_2': xǁQualityUpdaterǁdecrease_sell_in__mutmut_2, 
        'xǁQualityUpdaterǁdecrease_sell_in__mutmut_3': xǁQualityUpdaterǁdecrease_sell_in__mutmut_3
    }
    
    def decrease_sell_in(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁQualityUpdaterǁdecrease_sell_in__mutmut_orig"), object.__getattribute__(self, "xǁQualityUpdaterǁdecrease_sell_in__mutmut_mutants"), args, kwargs, self)
        return result 
    
    decrease_sell_in.__signature__ = _mutmut_signature(xǁQualityUpdaterǁdecrease_sell_in__mutmut_orig)
    xǁQualityUpdaterǁdecrease_sell_in__mutmut_orig.__name__ = 'xǁQualityUpdaterǁdecrease_sell_in'


class NormalItemUpdater(QualityUpdater):
    """
    Strategy for normal items (neither Aged Brie nor Backstage passes).
    Degrades quality by 1 before expiration, 2 after.
    """
    
    def xǁNormalItemUpdaterǁupdate_quality__mutmut_orig(self, item: Item) -> None:
        """Decrease quality by 1 before expiration, 2 after."""
        self._degrade_quality_before_expiration(item)
    
    def xǁNormalItemUpdaterǁupdate_quality__mutmut_1(self, item: Item) -> None:
        """Decrease quality by 1 before expiration, 2 after."""
        self._degrade_quality_before_expiration(None)
    
    xǁNormalItemUpdaterǁupdate_quality__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁNormalItemUpdaterǁupdate_quality__mutmut_1': xǁNormalItemUpdaterǁupdate_quality__mutmut_1
    }
    
    def update_quality(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁNormalItemUpdaterǁupdate_quality__mutmut_orig"), object.__getattribute__(self, "xǁNormalItemUpdaterǁupdate_quality__mutmut_mutants"), args, kwargs, self)
        return result 
    
    update_quality.__signature__ = _mutmut_signature(xǁNormalItemUpdaterǁupdate_quality__mutmut_orig)
    xǁNormalItemUpdaterǁupdate_quality__mutmut_orig.__name__ = 'xǁNormalItemUpdaterǁupdate_quality'
    
    def xǁNormalItemUpdaterǁupdate_sell_in__mutmut_orig(self, item: Item) -> None:
        """Decrease sell_in by 1 each day."""
        self.decrease_sell_in(item)
        # Apply double degradation after sell_in becomes negative
        if self.is_expired(item):
            self._degrade_quality_additional_after_expiration(item)
    
    def xǁNormalItemUpdaterǁupdate_sell_in__mutmut_1(self, item: Item) -> None:
        """Decrease sell_in by 1 each day."""
        self.decrease_sell_in(None)
        # Apply double degradation after sell_in becomes negative
        if self.is_expired(item):
            self._degrade_quality_additional_after_expiration(item)
    
    def xǁNormalItemUpdaterǁupdate_sell_in__mutmut_2(self, item: Item) -> None:
        """Decrease sell_in by 1 each day."""
        self.decrease_sell_in(item)
        # Apply double degradation after sell_in becomes negative
        if self.is_expired(None):
            self._degrade_quality_additional_after_expiration(item)
    
    def xǁNormalItemUpdaterǁupdate_sell_in__mutmut_3(self, item: Item) -> None:
        """Decrease sell_in by 1 each day."""
        self.decrease_sell_in(item)
        # Apply double degradation after sell_in becomes negative
        if self.is_expired(item):
            self._degrade_quality_additional_after_expiration(None)
    
    xǁNormalItemUpdaterǁupdate_sell_in__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁNormalItemUpdaterǁupdate_sell_in__mutmut_1': xǁNormalItemUpdaterǁupdate_sell_in__mutmut_1, 
        'xǁNormalItemUpdaterǁupdate_sell_in__mutmut_2': xǁNormalItemUpdaterǁupdate_sell_in__mutmut_2, 
        'xǁNormalItemUpdaterǁupdate_sell_in__mutmut_3': xǁNormalItemUpdaterǁupdate_sell_in__mutmut_3
    }
    
    def update_sell_in(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁNormalItemUpdaterǁupdate_sell_in__mutmut_orig"), object.__getattribute__(self, "xǁNormalItemUpdaterǁupdate_sell_in__mutmut_mutants"), args, kwargs, self)
        return result 
    
    update_sell_in.__signature__ = _mutmut_signature(xǁNormalItemUpdaterǁupdate_sell_in__mutmut_orig)
    xǁNormalItemUpdaterǁupdate_sell_in__mutmut_orig.__name__ = 'xǁNormalItemUpdaterǁupdate_sell_in'
    
    def xǁNormalItemUpdaterǁ_degrade_quality_before_expiration__mutmut_orig(self, item: Item) -> None:
        """Quality decreases by 1 before sell_in date."""
        item.quality = self.clamp_quality(item.quality - 1)
    
    def xǁNormalItemUpdaterǁ_degrade_quality_before_expiration__mutmut_1(self, item: Item) -> None:
        """Quality decreases by 1 before sell_in date."""
        item.quality = None
    
    def xǁNormalItemUpdaterǁ_degrade_quality_before_expiration__mutmut_2(self, item: Item) -> None:
        """Quality decreases by 1 before sell_in date."""
        item.quality = self.clamp_quality(None)
    
    def xǁNormalItemUpdaterǁ_degrade_quality_before_expiration__mutmut_3(self, item: Item) -> None:
        """Quality decreases by 1 before sell_in date."""
        item.quality = self.clamp_quality(item.quality + 1)
    
    def xǁNormalItemUpdaterǁ_degrade_quality_before_expiration__mutmut_4(self, item: Item) -> None:
        """Quality decreases by 1 before sell_in date."""
        item.quality = self.clamp_quality(item.quality - 2)
    
    xǁNormalItemUpdaterǁ_degrade_quality_before_expiration__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁNormalItemUpdaterǁ_degrade_quality_before_expiration__mutmut_1': xǁNormalItemUpdaterǁ_degrade_quality_before_expiration__mutmut_1, 
        'xǁNormalItemUpdaterǁ_degrade_quality_before_expiration__mutmut_2': xǁNormalItemUpdaterǁ_degrade_quality_before_expiration__mutmut_2, 
        'xǁNormalItemUpdaterǁ_degrade_quality_before_expiration__mutmut_3': xǁNormalItemUpdaterǁ_degrade_quality_before_expiration__mutmut_3, 
        'xǁNormalItemUpdaterǁ_degrade_quality_before_expiration__mutmut_4': xǁNormalItemUpdaterǁ_degrade_quality_before_expiration__mutmut_4
    }
    
    def _degrade_quality_before_expiration(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁNormalItemUpdaterǁ_degrade_quality_before_expiration__mutmut_orig"), object.__getattribute__(self, "xǁNormalItemUpdaterǁ_degrade_quality_before_expiration__mutmut_mutants"), args, kwargs, self)
        return result 
    
    _degrade_quality_before_expiration.__signature__ = _mutmut_signature(xǁNormalItemUpdaterǁ_degrade_quality_before_expiration__mutmut_orig)
    xǁNormalItemUpdaterǁ_degrade_quality_before_expiration__mutmut_orig.__name__ = 'xǁNormalItemUpdaterǁ_degrade_quality_before_expiration'
    
    def xǁNormalItemUpdaterǁ_degrade_quality_additional_after_expiration__mutmut_orig(self, item: Item) -> None:
        """Quality degrades one more time after becoming expired."""
        item.quality = self.clamp_quality(item.quality - 1)
    
    def xǁNormalItemUpdaterǁ_degrade_quality_additional_after_expiration__mutmut_1(self, item: Item) -> None:
        """Quality degrades one more time after becoming expired."""
        item.quality = None
    
    def xǁNormalItemUpdaterǁ_degrade_quality_additional_after_expiration__mutmut_2(self, item: Item) -> None:
        """Quality degrades one more time after becoming expired."""
        item.quality = self.clamp_quality(None)
    
    def xǁNormalItemUpdaterǁ_degrade_quality_additional_after_expiration__mutmut_3(self, item: Item) -> None:
        """Quality degrades one more time after becoming expired."""
        item.quality = self.clamp_quality(item.quality + 1)
    
    def xǁNormalItemUpdaterǁ_degrade_quality_additional_after_expiration__mutmut_4(self, item: Item) -> None:
        """Quality degrades one more time after becoming expired."""
        item.quality = self.clamp_quality(item.quality - 2)
    
    xǁNormalItemUpdaterǁ_degrade_quality_additional_after_expiration__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁNormalItemUpdaterǁ_degrade_quality_additional_after_expiration__mutmut_1': xǁNormalItemUpdaterǁ_degrade_quality_additional_after_expiration__mutmut_1, 
        'xǁNormalItemUpdaterǁ_degrade_quality_additional_after_expiration__mutmut_2': xǁNormalItemUpdaterǁ_degrade_quality_additional_after_expiration__mutmut_2, 
        'xǁNormalItemUpdaterǁ_degrade_quality_additional_after_expiration__mutmut_3': xǁNormalItemUpdaterǁ_degrade_quality_additional_after_expiration__mutmut_3, 
        'xǁNormalItemUpdaterǁ_degrade_quality_additional_after_expiration__mutmut_4': xǁNormalItemUpdaterǁ_degrade_quality_additional_after_expiration__mutmut_4
    }
    
    def _degrade_quality_additional_after_expiration(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁNormalItemUpdaterǁ_degrade_quality_additional_after_expiration__mutmut_orig"), object.__getattribute__(self, "xǁNormalItemUpdaterǁ_degrade_quality_additional_after_expiration__mutmut_mutants"), args, kwargs, self)
        return result 
    
    _degrade_quality_additional_after_expiration.__signature__ = _mutmut_signature(xǁNormalItemUpdaterǁ_degrade_quality_additional_after_expiration__mutmut_orig)
    xǁNormalItemUpdaterǁ_degrade_quality_additional_after_expiration__mutmut_orig.__name__ = 'xǁNormalItemUpdaterǁ_degrade_quality_additional_after_expiration'


class AgedBrieUpdater(QualityUpdater):
    """
    Strategy for Aged Brie.
    Improves quality by 1 before expiration, 2 after (opposite of normal items).
    """
    
    def xǁAgedBrieUpdaterǁupdate_quality__mutmut_orig(self, item: Item) -> None:
        """Increase quality by 1 before expiration, 2 after."""
        self._improve_quality_before_expiration(item)
    
    def xǁAgedBrieUpdaterǁupdate_quality__mutmut_1(self, item: Item) -> None:
        """Increase quality by 1 before expiration, 2 after."""
        self._improve_quality_before_expiration(None)
    
    xǁAgedBrieUpdaterǁupdate_quality__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁAgedBrieUpdaterǁupdate_quality__mutmut_1': xǁAgedBrieUpdaterǁupdate_quality__mutmut_1
    }
    
    def update_quality(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁAgedBrieUpdaterǁupdate_quality__mutmut_orig"), object.__getattribute__(self, "xǁAgedBrieUpdaterǁupdate_quality__mutmut_mutants"), args, kwargs, self)
        return result 
    
    update_quality.__signature__ = _mutmut_signature(xǁAgedBrieUpdaterǁupdate_quality__mutmut_orig)
    xǁAgedBrieUpdaterǁupdate_quality__mutmut_orig.__name__ = 'xǁAgedBrieUpdaterǁupdate_quality'
    
    def xǁAgedBrieUpdaterǁupdate_sell_in__mutmut_orig(self, item: Item) -> None:
        """Decrease sell_in by 1 each day."""
        self.decrease_sell_in(item)
        # Apply additional improvement after sell_in becomes negative
        if self.is_expired(item):
            self._improve_quality_additional_after_expiration(item)
    
    def xǁAgedBrieUpdaterǁupdate_sell_in__mutmut_1(self, item: Item) -> None:
        """Decrease sell_in by 1 each day."""
        self.decrease_sell_in(None)
        # Apply additional improvement after sell_in becomes negative
        if self.is_expired(item):
            self._improve_quality_additional_after_expiration(item)
    
    def xǁAgedBrieUpdaterǁupdate_sell_in__mutmut_2(self, item: Item) -> None:
        """Decrease sell_in by 1 each day."""
        self.decrease_sell_in(item)
        # Apply additional improvement after sell_in becomes negative
        if self.is_expired(None):
            self._improve_quality_additional_after_expiration(item)
    
    def xǁAgedBrieUpdaterǁupdate_sell_in__mutmut_3(self, item: Item) -> None:
        """Decrease sell_in by 1 each day."""
        self.decrease_sell_in(item)
        # Apply additional improvement after sell_in becomes negative
        if self.is_expired(item):
            self._improve_quality_additional_after_expiration(None)
    
    xǁAgedBrieUpdaterǁupdate_sell_in__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁAgedBrieUpdaterǁupdate_sell_in__mutmut_1': xǁAgedBrieUpdaterǁupdate_sell_in__mutmut_1, 
        'xǁAgedBrieUpdaterǁupdate_sell_in__mutmut_2': xǁAgedBrieUpdaterǁupdate_sell_in__mutmut_2, 
        'xǁAgedBrieUpdaterǁupdate_sell_in__mutmut_3': xǁAgedBrieUpdaterǁupdate_sell_in__mutmut_3
    }
    
    def update_sell_in(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁAgedBrieUpdaterǁupdate_sell_in__mutmut_orig"), object.__getattribute__(self, "xǁAgedBrieUpdaterǁupdate_sell_in__mutmut_mutants"), args, kwargs, self)
        return result 
    
    update_sell_in.__signature__ = _mutmut_signature(xǁAgedBrieUpdaterǁupdate_sell_in__mutmut_orig)
    xǁAgedBrieUpdaterǁupdate_sell_in__mutmut_orig.__name__ = 'xǁAgedBrieUpdaterǁupdate_sell_in'
    
    def xǁAgedBrieUpdaterǁ_improve_quality_before_expiration__mutmut_orig(self, item: Item) -> None:
        """Quality increases by 1 before sell_in date."""
        item.quality = self.clamp_quality(item.quality + 1)
    
    def xǁAgedBrieUpdaterǁ_improve_quality_before_expiration__mutmut_1(self, item: Item) -> None:
        """Quality increases by 1 before sell_in date."""
        item.quality = None
    
    def xǁAgedBrieUpdaterǁ_improve_quality_before_expiration__mutmut_2(self, item: Item) -> None:
        """Quality increases by 1 before sell_in date."""
        item.quality = self.clamp_quality(None)
    
    def xǁAgedBrieUpdaterǁ_improve_quality_before_expiration__mutmut_3(self, item: Item) -> None:
        """Quality increases by 1 before sell_in date."""
        item.quality = self.clamp_quality(item.quality - 1)
    
    def xǁAgedBrieUpdaterǁ_improve_quality_before_expiration__mutmut_4(self, item: Item) -> None:
        """Quality increases by 1 before sell_in date."""
        item.quality = self.clamp_quality(item.quality + 2)
    
    xǁAgedBrieUpdaterǁ_improve_quality_before_expiration__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁAgedBrieUpdaterǁ_improve_quality_before_expiration__mutmut_1': xǁAgedBrieUpdaterǁ_improve_quality_before_expiration__mutmut_1, 
        'xǁAgedBrieUpdaterǁ_improve_quality_before_expiration__mutmut_2': xǁAgedBrieUpdaterǁ_improve_quality_before_expiration__mutmut_2, 
        'xǁAgedBrieUpdaterǁ_improve_quality_before_expiration__mutmut_3': xǁAgedBrieUpdaterǁ_improve_quality_before_expiration__mutmut_3, 
        'xǁAgedBrieUpdaterǁ_improve_quality_before_expiration__mutmut_4': xǁAgedBrieUpdaterǁ_improve_quality_before_expiration__mutmut_4
    }
    
    def _improve_quality_before_expiration(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁAgedBrieUpdaterǁ_improve_quality_before_expiration__mutmut_orig"), object.__getattribute__(self, "xǁAgedBrieUpdaterǁ_improve_quality_before_expiration__mutmut_mutants"), args, kwargs, self)
        return result 
    
    _improve_quality_before_expiration.__signature__ = _mutmut_signature(xǁAgedBrieUpdaterǁ_improve_quality_before_expiration__mutmut_orig)
    xǁAgedBrieUpdaterǁ_improve_quality_before_expiration__mutmut_orig.__name__ = 'xǁAgedBrieUpdaterǁ_improve_quality_before_expiration'
    
    def xǁAgedBrieUpdaterǁ_improve_quality_additional_after_expiration__mutmut_orig(self, item: Item) -> None:
        """Quality improves one more time after becoming expired."""
        item.quality = self.clamp_quality(item.quality + 1)
    
    def xǁAgedBrieUpdaterǁ_improve_quality_additional_after_expiration__mutmut_1(self, item: Item) -> None:
        """Quality improves one more time after becoming expired."""
        item.quality = None
    
    def xǁAgedBrieUpdaterǁ_improve_quality_additional_after_expiration__mutmut_2(self, item: Item) -> None:
        """Quality improves one more time after becoming expired."""
        item.quality = self.clamp_quality(None)
    
    def xǁAgedBrieUpdaterǁ_improve_quality_additional_after_expiration__mutmut_3(self, item: Item) -> None:
        """Quality improves one more time after becoming expired."""
        item.quality = self.clamp_quality(item.quality - 1)
    
    def xǁAgedBrieUpdaterǁ_improve_quality_additional_after_expiration__mutmut_4(self, item: Item) -> None:
        """Quality improves one more time after becoming expired."""
        item.quality = self.clamp_quality(item.quality + 2)
    
    xǁAgedBrieUpdaterǁ_improve_quality_additional_after_expiration__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁAgedBrieUpdaterǁ_improve_quality_additional_after_expiration__mutmut_1': xǁAgedBrieUpdaterǁ_improve_quality_additional_after_expiration__mutmut_1, 
        'xǁAgedBrieUpdaterǁ_improve_quality_additional_after_expiration__mutmut_2': xǁAgedBrieUpdaterǁ_improve_quality_additional_after_expiration__mutmut_2, 
        'xǁAgedBrieUpdaterǁ_improve_quality_additional_after_expiration__mutmut_3': xǁAgedBrieUpdaterǁ_improve_quality_additional_after_expiration__mutmut_3, 
        'xǁAgedBrieUpdaterǁ_improve_quality_additional_after_expiration__mutmut_4': xǁAgedBrieUpdaterǁ_improve_quality_additional_after_expiration__mutmut_4
    }
    
    def _improve_quality_additional_after_expiration(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁAgedBrieUpdaterǁ_improve_quality_additional_after_expiration__mutmut_orig"), object.__getattribute__(self, "xǁAgedBrieUpdaterǁ_improve_quality_additional_after_expiration__mutmut_mutants"), args, kwargs, self)
        return result 
    
    _improve_quality_additional_after_expiration.__signature__ = _mutmut_signature(xǁAgedBrieUpdaterǁ_improve_quality_additional_after_expiration__mutmut_orig)
    xǁAgedBrieUpdaterǁ_improve_quality_additional_after_expiration__mutmut_orig.__name__ = 'xǁAgedBrieUpdaterǁ_improve_quality_additional_after_expiration'


class BackstagePassUpdater(QualityUpdater):
    """
    Strategy for Backstage passes with tiered quality increases.
    Implements complex logic without nested conditionals.
    """
    
    DAYS_CRITICAL_ZONE = 6   # Less than 6 days: +3
    DAYS_URGENT_ZONE = 11    # Less than 11 days: +2
    
    def xǁBackstagePassUpdaterǁupdate_quality__mutmut_orig(self, item: Item) -> None:
        """Increase quality based on urgency (days until concert)."""
        self._increase_quality_by_urgency(item)
    
    def xǁBackstagePassUpdaterǁupdate_quality__mutmut_1(self, item: Item) -> None:
        """Increase quality based on urgency (days until concert)."""
        self._increase_quality_by_urgency(None)
    
    xǁBackstagePassUpdaterǁupdate_quality__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁBackstagePassUpdaterǁupdate_quality__mutmut_1': xǁBackstagePassUpdaterǁupdate_quality__mutmut_1
    }
    
    def update_quality(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁBackstagePassUpdaterǁupdate_quality__mutmut_orig"), object.__getattribute__(self, "xǁBackstagePassUpdaterǁupdate_quality__mutmut_mutants"), args, kwargs, self)
        return result 
    
    update_quality.__signature__ = _mutmut_signature(xǁBackstagePassUpdaterǁupdate_quality__mutmut_orig)
    xǁBackstagePassUpdaterǁupdate_quality__mutmut_orig.__name__ = 'xǁBackstagePassUpdaterǁupdate_quality'
    
    def xǁBackstagePassUpdaterǁupdate_sell_in__mutmut_orig(self, item: Item) -> None:
        """Decrease sell_in by 1 each day."""
        self.decrease_sell_in(item)
        # Drop quality to 0 after concert
        if self.is_expired(item):
            self._expire_backstage_pass(item)
    
    def xǁBackstagePassUpdaterǁupdate_sell_in__mutmut_1(self, item: Item) -> None:
        """Decrease sell_in by 1 each day."""
        self.decrease_sell_in(None)
        # Drop quality to 0 after concert
        if self.is_expired(item):
            self._expire_backstage_pass(item)
    
    def xǁBackstagePassUpdaterǁupdate_sell_in__mutmut_2(self, item: Item) -> None:
        """Decrease sell_in by 1 each day."""
        self.decrease_sell_in(item)
        # Drop quality to 0 after concert
        if self.is_expired(None):
            self._expire_backstage_pass(item)
    
    def xǁBackstagePassUpdaterǁupdate_sell_in__mutmut_3(self, item: Item) -> None:
        """Decrease sell_in by 1 each day."""
        self.decrease_sell_in(item)
        # Drop quality to 0 after concert
        if self.is_expired(item):
            self._expire_backstage_pass(None)
    
    xǁBackstagePassUpdaterǁupdate_sell_in__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁBackstagePassUpdaterǁupdate_sell_in__mutmut_1': xǁBackstagePassUpdaterǁupdate_sell_in__mutmut_1, 
        'xǁBackstagePassUpdaterǁupdate_sell_in__mutmut_2': xǁBackstagePassUpdaterǁupdate_sell_in__mutmut_2, 
        'xǁBackstagePassUpdaterǁupdate_sell_in__mutmut_3': xǁBackstagePassUpdaterǁupdate_sell_in__mutmut_3
    }
    
    def update_sell_in(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁBackstagePassUpdaterǁupdate_sell_in__mutmut_orig"), object.__getattribute__(self, "xǁBackstagePassUpdaterǁupdate_sell_in__mutmut_mutants"), args, kwargs, self)
        return result 
    
    update_sell_in.__signature__ = _mutmut_signature(xǁBackstagePassUpdaterǁupdate_sell_in__mutmut_orig)
    xǁBackstagePassUpdaterǁupdate_sell_in__mutmut_orig.__name__ = 'xǁBackstagePassUpdaterǁupdate_sell_in'
    
    def xǁBackstagePassUpdaterǁ_increase_quality_by_urgency__mutmut_orig(self, item: Item) -> None:
        """Increase quality based on days until concert (tiered bonuses)."""
        quality_increase = self._calculate_quality_increase(item.sell_in)
        item.quality = self.clamp_quality(item.quality + quality_increase)
    
    def xǁBackstagePassUpdaterǁ_increase_quality_by_urgency__mutmut_1(self, item: Item) -> None:
        """Increase quality based on days until concert (tiered bonuses)."""
        quality_increase = None
        item.quality = self.clamp_quality(item.quality + quality_increase)
    
    def xǁBackstagePassUpdaterǁ_increase_quality_by_urgency__mutmut_2(self, item: Item) -> None:
        """Increase quality based on days until concert (tiered bonuses)."""
        quality_increase = self._calculate_quality_increase(None)
        item.quality = self.clamp_quality(item.quality + quality_increase)
    
    def xǁBackstagePassUpdaterǁ_increase_quality_by_urgency__mutmut_3(self, item: Item) -> None:
        """Increase quality based on days until concert (tiered bonuses)."""
        quality_increase = self._calculate_quality_increase(item.sell_in)
        item.quality = None
    
    def xǁBackstagePassUpdaterǁ_increase_quality_by_urgency__mutmut_4(self, item: Item) -> None:
        """Increase quality based on days until concert (tiered bonuses)."""
        quality_increase = self._calculate_quality_increase(item.sell_in)
        item.quality = self.clamp_quality(None)
    
    def xǁBackstagePassUpdaterǁ_increase_quality_by_urgency__mutmut_5(self, item: Item) -> None:
        """Increase quality based on days until concert (tiered bonuses)."""
        quality_increase = self._calculate_quality_increase(item.sell_in)
        item.quality = self.clamp_quality(item.quality - quality_increase)
    
    xǁBackstagePassUpdaterǁ_increase_quality_by_urgency__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁBackstagePassUpdaterǁ_increase_quality_by_urgency__mutmut_1': xǁBackstagePassUpdaterǁ_increase_quality_by_urgency__mutmut_1, 
        'xǁBackstagePassUpdaterǁ_increase_quality_by_urgency__mutmut_2': xǁBackstagePassUpdaterǁ_increase_quality_by_urgency__mutmut_2, 
        'xǁBackstagePassUpdaterǁ_increase_quality_by_urgency__mutmut_3': xǁBackstagePassUpdaterǁ_increase_quality_by_urgency__mutmut_3, 
        'xǁBackstagePassUpdaterǁ_increase_quality_by_urgency__mutmut_4': xǁBackstagePassUpdaterǁ_increase_quality_by_urgency__mutmut_4, 
        'xǁBackstagePassUpdaterǁ_increase_quality_by_urgency__mutmut_5': xǁBackstagePassUpdaterǁ_increase_quality_by_urgency__mutmut_5
    }
    
    def _increase_quality_by_urgency(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁBackstagePassUpdaterǁ_increase_quality_by_urgency__mutmut_orig"), object.__getattribute__(self, "xǁBackstagePassUpdaterǁ_increase_quality_by_urgency__mutmut_mutants"), args, kwargs, self)
        return result 
    
    _increase_quality_by_urgency.__signature__ = _mutmut_signature(xǁBackstagePassUpdaterǁ_increase_quality_by_urgency__mutmut_orig)
    xǁBackstagePassUpdaterǁ_increase_quality_by_urgency__mutmut_orig.__name__ = 'xǁBackstagePassUpdaterǁ_increase_quality_by_urgency'
    
    def xǁBackstagePassUpdaterǁ_calculate_quality_increase__mutmut_orig(self, days_until_concert: int) -> int:
        """
        Extract quality increase calculation to semantic method.
        Replaces nested if-statements with clear logic flow.
        """
        if days_until_concert < self.DAYS_CRITICAL_ZONE:
            return 3  # 5 days or less: increase by 3
        elif days_until_concert < self.DAYS_URGENT_ZONE:
            return 2  # 6-10 days: increase by 2
        else:
            return 1  # More than 10 days: increase by 1
    
    def xǁBackstagePassUpdaterǁ_calculate_quality_increase__mutmut_1(self, days_until_concert: int) -> int:
        """
        Extract quality increase calculation to semantic method.
        Replaces nested if-statements with clear logic flow.
        """
        if days_until_concert <= self.DAYS_CRITICAL_ZONE:
            return 3  # 5 days or less: increase by 3
        elif days_until_concert < self.DAYS_URGENT_ZONE:
            return 2  # 6-10 days: increase by 2
        else:
            return 1  # More than 10 days: increase by 1
    
    def xǁBackstagePassUpdaterǁ_calculate_quality_increase__mutmut_2(self, days_until_concert: int) -> int:
        """
        Extract quality increase calculation to semantic method.
        Replaces nested if-statements with clear logic flow.
        """
        if days_until_concert < self.DAYS_CRITICAL_ZONE:
            return 4  # 5 days or less: increase by 3
        elif days_until_concert < self.DAYS_URGENT_ZONE:
            return 2  # 6-10 days: increase by 2
        else:
            return 1  # More than 10 days: increase by 1
    
    def xǁBackstagePassUpdaterǁ_calculate_quality_increase__mutmut_3(self, days_until_concert: int) -> int:
        """
        Extract quality increase calculation to semantic method.
        Replaces nested if-statements with clear logic flow.
        """
        if days_until_concert < self.DAYS_CRITICAL_ZONE:
            return 3  # 5 days or less: increase by 3
        elif days_until_concert <= self.DAYS_URGENT_ZONE:
            return 2  # 6-10 days: increase by 2
        else:
            return 1  # More than 10 days: increase by 1
    
    def xǁBackstagePassUpdaterǁ_calculate_quality_increase__mutmut_4(self, days_until_concert: int) -> int:
        """
        Extract quality increase calculation to semantic method.
        Replaces nested if-statements with clear logic flow.
        """
        if days_until_concert < self.DAYS_CRITICAL_ZONE:
            return 3  # 5 days or less: increase by 3
        elif days_until_concert < self.DAYS_URGENT_ZONE:
            return 3  # 6-10 days: increase by 2
        else:
            return 1  # More than 10 days: increase by 1
    
    def xǁBackstagePassUpdaterǁ_calculate_quality_increase__mutmut_5(self, days_until_concert: int) -> int:
        """
        Extract quality increase calculation to semantic method.
        Replaces nested if-statements with clear logic flow.
        """
        if days_until_concert < self.DAYS_CRITICAL_ZONE:
            return 3  # 5 days or less: increase by 3
        elif days_until_concert < self.DAYS_URGENT_ZONE:
            return 2  # 6-10 days: increase by 2
        else:
            return 2  # More than 10 days: increase by 1
    
    xǁBackstagePassUpdaterǁ_calculate_quality_increase__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁBackstagePassUpdaterǁ_calculate_quality_increase__mutmut_1': xǁBackstagePassUpdaterǁ_calculate_quality_increase__mutmut_1, 
        'xǁBackstagePassUpdaterǁ_calculate_quality_increase__mutmut_2': xǁBackstagePassUpdaterǁ_calculate_quality_increase__mutmut_2, 
        'xǁBackstagePassUpdaterǁ_calculate_quality_increase__mutmut_3': xǁBackstagePassUpdaterǁ_calculate_quality_increase__mutmut_3, 
        'xǁBackstagePassUpdaterǁ_calculate_quality_increase__mutmut_4': xǁBackstagePassUpdaterǁ_calculate_quality_increase__mutmut_4, 
        'xǁBackstagePassUpdaterǁ_calculate_quality_increase__mutmut_5': xǁBackstagePassUpdaterǁ_calculate_quality_increase__mutmut_5
    }
    
    def _calculate_quality_increase(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁBackstagePassUpdaterǁ_calculate_quality_increase__mutmut_orig"), object.__getattribute__(self, "xǁBackstagePassUpdaterǁ_calculate_quality_increase__mutmut_mutants"), args, kwargs, self)
        return result 
    
    _calculate_quality_increase.__signature__ = _mutmut_signature(xǁBackstagePassUpdaterǁ_calculate_quality_increase__mutmut_orig)
    xǁBackstagePassUpdaterǁ_calculate_quality_increase__mutmut_orig.__name__ = 'xǁBackstagePassUpdaterǁ_calculate_quality_increase'
    
    def xǁBackstagePassUpdaterǁ_expire_backstage_pass__mutmut_orig(self, item: Item) -> None:
        """Backstage pass loses all value after concert."""
        item.quality = self.MINIMUM_QUALITY
    
    def xǁBackstagePassUpdaterǁ_expire_backstage_pass__mutmut_1(self, item: Item) -> None:
        """Backstage pass loses all value after concert."""
        item.quality = None
    
    xǁBackstagePassUpdaterǁ_expire_backstage_pass__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁBackstagePassUpdaterǁ_expire_backstage_pass__mutmut_1': xǁBackstagePassUpdaterǁ_expire_backstage_pass__mutmut_1
    }
    
    def _expire_backstage_pass(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁBackstagePassUpdaterǁ_expire_backstage_pass__mutmut_orig"), object.__getattribute__(self, "xǁBackstagePassUpdaterǁ_expire_backstage_pass__mutmut_mutants"), args, kwargs, self)
        return result 
    
    _expire_backstage_pass.__signature__ = _mutmut_signature(xǁBackstagePassUpdaterǁ_expire_backstage_pass__mutmut_orig)
    xǁBackstagePassUpdaterǁ_expire_backstage_pass__mutmut_orig.__name__ = 'xǁBackstagePassUpdaterǁ_expire_backstage_pass'


class SulfurasUpdater(QualityUpdater):
    """
    Strategy for Sulfuras (legendary item).
    Implements the invariant: Sulfuras never changes.
    """
    
    def update_quality(self, item: Item) -> None:
        """Sulfuras is legendary - quality never changes."""
        pass  # No operation - immutable
    
    def update_sell_in(self, item: Item) -> None:
        """Sulfuras is legendary - sell_in never changes."""
        pass  # No operation - immutable


class ItemUpdaterFactory:
    """
    Factory Pattern for creating strategies.
    Implements Open/Closed Principle: open for extension, closed for modification.
    Adding new item types requires only adding a new strategy class.
    """
    
    def xǁItemUpdaterFactoryǁ__init____mutmut_orig(self):
        """Initialize with all known item type strategies."""
        self._strategies = {
            "Aged Brie": AgedBrieUpdater(),
            "Backstage passes to a TAFKAL80ETC concert": BackstagePassUpdater(),
            "Sulfuras, Hand of Ragnaros": SulfurasUpdater(),
        }
    
    def xǁItemUpdaterFactoryǁ__init____mutmut_1(self):
        """Initialize with all known item type strategies."""
        self._strategies = None
    
    def xǁItemUpdaterFactoryǁ__init____mutmut_2(self):
        """Initialize with all known item type strategies."""
        self._strategies = {
            "XXAged BrieXX": AgedBrieUpdater(),
            "Backstage passes to a TAFKAL80ETC concert": BackstagePassUpdater(),
            "Sulfuras, Hand of Ragnaros": SulfurasUpdater(),
        }
    
    def xǁItemUpdaterFactoryǁ__init____mutmut_3(self):
        """Initialize with all known item type strategies."""
        self._strategies = {
            "aged brie": AgedBrieUpdater(),
            "Backstage passes to a TAFKAL80ETC concert": BackstagePassUpdater(),
            "Sulfuras, Hand of Ragnaros": SulfurasUpdater(),
        }
    
    def xǁItemUpdaterFactoryǁ__init____mutmut_4(self):
        """Initialize with all known item type strategies."""
        self._strategies = {
            "AGED BRIE": AgedBrieUpdater(),
            "Backstage passes to a TAFKAL80ETC concert": BackstagePassUpdater(),
            "Sulfuras, Hand of Ragnaros": SulfurasUpdater(),
        }
    
    def xǁItemUpdaterFactoryǁ__init____mutmut_5(self):
        """Initialize with all known item type strategies."""
        self._strategies = {
            "Aged Brie": AgedBrieUpdater(),
            "XXBackstage passes to a TAFKAL80ETC concertXX": BackstagePassUpdater(),
            "Sulfuras, Hand of Ragnaros": SulfurasUpdater(),
        }
    
    def xǁItemUpdaterFactoryǁ__init____mutmut_6(self):
        """Initialize with all known item type strategies."""
        self._strategies = {
            "Aged Brie": AgedBrieUpdater(),
            "backstage passes to a tafkal80etc concert": BackstagePassUpdater(),
            "Sulfuras, Hand of Ragnaros": SulfurasUpdater(),
        }
    
    def xǁItemUpdaterFactoryǁ__init____mutmut_7(self):
        """Initialize with all known item type strategies."""
        self._strategies = {
            "Aged Brie": AgedBrieUpdater(),
            "BACKSTAGE PASSES TO A TAFKAL80ETC CONCERT": BackstagePassUpdater(),
            "Sulfuras, Hand of Ragnaros": SulfurasUpdater(),
        }
    
    def xǁItemUpdaterFactoryǁ__init____mutmut_8(self):
        """Initialize with all known item type strategies."""
        self._strategies = {
            "Aged Brie": AgedBrieUpdater(),
            "Backstage passes to a TAFKAL80ETC concert": BackstagePassUpdater(),
            "XXSulfuras, Hand of RagnarosXX": SulfurasUpdater(),
        }
    
    def xǁItemUpdaterFactoryǁ__init____mutmut_9(self):
        """Initialize with all known item type strategies."""
        self._strategies = {
            "Aged Brie": AgedBrieUpdater(),
            "Backstage passes to a TAFKAL80ETC concert": BackstagePassUpdater(),
            "sulfuras, hand of ragnaros": SulfurasUpdater(),
        }
    
    def xǁItemUpdaterFactoryǁ__init____mutmut_10(self):
        """Initialize with all known item type strategies."""
        self._strategies = {
            "Aged Brie": AgedBrieUpdater(),
            "Backstage passes to a TAFKAL80ETC concert": BackstagePassUpdater(),
            "SULFURAS, HAND OF RAGNAROS": SulfurasUpdater(),
        }
    
    xǁItemUpdaterFactoryǁ__init____mutmut_mutants : ClassVar[MutantDict] = {
    'xǁItemUpdaterFactoryǁ__init____mutmut_1': xǁItemUpdaterFactoryǁ__init____mutmut_1, 
        'xǁItemUpdaterFactoryǁ__init____mutmut_2': xǁItemUpdaterFactoryǁ__init____mutmut_2, 
        'xǁItemUpdaterFactoryǁ__init____mutmut_3': xǁItemUpdaterFactoryǁ__init____mutmut_3, 
        'xǁItemUpdaterFactoryǁ__init____mutmut_4': xǁItemUpdaterFactoryǁ__init____mutmut_4, 
        'xǁItemUpdaterFactoryǁ__init____mutmut_5': xǁItemUpdaterFactoryǁ__init____mutmut_5, 
        'xǁItemUpdaterFactoryǁ__init____mutmut_6': xǁItemUpdaterFactoryǁ__init____mutmut_6, 
        'xǁItemUpdaterFactoryǁ__init____mutmut_7': xǁItemUpdaterFactoryǁ__init____mutmut_7, 
        'xǁItemUpdaterFactoryǁ__init____mutmut_8': xǁItemUpdaterFactoryǁ__init____mutmut_8, 
        'xǁItemUpdaterFactoryǁ__init____mutmut_9': xǁItemUpdaterFactoryǁ__init____mutmut_9, 
        'xǁItemUpdaterFactoryǁ__init____mutmut_10': xǁItemUpdaterFactoryǁ__init____mutmut_10
    }
    
    def __init__(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁItemUpdaterFactoryǁ__init____mutmut_orig"), object.__getattribute__(self, "xǁItemUpdaterFactoryǁ__init____mutmut_mutants"), args, kwargs, self)
        return result 
    
    __init__.__signature__ = _mutmut_signature(xǁItemUpdaterFactoryǁ__init____mutmut_orig)
    xǁItemUpdaterFactoryǁ__init____mutmut_orig.__name__ = 'xǁItemUpdaterFactoryǁ__init__'
    
    def xǁItemUpdaterFactoryǁget_updater__mutmut_orig(self, item_name: str) -> QualityUpdater:
        """
        Get the appropriate strategy for an item.
        Returns NormalItemUpdater for unknown types (default).
        """
        return self._strategies.get(item_name, NormalItemUpdater())
    
    def xǁItemUpdaterFactoryǁget_updater__mutmut_1(self, item_name: str) -> QualityUpdater:
        """
        Get the appropriate strategy for an item.
        Returns NormalItemUpdater for unknown types (default).
        """
        return self._strategies.get(None, NormalItemUpdater())
    
    def xǁItemUpdaterFactoryǁget_updater__mutmut_2(self, item_name: str) -> QualityUpdater:
        """
        Get the appropriate strategy for an item.
        Returns NormalItemUpdater for unknown types (default).
        """
        return self._strategies.get(item_name, None)
    
    def xǁItemUpdaterFactoryǁget_updater__mutmut_3(self, item_name: str) -> QualityUpdater:
        """
        Get the appropriate strategy for an item.
        Returns NormalItemUpdater for unknown types (default).
        """
        return self._strategies.get(NormalItemUpdater())
    
    def xǁItemUpdaterFactoryǁget_updater__mutmut_4(self, item_name: str) -> QualityUpdater:
        """
        Get the appropriate strategy for an item.
        Returns NormalItemUpdater for unknown types (default).
        """
        return self._strategies.get(item_name, )
    
    xǁItemUpdaterFactoryǁget_updater__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁItemUpdaterFactoryǁget_updater__mutmut_1': xǁItemUpdaterFactoryǁget_updater__mutmut_1, 
        'xǁItemUpdaterFactoryǁget_updater__mutmut_2': xǁItemUpdaterFactoryǁget_updater__mutmut_2, 
        'xǁItemUpdaterFactoryǁget_updater__mutmut_3': xǁItemUpdaterFactoryǁget_updater__mutmut_3, 
        'xǁItemUpdaterFactoryǁget_updater__mutmut_4': xǁItemUpdaterFactoryǁget_updater__mutmut_4
    }
    
    def get_updater(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁItemUpdaterFactoryǁget_updater__mutmut_orig"), object.__getattribute__(self, "xǁItemUpdaterFactoryǁget_updater__mutmut_mutants"), args, kwargs, self)
        return result 
    
    get_updater.__signature__ = _mutmut_signature(xǁItemUpdaterFactoryǁget_updater__mutmut_orig)
    xǁItemUpdaterFactoryǁget_updater__mutmut_orig.__name__ = 'xǁItemUpdaterFactoryǁget_updater'
    
    def xǁItemUpdaterFactoryǁregister_strategy__mutmut_orig(self, item_name: str, updater: QualityUpdater) -> None:
        """
        Register a new item type strategy.
        Allows runtime addition of new item types without modifying existing code.
        """
        self._strategies[item_name] = updater
    
    def xǁItemUpdaterFactoryǁregister_strategy__mutmut_1(self, item_name: str, updater: QualityUpdater) -> None:
        """
        Register a new item type strategy.
        Allows runtime addition of new item types without modifying existing code.
        """
        self._strategies[item_name] = None
    
    xǁItemUpdaterFactoryǁregister_strategy__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁItemUpdaterFactoryǁregister_strategy__mutmut_1': xǁItemUpdaterFactoryǁregister_strategy__mutmut_1
    }
    
    def register_strategy(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁItemUpdaterFactoryǁregister_strategy__mutmut_orig"), object.__getattribute__(self, "xǁItemUpdaterFactoryǁregister_strategy__mutmut_mutants"), args, kwargs, self)
        return result 
    
    register_strategy.__signature__ = _mutmut_signature(xǁItemUpdaterFactoryǁregister_strategy__mutmut_orig)
    xǁItemUpdaterFactoryǁregister_strategy__mutmut_orig.__name__ = 'xǁItemUpdaterFactoryǁregister_strategy'


class GildedRose:
    """
    Main inventory manager using Strategy Pattern.
    
    Improvements over original:
    - No nested conditionals (max 2 levels instead of 6+)
    - Clear separation of concerns via strategies
    - Easy to add new item types without modifying this class
    - Semantic method names explain intent
    - Small, cohesive methods with single responsibility
    - No code duplication (shared logic in base class)
    """
    
    def xǁGildedRoseǁ__init____mutmut_orig(self, items: List[Item]):
        self.items = items
        self._updater_factory = ItemUpdaterFactory()
    
    def xǁGildedRoseǁ__init____mutmut_1(self, items: List[Item]):
        self.items = None
        self._updater_factory = ItemUpdaterFactory()
    
    def xǁGildedRoseǁ__init____mutmut_2(self, items: List[Item]):
        self.items = items
        self._updater_factory = None
    
    xǁGildedRoseǁ__init____mutmut_mutants : ClassVar[MutantDict] = {
    'xǁGildedRoseǁ__init____mutmut_1': xǁGildedRoseǁ__init____mutmut_1, 
        'xǁGildedRoseǁ__init____mutmut_2': xǁGildedRoseǁ__init____mutmut_2
    }
    
    def __init__(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁGildedRoseǁ__init____mutmut_orig"), object.__getattribute__(self, "xǁGildedRoseǁ__init____mutmut_mutants"), args, kwargs, self)
        return result 
    
    __init__.__signature__ = _mutmut_signature(xǁGildedRoseǁ__init____mutmut_orig)
    xǁGildedRoseǁ__init____mutmut_orig.__name__ = 'xǁGildedRoseǁ__init__'
    
    def xǁGildedRoseǁupdate_quality__mutmut_orig(self) -> None:
        """Update quality for all items in inventory."""
        for item in self.items:
            self._update_single_item(item)
    
    def xǁGildedRoseǁupdate_quality__mutmut_1(self) -> None:
        """Update quality for all items in inventory."""
        for item in self.items:
            self._update_single_item(None)
    
    xǁGildedRoseǁupdate_quality__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁGildedRoseǁupdate_quality__mutmut_1': xǁGildedRoseǁupdate_quality__mutmut_1
    }
    
    def update_quality(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁGildedRoseǁupdate_quality__mutmut_orig"), object.__getattribute__(self, "xǁGildedRoseǁupdate_quality__mutmut_mutants"), args, kwargs, self)
        return result 
    
    update_quality.__signature__ = _mutmut_signature(xǁGildedRoseǁupdate_quality__mutmut_orig)
    xǁGildedRoseǁupdate_quality__mutmut_orig.__name__ = 'xǁGildedRoseǁupdate_quality'
    
    def xǁGildedRoseǁ_update_single_item__mutmut_orig(self, item: Item) -> None:
        """
        Update a single item using the appropriate strategy.
        Delegates to the strategy pattern for type-specific logic.
        Note: First update quality, then update sell_in (which may apply post-expiration logic).
        """
        updater = self._updater_factory.get_updater(item.name)
        updater.update_quality(item)
        updater.update_sell_in(item)
    
    def xǁGildedRoseǁ_update_single_item__mutmut_1(self, item: Item) -> None:
        """
        Update a single item using the appropriate strategy.
        Delegates to the strategy pattern for type-specific logic.
        Note: First update quality, then update sell_in (which may apply post-expiration logic).
        """
        updater = None
        updater.update_quality(item)
        updater.update_sell_in(item)
    
    def xǁGildedRoseǁ_update_single_item__mutmut_2(self, item: Item) -> None:
        """
        Update a single item using the appropriate strategy.
        Delegates to the strategy pattern for type-specific logic.
        Note: First update quality, then update sell_in (which may apply post-expiration logic).
        """
        updater = self._updater_factory.get_updater(None)
        updater.update_quality(item)
        updater.update_sell_in(item)
    
    def xǁGildedRoseǁ_update_single_item__mutmut_3(self, item: Item) -> None:
        """
        Update a single item using the appropriate strategy.
        Delegates to the strategy pattern for type-specific logic.
        Note: First update quality, then update sell_in (which may apply post-expiration logic).
        """
        updater = self._updater_factory.get_updater(item.name)
        updater.update_quality(None)
        updater.update_sell_in(item)
    
    def xǁGildedRoseǁ_update_single_item__mutmut_4(self, item: Item) -> None:
        """
        Update a single item using the appropriate strategy.
        Delegates to the strategy pattern for type-specific logic.
        Note: First update quality, then update sell_in (which may apply post-expiration logic).
        """
        updater = self._updater_factory.get_updater(item.name)
        updater.update_quality(item)
        updater.update_sell_in(None)
    
    xǁGildedRoseǁ_update_single_item__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁGildedRoseǁ_update_single_item__mutmut_1': xǁGildedRoseǁ_update_single_item__mutmut_1, 
        'xǁGildedRoseǁ_update_single_item__mutmut_2': xǁGildedRoseǁ_update_single_item__mutmut_2, 
        'xǁGildedRoseǁ_update_single_item__mutmut_3': xǁGildedRoseǁ_update_single_item__mutmut_3, 
        'xǁGildedRoseǁ_update_single_item__mutmut_4': xǁGildedRoseǁ_update_single_item__mutmut_4
    }
    
    def _update_single_item(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁGildedRoseǁ_update_single_item__mutmut_orig"), object.__getattribute__(self, "xǁGildedRoseǁ_update_single_item__mutmut_mutants"), args, kwargs, self)
        return result 
    
    _update_single_item.__signature__ = _mutmut_signature(xǁGildedRoseǁ_update_single_item__mutmut_orig)
    xǁGildedRoseǁ_update_single_item__mutmut_orig.__name__ = 'xǁGildedRoseǁ_update_single_item'

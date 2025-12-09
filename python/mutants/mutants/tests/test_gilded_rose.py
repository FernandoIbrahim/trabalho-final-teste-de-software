# -*- coding: utf-8 -*-
import pytest
from gilded_rose import Item, GildedRose
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


class TestGildedRoseNormalItems:
    """Tests for normal items (neither Aged Brie nor Backstage passes)."""

    @pytest.mark.parametrize(
        "initial_quality,initial_sell_in,expected_quality,expected_sell_in",
        [
            # Boundary: Quality at maximum
            (50, 10, 49, 9),
            # Boundary: Quality at 1 (will decrease to 0)
            (1, 10, 0, 9),
            # Normal case: Quality > 1
            (25, 10, 24, 9),
            # Boundary: sell_in = 1 (before expiration)
            (10, 1, 9, 0),
            # Boundary: Quality = 0 (cannot go below 0)
            (0, 10, 0, 9),
            # Equivalence class: High quality, far from expiration
            (45, 20, 44, 19),
            # Equivalence class: Low quality, far from expiration
            (5, 20, 4, 19),
        ],
    )
    def test_normal_item_quality_decreases(
        self, initial_quality, initial_sell_in, expected_quality, expected_sell_in
    ):
        """Normal items decrease in quality by 1 before expiration."""
        items = [Item("Normal Item", initial_sell_in, initial_quality)]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == expected_quality
        assert items[0].sell_in == expected_sell_in

    @pytest.mark.parametrize(
        "initial_quality,initial_sell_in,expected_quality",
        [
            # Boundary: Just expired
            (10, -1, 8),
            # Boundary: Far expired
            (10, -10, 8),
            # Boundary: Quality at 2 (decreases by 2 after expiration)
            (2, -1, 0),
            # Boundary: Quality at 1 (would go below 0, but clamped to 0)
            (1, -1, 0),
            # Normal expired case
            (25, -1, 23),
            # Quality at 0 after expiration
            (0, -1, 0),
        ],
    )
    def test_normal_item_expired_quality_decreases_by_two(
        self, initial_quality, initial_sell_in, expected_quality
    ):
        """After expiration, normal items degrade twice as fast."""
        items = [Item("Normal Item", initial_sell_in, initial_quality)]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == expected_quality


class TestGildedRoseAgedBrie:
    """Tests for Aged Brie (increases in quality)."""

    @pytest.mark.parametrize(
        "initial_quality,initial_sell_in,expected_quality,expected_sell_in",
        [
            # Boundary: Quality at 49 (will increase to 50, max)
            (49, 10, 50, 9),
            # Boundary: Quality at 0 (will increase to 1)
            (0, 10, 1, 9),
            # Normal case: Quality in middle range
            (25, 10, 26, 9),
            # Boundary: Quality at 50 (already at max, cannot increase)
            (50, 10, 50, 9),
            # Boundary: sell_in = 1 (before expiration, next call will trigger post-expiration)
            (25, 1, 26, 0),
            # Equivalence class: High quality, far from expiration
            (45, 20, 46, 19),
            # Equivalence class: Low quality, far from expiration
            (5, 20, 6, 19),
        ],
    )
    def test_aged_brie_increases_quality(
        self, initial_quality, initial_sell_in, expected_quality, expected_sell_in
    ):
        """Aged Brie increases in quality."""
        items = [Item("Aged Brie", initial_sell_in, initial_quality)]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == expected_quality
        assert items[0].sell_in == expected_sell_in

    @pytest.mark.parametrize(
        "initial_quality,initial_sell_in,expected_quality",
        [
            # Boundary: Just expired, quality at 49
            (49, -1, 50),
            # Boundary: Just expired, quality at 48 (increases to 49 then to 50 cap)
            (48, -1, 50),
            # Boundary: Quality at 50 (already max, cannot increase further)
            (50, -1, 50),
            # Normal expired case
            (25, -1, 27),
            # Boundary: Quality at 0 after expiration
            (0, -1, 2),
        ],
    )
    def test_aged_brie_expired_increases_by_two(
        self, initial_quality, initial_sell_in, expected_quality
    ):
        """After expiration, Aged Brie increases by 2 per day (capped at 50)."""
        items = [Item("Aged Brie", initial_sell_in, initial_quality)]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == expected_quality


class TestGildedRoseBackstagePasses:
    """Tests for Backstage passes (increases with complex rules)."""

    @pytest.mark.parametrize(
        "initial_quality,initial_sell_in,expected_quality,expected_sell_in",
        [
            # Boundary: sell_in = 11 (not in either bonus range)
            (25, 11, 26, 10),
            # Boundary: sell_in = 10 (starts "less than 11" bonus)
            (25, 10, 27, 9),
            # Equivalence: sell_in in (6, 10]
            (25, 8, 27, 7),
            (25, 6, 27, 5),
            # Boundary: sell_in = 5 (starts "less than 6" bonus)
            (25, 5, 28, 4),
            # Equivalence: sell_in in (0, 5)
            (25, 3, 28, 2),
            (25, 1, 28, 0),
            # Boundary: Quality at 48 (will increase by 3 to 51, capped at 50)
            (48, 5, 50, 4),
            # Boundary: Quality at 49 (will increase by 2 to 51, capped at 50)
            (49, 10, 50, 9),
            # Boundary: Quality at 50 (already at max)
            (50, 5, 50, 4),
            # Boundary: Quality at 0, far from expiration
            (0, 11, 1, 10),
        ],
    )
    def test_backstage_pass_before_expiration(
        self, initial_quality, initial_sell_in, expected_quality, expected_sell_in
    ):
        """Backstage passes increase in quality at different rates before expiration."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", initial_sell_in, initial_quality)]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == expected_quality
        assert items[0].sell_in == expected_sell_in

    @pytest.mark.parametrize(
        "initial_quality,initial_sell_in,expected_quality",
        [
            # Boundary: Just expired (sell_in becomes -1)
            (25, 0, 0),
            # Boundary: Far expired
            (25, -5, 0),
            # Quality at 0 after expiration
            (0, -1, 0),
            # Quality at 50 after expiration
            (50, -1, 0),
        ],
    )
    def test_backstage_pass_expired_becomes_zero(
        self, initial_quality, initial_sell_in, expected_quality
    ):
        """After expiration, Backstage passes drop to 0 quality."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", initial_sell_in, initial_quality)]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == expected_quality


class TestGildedRoseSulfuras:
    """Tests for Sulfuras (legendary item, never decreases)."""

    @pytest.mark.parametrize(
        "initial_quality,initial_sell_in",
        [
            # Legendary item should maintain quality and sell_in
            (80, 0),
            (80, 10),
            (80, -1),
            (80, 100),
            # Edge cases for Sulfuras
            (79, 5),
            (81, 5),
        ],
    )
    def test_sulfuras_never_changes(self, initial_quality, initial_sell_in):
        """Sulfuras is a legendary item and never changes."""
        items = [Item("Sulfuras, Hand of Ragnaros", initial_sell_in, initial_quality)]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == initial_quality
        assert items[0].sell_in == initial_sell_in


class TestGildedRoseMultipleItems:
    """Tests for multiple items in one update."""

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_orig(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_1(self):
        """Multiple items should update independently."""
        items = None
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_2(self):
        """Multiple items should update independently."""
        items = [
            Item(None, 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_3(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", None, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_4(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, None),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_5(self):
        """Multiple items should update independently."""
        items = [
            Item(10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_6(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_7(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, ),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_8(self):
        """Multiple items should update independently."""
        items = [
            Item("XXNormal ItemXX", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_9(self):
        """Multiple items should update independently."""
        items = [
            Item("normal item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_10(self):
        """Multiple items should update independently."""
        items = [
            Item("NORMAL ITEM", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_11(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 11, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_12(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 21),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_13(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item(None, 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_14(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", None, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_15(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, None),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_16(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item(10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_17(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_18(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, ),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_19(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("XXAged BrieXX", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_20(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("aged brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_21(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("AGED BRIE", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_22(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 11, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_23(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 21),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_24(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item(None, 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_25(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", None, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_26(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, None),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_27(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item(10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_28(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_29(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, ),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_30(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("XXBackstage passes to a TAFKAL80ETC concertXX", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_31(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("backstage passes to a tafkal80etc concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_32(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("BACKSTAGE PASSES TO A TAFKAL80ETC CONCERT", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_33(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 11, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_34(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 21),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_35(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item(None, 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_36(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", None, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_37(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, None),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_38(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item(10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_39(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_40(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, ),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_41(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("XXSulfuras, Hand of RagnarosXX", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_42(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("sulfuras, hand of ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_43(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("SULFURAS, HAND OF RAGNAROS", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_44(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 11, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_45(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 81),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_46(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = None
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_47(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(None)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_48(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[1].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_49(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality != 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_50(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 20  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_51(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[1].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_52(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in != 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_53(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 10
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_54(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[2].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_55(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality != 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_56(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 22  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_57(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[2].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_58(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in != 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_59(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 10
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_60(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[3].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_61(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality != 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_62(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 23  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_63(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[3].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_64(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in != 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_65(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 10
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_66(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[4].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_67(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality != 80  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_68(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 81  # Sulfuras unchanged
        assert items[3].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_69(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[4].sell_in == 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_70(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in != 10

    def xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_71(self):
        """Multiple items should update independently."""
        items = [
            Item("Normal Item", 10, 20),
            Item("Aged Brie", 10, 20),
            Item("Backstage passes to a TAFKAL80ETC concert", 10, 20),
            Item("Sulfuras, Hand of Ragnaros", 10, 80),
        ]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 19  # Normal item decreases
        assert items[0].sell_in == 9
        assert items[1].quality == 21  # Aged Brie increases
        assert items[1].sell_in == 9
        assert items[2].quality == 22  # Backstage pass increases by 2
        assert items[2].sell_in == 9
        assert items[3].quality == 80  # Sulfuras unchanged
        assert items[3].sell_in == 11
    
    xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_1': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_1, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_2': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_2, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_3': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_3, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_4': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_4, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_5': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_5, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_6': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_6, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_7': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_7, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_8': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_8, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_9': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_9, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_10': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_10, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_11': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_11, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_12': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_12, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_13': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_13, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_14': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_14, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_15': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_15, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_16': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_16, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_17': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_17, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_18': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_18, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_19': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_19, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_20': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_20, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_21': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_21, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_22': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_22, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_23': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_23, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_24': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_24, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_25': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_25, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_26': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_26, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_27': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_27, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_28': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_28, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_29': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_29, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_30': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_30, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_31': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_31, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_32': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_32, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_33': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_33, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_34': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_34, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_35': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_35, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_36': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_36, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_37': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_37, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_38': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_38, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_39': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_39, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_40': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_40, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_41': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_41, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_42': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_42, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_43': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_43, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_44': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_44, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_45': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_45, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_46': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_46, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_47': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_47, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_48': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_48, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_49': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_49, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_50': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_50, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_51': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_51, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_52': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_52, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_53': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_53, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_54': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_54, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_55': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_55, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_56': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_56, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_57': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_57, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_58': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_58, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_59': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_59, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_60': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_60, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_61': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_61, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_62': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_62, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_63': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_63, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_64': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_64, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_65': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_65, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_66': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_66, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_67': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_67, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_68': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_68, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_69': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_69, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_70': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_70, 
        'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_71': xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_71
    }
    
    def test_multiple_items_update_independently(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_orig"), object.__getattribute__(self, "xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_mutants"), args, kwargs, self)
        return result 
    
    test_multiple_items_update_independently.__signature__ = _mutmut_signature(xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_orig)
    xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently__mutmut_orig.__name__ = 'xǁTestGildedRoseMultipleItemsǁtest_multiple_items_update_independently'

    def xǁTestGildedRoseMultipleItemsǁtest_empty_item_list__mutmut_orig(self):
        """Empty item list should not raise an error."""
        items = []
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()  # Should not raise

        assert len(items) == 0

    def xǁTestGildedRoseMultipleItemsǁtest_empty_item_list__mutmut_1(self):
        """Empty item list should not raise an error."""
        items = None
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()  # Should not raise

        assert len(items) == 0

    def xǁTestGildedRoseMultipleItemsǁtest_empty_item_list__mutmut_2(self):
        """Empty item list should not raise an error."""
        items = []
        gilded_rose = None
        gilded_rose.update_quality()  # Should not raise

        assert len(items) == 0

    def xǁTestGildedRoseMultipleItemsǁtest_empty_item_list__mutmut_3(self):
        """Empty item list should not raise an error."""
        items = []
        gilded_rose = GildedRose(None)
        gilded_rose.update_quality()  # Should not raise

        assert len(items) == 0

    def xǁTestGildedRoseMultipleItemsǁtest_empty_item_list__mutmut_4(self):
        """Empty item list should not raise an error."""
        items = []
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()  # Should not raise

        assert len(items) != 0

    def xǁTestGildedRoseMultipleItemsǁtest_empty_item_list__mutmut_5(self):
        """Empty item list should not raise an error."""
        items = []
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()  # Should not raise

        assert len(items) == 1
    
    xǁTestGildedRoseMultipleItemsǁtest_empty_item_list__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁTestGildedRoseMultipleItemsǁtest_empty_item_list__mutmut_1': xǁTestGildedRoseMultipleItemsǁtest_empty_item_list__mutmut_1, 
        'xǁTestGildedRoseMultipleItemsǁtest_empty_item_list__mutmut_2': xǁTestGildedRoseMultipleItemsǁtest_empty_item_list__mutmut_2, 
        'xǁTestGildedRoseMultipleItemsǁtest_empty_item_list__mutmut_3': xǁTestGildedRoseMultipleItemsǁtest_empty_item_list__mutmut_3, 
        'xǁTestGildedRoseMultipleItemsǁtest_empty_item_list__mutmut_4': xǁTestGildedRoseMultipleItemsǁtest_empty_item_list__mutmut_4, 
        'xǁTestGildedRoseMultipleItemsǁtest_empty_item_list__mutmut_5': xǁTestGildedRoseMultipleItemsǁtest_empty_item_list__mutmut_5
    }
    
    def test_empty_item_list(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁTestGildedRoseMultipleItemsǁtest_empty_item_list__mutmut_orig"), object.__getattribute__(self, "xǁTestGildedRoseMultipleItemsǁtest_empty_item_list__mutmut_mutants"), args, kwargs, self)
        return result 
    
    test_empty_item_list.__signature__ = _mutmut_signature(xǁTestGildedRoseMultipleItemsǁtest_empty_item_list__mutmut_orig)
    xǁTestGildedRoseMultipleItemsǁtest_empty_item_list__mutmut_orig.__name__ = 'xǁTestGildedRoseMultipleItemsǁtest_empty_item_list'


class TestGildedRoseEdgeCasesAndBoundaries:
    """Tests for edge cases and specific boundary conditions."""

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_orig(self):
        """Quality of normal items should never go below 0."""
        items = [Item("Normal Item", 10, 0)]
        gilded_rose = GildedRose(items)

        for _ in range(5):
            gilded_rose.update_quality()
            assert items[0].quality >= 0

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_1(self):
        """Quality of normal items should never go below 0."""
        items = None
        gilded_rose = GildedRose(items)

        for _ in range(5):
            gilded_rose.update_quality()
            assert items[0].quality >= 0

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_2(self):
        """Quality of normal items should never go below 0."""
        items = [Item(None, 10, 0)]
        gilded_rose = GildedRose(items)

        for _ in range(5):
            gilded_rose.update_quality()
            assert items[0].quality >= 0

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_3(self):
        """Quality of normal items should never go below 0."""
        items = [Item("Normal Item", None, 0)]
        gilded_rose = GildedRose(items)

        for _ in range(5):
            gilded_rose.update_quality()
            assert items[0].quality >= 0

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_4(self):
        """Quality of normal items should never go below 0."""
        items = [Item("Normal Item", 10, None)]
        gilded_rose = GildedRose(items)

        for _ in range(5):
            gilded_rose.update_quality()
            assert items[0].quality >= 0

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_5(self):
        """Quality of normal items should never go below 0."""
        items = [Item(10, 0)]
        gilded_rose = GildedRose(items)

        for _ in range(5):
            gilded_rose.update_quality()
            assert items[0].quality >= 0

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_6(self):
        """Quality of normal items should never go below 0."""
        items = [Item("Normal Item", 0)]
        gilded_rose = GildedRose(items)

        for _ in range(5):
            gilded_rose.update_quality()
            assert items[0].quality >= 0

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_7(self):
        """Quality of normal items should never go below 0."""
        items = [Item("Normal Item", 10, )]
        gilded_rose = GildedRose(items)

        for _ in range(5):
            gilded_rose.update_quality()
            assert items[0].quality >= 0

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_8(self):
        """Quality of normal items should never go below 0."""
        items = [Item("XXNormal ItemXX", 10, 0)]
        gilded_rose = GildedRose(items)

        for _ in range(5):
            gilded_rose.update_quality()
            assert items[0].quality >= 0

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_9(self):
        """Quality of normal items should never go below 0."""
        items = [Item("normal item", 10, 0)]
        gilded_rose = GildedRose(items)

        for _ in range(5):
            gilded_rose.update_quality()
            assert items[0].quality >= 0

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_10(self):
        """Quality of normal items should never go below 0."""
        items = [Item("NORMAL ITEM", 10, 0)]
        gilded_rose = GildedRose(items)

        for _ in range(5):
            gilded_rose.update_quality()
            assert items[0].quality >= 0

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_11(self):
        """Quality of normal items should never go below 0."""
        items = [Item("Normal Item", 11, 0)]
        gilded_rose = GildedRose(items)

        for _ in range(5):
            gilded_rose.update_quality()
            assert items[0].quality >= 0

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_12(self):
        """Quality of normal items should never go below 0."""
        items = [Item("Normal Item", 10, 1)]
        gilded_rose = GildedRose(items)

        for _ in range(5):
            gilded_rose.update_quality()
            assert items[0].quality >= 0

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_13(self):
        """Quality of normal items should never go below 0."""
        items = [Item("Normal Item", 10, 0)]
        gilded_rose = None

        for _ in range(5):
            gilded_rose.update_quality()
            assert items[0].quality >= 0

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_14(self):
        """Quality of normal items should never go below 0."""
        items = [Item("Normal Item", 10, 0)]
        gilded_rose = GildedRose(None)

        for _ in range(5):
            gilded_rose.update_quality()
            assert items[0].quality >= 0

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_15(self):
        """Quality of normal items should never go below 0."""
        items = [Item("Normal Item", 10, 0)]
        gilded_rose = GildedRose(items)

        for _ in range(None):
            gilded_rose.update_quality()
            assert items[0].quality >= 0

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_16(self):
        """Quality of normal items should never go below 0."""
        items = [Item("Normal Item", 10, 0)]
        gilded_rose = GildedRose(items)

        for _ in range(6):
            gilded_rose.update_quality()
            assert items[0].quality >= 0

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_17(self):
        """Quality of normal items should never go below 0."""
        items = [Item("Normal Item", 10, 0)]
        gilded_rose = GildedRose(items)

        for _ in range(5):
            gilded_rose.update_quality()
            assert items[1].quality >= 0

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_18(self):
        """Quality of normal items should never go below 0."""
        items = [Item("Normal Item", 10, 0)]
        gilded_rose = GildedRose(items)

        for _ in range(5):
            gilded_rose.update_quality()
            assert items[0].quality > 0

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_19(self):
        """Quality of normal items should never go below 0."""
        items = [Item("Normal Item", 10, 0)]
        gilded_rose = GildedRose(items)

        for _ in range(5):
            gilded_rose.update_quality()
            assert items[0].quality >= 1
    
    xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_1': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_1, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_2': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_2, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_3': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_3, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_4': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_4, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_5': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_5, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_6': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_6, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_7': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_7, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_8': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_8, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_9': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_9, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_10': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_10, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_11': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_11, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_12': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_12, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_13': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_13, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_14': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_14, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_15': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_15, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_16': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_16, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_17': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_17, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_18': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_18, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_19': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_19
    }
    
    def test_normal_item_quality_never_negative(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_orig"), object.__getattribute__(self, "xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_mutants"), args, kwargs, self)
        return result 
    
    test_normal_item_quality_never_negative.__signature__ = _mutmut_signature(xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_orig)
    xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative__mutmut_orig.__name__ = 'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_normal_item_quality_never_negative'

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_orig(self):
        """Quality of Aged Brie should never exceed 50."""
        items = [Item("Aged Brie", 0, 45)]
        gilded_rose = GildedRose(items)

        for _ in range(10):
            gilded_rose.update_quality()
            assert items[0].quality <= 50

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_1(self):
        """Quality of Aged Brie should never exceed 50."""
        items = None
        gilded_rose = GildedRose(items)

        for _ in range(10):
            gilded_rose.update_quality()
            assert items[0].quality <= 50

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_2(self):
        """Quality of Aged Brie should never exceed 50."""
        items = [Item(None, 0, 45)]
        gilded_rose = GildedRose(items)

        for _ in range(10):
            gilded_rose.update_quality()
            assert items[0].quality <= 50

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_3(self):
        """Quality of Aged Brie should never exceed 50."""
        items = [Item("Aged Brie", None, 45)]
        gilded_rose = GildedRose(items)

        for _ in range(10):
            gilded_rose.update_quality()
            assert items[0].quality <= 50

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_4(self):
        """Quality of Aged Brie should never exceed 50."""
        items = [Item("Aged Brie", 0, None)]
        gilded_rose = GildedRose(items)

        for _ in range(10):
            gilded_rose.update_quality()
            assert items[0].quality <= 50

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_5(self):
        """Quality of Aged Brie should never exceed 50."""
        items = [Item(0, 45)]
        gilded_rose = GildedRose(items)

        for _ in range(10):
            gilded_rose.update_quality()
            assert items[0].quality <= 50

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_6(self):
        """Quality of Aged Brie should never exceed 50."""
        items = [Item("Aged Brie", 45)]
        gilded_rose = GildedRose(items)

        for _ in range(10):
            gilded_rose.update_quality()
            assert items[0].quality <= 50

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_7(self):
        """Quality of Aged Brie should never exceed 50."""
        items = [Item("Aged Brie", 0, )]
        gilded_rose = GildedRose(items)

        for _ in range(10):
            gilded_rose.update_quality()
            assert items[0].quality <= 50

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_8(self):
        """Quality of Aged Brie should never exceed 50."""
        items = [Item("XXAged BrieXX", 0, 45)]
        gilded_rose = GildedRose(items)

        for _ in range(10):
            gilded_rose.update_quality()
            assert items[0].quality <= 50

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_9(self):
        """Quality of Aged Brie should never exceed 50."""
        items = [Item("aged brie", 0, 45)]
        gilded_rose = GildedRose(items)

        for _ in range(10):
            gilded_rose.update_quality()
            assert items[0].quality <= 50

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_10(self):
        """Quality of Aged Brie should never exceed 50."""
        items = [Item("AGED BRIE", 0, 45)]
        gilded_rose = GildedRose(items)

        for _ in range(10):
            gilded_rose.update_quality()
            assert items[0].quality <= 50

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_11(self):
        """Quality of Aged Brie should never exceed 50."""
        items = [Item("Aged Brie", 1, 45)]
        gilded_rose = GildedRose(items)

        for _ in range(10):
            gilded_rose.update_quality()
            assert items[0].quality <= 50

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_12(self):
        """Quality of Aged Brie should never exceed 50."""
        items = [Item("Aged Brie", 0, 46)]
        gilded_rose = GildedRose(items)

        for _ in range(10):
            gilded_rose.update_quality()
            assert items[0].quality <= 50

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_13(self):
        """Quality of Aged Brie should never exceed 50."""
        items = [Item("Aged Brie", 0, 45)]
        gilded_rose = None

        for _ in range(10):
            gilded_rose.update_quality()
            assert items[0].quality <= 50

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_14(self):
        """Quality of Aged Brie should never exceed 50."""
        items = [Item("Aged Brie", 0, 45)]
        gilded_rose = GildedRose(None)

        for _ in range(10):
            gilded_rose.update_quality()
            assert items[0].quality <= 50

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_15(self):
        """Quality of Aged Brie should never exceed 50."""
        items = [Item("Aged Brie", 0, 45)]
        gilded_rose = GildedRose(items)

        for _ in range(None):
            gilded_rose.update_quality()
            assert items[0].quality <= 50

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_16(self):
        """Quality of Aged Brie should never exceed 50."""
        items = [Item("Aged Brie", 0, 45)]
        gilded_rose = GildedRose(items)

        for _ in range(11):
            gilded_rose.update_quality()
            assert items[0].quality <= 50

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_17(self):
        """Quality of Aged Brie should never exceed 50."""
        items = [Item("Aged Brie", 0, 45)]
        gilded_rose = GildedRose(items)

        for _ in range(10):
            gilded_rose.update_quality()
            assert items[1].quality <= 50

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_18(self):
        """Quality of Aged Brie should never exceed 50."""
        items = [Item("Aged Brie", 0, 45)]
        gilded_rose = GildedRose(items)

        for _ in range(10):
            gilded_rose.update_quality()
            assert items[0].quality < 50

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_19(self):
        """Quality of Aged Brie should never exceed 50."""
        items = [Item("Aged Brie", 0, 45)]
        gilded_rose = GildedRose(items)

        for _ in range(10):
            gilded_rose.update_quality()
            assert items[0].quality <= 51
    
    xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_1': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_1, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_2': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_2, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_3': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_3, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_4': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_4, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_5': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_5, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_6': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_6, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_7': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_7, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_8': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_8, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_9': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_9, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_10': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_10, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_11': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_11, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_12': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_12, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_13': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_13, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_14': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_14, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_15': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_15, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_16': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_16, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_17': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_17, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_18': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_18, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_19': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_19
    }
    
    def test_aged_brie_quality_never_above_50(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_orig"), object.__getattribute__(self, "xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_mutants"), args, kwargs, self)
        return result 
    
    test_aged_brie_quality_never_above_50.__signature__ = _mutmut_signature(xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_orig)
    xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50__mutmut_orig.__name__ = 'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_aged_brie_quality_never_above_50'

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_orig(self):
        """Quality of Backstage passes should never exceed 50."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 5, 45)]
        gilded_rose = GildedRose(items)

        for _ in range(10):
            gilded_rose.update_quality()
            assert items[0].quality <= 50

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_1(self):
        """Quality of Backstage passes should never exceed 50."""
        items = None
        gilded_rose = GildedRose(items)

        for _ in range(10):
            gilded_rose.update_quality()
            assert items[0].quality <= 50

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_2(self):
        """Quality of Backstage passes should never exceed 50."""
        items = [Item(None, 5, 45)]
        gilded_rose = GildedRose(items)

        for _ in range(10):
            gilded_rose.update_quality()
            assert items[0].quality <= 50

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_3(self):
        """Quality of Backstage passes should never exceed 50."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", None, 45)]
        gilded_rose = GildedRose(items)

        for _ in range(10):
            gilded_rose.update_quality()
            assert items[0].quality <= 50

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_4(self):
        """Quality of Backstage passes should never exceed 50."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 5, None)]
        gilded_rose = GildedRose(items)

        for _ in range(10):
            gilded_rose.update_quality()
            assert items[0].quality <= 50

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_5(self):
        """Quality of Backstage passes should never exceed 50."""
        items = [Item(5, 45)]
        gilded_rose = GildedRose(items)

        for _ in range(10):
            gilded_rose.update_quality()
            assert items[0].quality <= 50

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_6(self):
        """Quality of Backstage passes should never exceed 50."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 45)]
        gilded_rose = GildedRose(items)

        for _ in range(10):
            gilded_rose.update_quality()
            assert items[0].quality <= 50

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_7(self):
        """Quality of Backstage passes should never exceed 50."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 5, )]
        gilded_rose = GildedRose(items)

        for _ in range(10):
            gilded_rose.update_quality()
            assert items[0].quality <= 50

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_8(self):
        """Quality of Backstage passes should never exceed 50."""
        items = [Item("XXBackstage passes to a TAFKAL80ETC concertXX", 5, 45)]
        gilded_rose = GildedRose(items)

        for _ in range(10):
            gilded_rose.update_quality()
            assert items[0].quality <= 50

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_9(self):
        """Quality of Backstage passes should never exceed 50."""
        items = [Item("backstage passes to a tafkal80etc concert", 5, 45)]
        gilded_rose = GildedRose(items)

        for _ in range(10):
            gilded_rose.update_quality()
            assert items[0].quality <= 50

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_10(self):
        """Quality of Backstage passes should never exceed 50."""
        items = [Item("BACKSTAGE PASSES TO A TAFKAL80ETC CONCERT", 5, 45)]
        gilded_rose = GildedRose(items)

        for _ in range(10):
            gilded_rose.update_quality()
            assert items[0].quality <= 50

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_11(self):
        """Quality of Backstage passes should never exceed 50."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 6, 45)]
        gilded_rose = GildedRose(items)

        for _ in range(10):
            gilded_rose.update_quality()
            assert items[0].quality <= 50

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_12(self):
        """Quality of Backstage passes should never exceed 50."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 5, 46)]
        gilded_rose = GildedRose(items)

        for _ in range(10):
            gilded_rose.update_quality()
            assert items[0].quality <= 50

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_13(self):
        """Quality of Backstage passes should never exceed 50."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 5, 45)]
        gilded_rose = None

        for _ in range(10):
            gilded_rose.update_quality()
            assert items[0].quality <= 50

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_14(self):
        """Quality of Backstage passes should never exceed 50."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 5, 45)]
        gilded_rose = GildedRose(None)

        for _ in range(10):
            gilded_rose.update_quality()
            assert items[0].quality <= 50

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_15(self):
        """Quality of Backstage passes should never exceed 50."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 5, 45)]
        gilded_rose = GildedRose(items)

        for _ in range(None):
            gilded_rose.update_quality()
            assert items[0].quality <= 50

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_16(self):
        """Quality of Backstage passes should never exceed 50."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 5, 45)]
        gilded_rose = GildedRose(items)

        for _ in range(11):
            gilded_rose.update_quality()
            assert items[0].quality <= 50

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_17(self):
        """Quality of Backstage passes should never exceed 50."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 5, 45)]
        gilded_rose = GildedRose(items)

        for _ in range(10):
            gilded_rose.update_quality()
            assert items[1].quality <= 50

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_18(self):
        """Quality of Backstage passes should never exceed 50."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 5, 45)]
        gilded_rose = GildedRose(items)

        for _ in range(10):
            gilded_rose.update_quality()
            assert items[0].quality < 50

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_19(self):
        """Quality of Backstage passes should never exceed 50."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 5, 45)]
        gilded_rose = GildedRose(items)

        for _ in range(10):
            gilded_rose.update_quality()
            assert items[0].quality <= 51
    
    xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_1': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_1, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_2': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_2, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_3': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_3, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_4': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_4, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_5': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_5, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_6': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_6, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_7': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_7, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_8': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_8, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_9': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_9, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_10': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_10, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_11': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_11, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_12': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_12, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_13': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_13, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_14': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_14, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_15': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_15, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_16': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_16, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_17': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_17, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_18': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_18, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_19': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_19
    }
    
    def test_backstage_pass_quality_never_above_50(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_orig"), object.__getattribute__(self, "xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_mutants"), args, kwargs, self)
        return result 
    
    test_backstage_pass_quality_never_above_50.__signature__ = _mutmut_signature(xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_orig)
    xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50__mutmut_orig.__name__ = 'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_quality_never_above_50'

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_orig(self):
        """Backstage pass quality becomes 0 the day after concert."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 0, 50)]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 0
        assert items[0].sell_in == -1

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_1(self):
        """Backstage pass quality becomes 0 the day after concert."""
        items = None
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 0
        assert items[0].sell_in == -1

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_2(self):
        """Backstage pass quality becomes 0 the day after concert."""
        items = [Item(None, 0, 50)]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 0
        assert items[0].sell_in == -1

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_3(self):
        """Backstage pass quality becomes 0 the day after concert."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", None, 50)]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 0
        assert items[0].sell_in == -1

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_4(self):
        """Backstage pass quality becomes 0 the day after concert."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 0, None)]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 0
        assert items[0].sell_in == -1

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_5(self):
        """Backstage pass quality becomes 0 the day after concert."""
        items = [Item(0, 50)]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 0
        assert items[0].sell_in == -1

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_6(self):
        """Backstage pass quality becomes 0 the day after concert."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 50)]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 0
        assert items[0].sell_in == -1

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_7(self):
        """Backstage pass quality becomes 0 the day after concert."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 0, )]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 0
        assert items[0].sell_in == -1

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_8(self):
        """Backstage pass quality becomes 0 the day after concert."""
        items = [Item("XXBackstage passes to a TAFKAL80ETC concertXX", 0, 50)]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 0
        assert items[0].sell_in == -1

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_9(self):
        """Backstage pass quality becomes 0 the day after concert."""
        items = [Item("backstage passes to a tafkal80etc concert", 0, 50)]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 0
        assert items[0].sell_in == -1

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_10(self):
        """Backstage pass quality becomes 0 the day after concert."""
        items = [Item("BACKSTAGE PASSES TO A TAFKAL80ETC CONCERT", 0, 50)]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 0
        assert items[0].sell_in == -1

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_11(self):
        """Backstage pass quality becomes 0 the day after concert."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 1, 50)]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 0
        assert items[0].sell_in == -1

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_12(self):
        """Backstage pass quality becomes 0 the day after concert."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 0, 51)]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 0
        assert items[0].sell_in == -1

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_13(self):
        """Backstage pass quality becomes 0 the day after concert."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 0, 50)]
        gilded_rose = None
        gilded_rose.update_quality()

        assert items[0].quality == 0
        assert items[0].sell_in == -1

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_14(self):
        """Backstage pass quality becomes 0 the day after concert."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 0, 50)]
        gilded_rose = GildedRose(None)
        gilded_rose.update_quality()

        assert items[0].quality == 0
        assert items[0].sell_in == -1

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_15(self):
        """Backstage pass quality becomes 0 the day after concert."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 0, 50)]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[1].quality == 0
        assert items[0].sell_in == -1

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_16(self):
        """Backstage pass quality becomes 0 the day after concert."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 0, 50)]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality != 0
        assert items[0].sell_in == -1

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_17(self):
        """Backstage pass quality becomes 0 the day after concert."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 0, 50)]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 1
        assert items[0].sell_in == -1

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_18(self):
        """Backstage pass quality becomes 0 the day after concert."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 0, 50)]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 0
        assert items[1].sell_in == -1

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_19(self):
        """Backstage pass quality becomes 0 the day after concert."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 0, 50)]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 0
        assert items[0].sell_in != -1

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_20(self):
        """Backstage pass quality becomes 0 the day after concert."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 0, 50)]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 0
        assert items[0].sell_in == +1

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_21(self):
        """Backstage pass quality becomes 0 the day after concert."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 0, 50)]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 0
        assert items[0].sell_in == -2
    
    xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_1': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_1, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_2': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_2, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_3': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_3, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_4': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_4, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_5': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_5, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_6': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_6, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_7': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_7, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_8': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_8, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_9': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_9, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_10': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_10, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_11': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_11, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_12': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_12, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_13': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_13, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_14': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_14, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_15': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_15, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_16': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_16, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_17': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_17, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_18': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_18, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_19': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_19, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_20': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_20, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_21': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_21
    }
    
    def test_backstage_pass_drops_to_zero_immediately_after_concert(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_orig"), object.__getattribute__(self, "xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_mutants"), args, kwargs, self)
        return result 
    
    test_backstage_pass_drops_to_zero_immediately_after_concert.__signature__ = _mutmut_signature(xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_orig)
    xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert__mutmut_orig.__name__ = 'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_backstage_pass_drops_to_zero_immediately_after_concert'

    @pytest.mark.parametrize("quality", [0, 1, 25, 49, 50])
    def test_normal_item_with_various_qualities(self, quality):
        """Normal items work correctly with all quality levels."""
        items = [Item("Normal Item", 10, quality)]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        expected = max(0, quality - 1)
        assert items[0].quality == expected

    @pytest.mark.parametrize("quality", [0, 1, 25, 49, 50])
    def test_aged_brie_with_various_qualities(self, quality):
        """Aged Brie works correctly with all quality levels."""
        items = [Item("Aged Brie", 10, quality)]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        expected = min(50, quality + 1)
        assert items[0].quality == expected

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_orig(self):
        """Test Item __repr__ method."""
        item = Item("Test Item", 5, 25)
        assert repr(item) == "Test Item, 5, 25"

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_1(self):
        """Test Item __repr__ method."""
        item = None
        assert repr(item) == "Test Item, 5, 25"

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_2(self):
        """Test Item __repr__ method."""
        item = Item(None, 5, 25)
        assert repr(item) == "Test Item, 5, 25"

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_3(self):
        """Test Item __repr__ method."""
        item = Item("Test Item", None, 25)
        assert repr(item) == "Test Item, 5, 25"

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_4(self):
        """Test Item __repr__ method."""
        item = Item("Test Item", 5, None)
        assert repr(item) == "Test Item, 5, 25"

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_5(self):
        """Test Item __repr__ method."""
        item = Item(5, 25)
        assert repr(item) == "Test Item, 5, 25"

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_6(self):
        """Test Item __repr__ method."""
        item = Item("Test Item", 25)
        assert repr(item) == "Test Item, 5, 25"

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_7(self):
        """Test Item __repr__ method."""
        item = Item("Test Item", 5, )
        assert repr(item) == "Test Item, 5, 25"

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_8(self):
        """Test Item __repr__ method."""
        item = Item("XXTest ItemXX", 5, 25)
        assert repr(item) == "Test Item, 5, 25"

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_9(self):
        """Test Item __repr__ method."""
        item = Item("test item", 5, 25)
        assert repr(item) == "Test Item, 5, 25"

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_10(self):
        """Test Item __repr__ method."""
        item = Item("TEST ITEM", 5, 25)
        assert repr(item) == "Test Item, 5, 25"

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_11(self):
        """Test Item __repr__ method."""
        item = Item("Test Item", 6, 25)
        assert repr(item) == "Test Item, 5, 25"

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_12(self):
        """Test Item __repr__ method."""
        item = Item("Test Item", 5, 26)
        assert repr(item) == "Test Item, 5, 25"

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_13(self):
        """Test Item __repr__ method."""
        item = Item("Test Item", 5, 25)
        assert repr(None) == "Test Item, 5, 25"

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_14(self):
        """Test Item __repr__ method."""
        item = Item("Test Item", 5, 25)
        assert repr(item) != "Test Item, 5, 25"

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_15(self):
        """Test Item __repr__ method."""
        item = Item("Test Item", 5, 25)
        assert repr(item) == "XXTest Item, 5, 25XX"

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_16(self):
        """Test Item __repr__ method."""
        item = Item("Test Item", 5, 25)
        assert repr(item) == "test item, 5, 25"

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_17(self):
        """Test Item __repr__ method."""
        item = Item("Test Item", 5, 25)
        assert repr(item) == "TEST ITEM, 5, 25"
    
    xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_1': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_1, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_2': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_2, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_3': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_3, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_4': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_4, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_5': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_5, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_6': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_6, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_7': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_7, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_8': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_8, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_9': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_9, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_10': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_10, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_11': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_11, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_12': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_12, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_13': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_13, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_14': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_14, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_15': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_15, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_16': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_16, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_17': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_17
    }
    
    def test_item_representation(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_orig"), object.__getattribute__(self, "xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_mutants"), args, kwargs, self)
        return result 
    
    test_item_representation.__signature__ = _mutmut_signature(xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_orig)
    xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation__mutmut_orig.__name__ = 'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_item_representation'

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_orig(self):
        """Test GildedRose initialization."""
        items = [Item("Test", 5, 25)]
        gilded_rose = GildedRose(items)

        assert gilded_rose.items == items
        assert len(gilded_rose.items) == 1

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_1(self):
        """Test GildedRose initialization."""
        items = None
        gilded_rose = GildedRose(items)

        assert gilded_rose.items == items
        assert len(gilded_rose.items) == 1

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_2(self):
        """Test GildedRose initialization."""
        items = [Item(None, 5, 25)]
        gilded_rose = GildedRose(items)

        assert gilded_rose.items == items
        assert len(gilded_rose.items) == 1

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_3(self):
        """Test GildedRose initialization."""
        items = [Item("Test", None, 25)]
        gilded_rose = GildedRose(items)

        assert gilded_rose.items == items
        assert len(gilded_rose.items) == 1

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_4(self):
        """Test GildedRose initialization."""
        items = [Item("Test", 5, None)]
        gilded_rose = GildedRose(items)

        assert gilded_rose.items == items
        assert len(gilded_rose.items) == 1

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_5(self):
        """Test GildedRose initialization."""
        items = [Item(5, 25)]
        gilded_rose = GildedRose(items)

        assert gilded_rose.items == items
        assert len(gilded_rose.items) == 1

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_6(self):
        """Test GildedRose initialization."""
        items = [Item("Test", 25)]
        gilded_rose = GildedRose(items)

        assert gilded_rose.items == items
        assert len(gilded_rose.items) == 1

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_7(self):
        """Test GildedRose initialization."""
        items = [Item("Test", 5, )]
        gilded_rose = GildedRose(items)

        assert gilded_rose.items == items
        assert len(gilded_rose.items) == 1

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_8(self):
        """Test GildedRose initialization."""
        items = [Item("XXTestXX", 5, 25)]
        gilded_rose = GildedRose(items)

        assert gilded_rose.items == items
        assert len(gilded_rose.items) == 1

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_9(self):
        """Test GildedRose initialization."""
        items = [Item("test", 5, 25)]
        gilded_rose = GildedRose(items)

        assert gilded_rose.items == items
        assert len(gilded_rose.items) == 1

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_10(self):
        """Test GildedRose initialization."""
        items = [Item("TEST", 5, 25)]
        gilded_rose = GildedRose(items)

        assert gilded_rose.items == items
        assert len(gilded_rose.items) == 1

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_11(self):
        """Test GildedRose initialization."""
        items = [Item("Test", 6, 25)]
        gilded_rose = GildedRose(items)

        assert gilded_rose.items == items
        assert len(gilded_rose.items) == 1

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_12(self):
        """Test GildedRose initialization."""
        items = [Item("Test", 5, 26)]
        gilded_rose = GildedRose(items)

        assert gilded_rose.items == items
        assert len(gilded_rose.items) == 1

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_13(self):
        """Test GildedRose initialization."""
        items = [Item("Test", 5, 25)]
        gilded_rose = None

        assert gilded_rose.items == items
        assert len(gilded_rose.items) == 1

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_14(self):
        """Test GildedRose initialization."""
        items = [Item("Test", 5, 25)]
        gilded_rose = GildedRose(None)

        assert gilded_rose.items == items
        assert len(gilded_rose.items) == 1

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_15(self):
        """Test GildedRose initialization."""
        items = [Item("Test", 5, 25)]
        gilded_rose = GildedRose(items)

        assert gilded_rose.items != items
        assert len(gilded_rose.items) == 1

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_16(self):
        """Test GildedRose initialization."""
        items = [Item("Test", 5, 25)]
        gilded_rose = GildedRose(items)

        assert gilded_rose.items == items
        assert len(gilded_rose.items) != 1

    def xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_17(self):
        """Test GildedRose initialization."""
        items = [Item("Test", 5, 25)]
        gilded_rose = GildedRose(items)

        assert gilded_rose.items == items
        assert len(gilded_rose.items) == 2
    
    xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_1': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_1, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_2': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_2, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_3': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_3, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_4': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_4, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_5': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_5, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_6': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_6, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_7': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_7, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_8': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_8, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_9': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_9, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_10': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_10, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_11': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_11, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_12': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_12, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_13': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_13, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_14': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_14, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_15': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_15, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_16': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_16, 
        'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_17': xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_17
    }
    
    def test_gilded_rose_initialization(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_orig"), object.__getattribute__(self, "xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_mutants"), args, kwargs, self)
        return result 
    
    test_gilded_rose_initialization.__signature__ = _mutmut_signature(xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_orig)
    xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization__mutmut_orig.__name__ = 'xǁTestGildedRoseEdgeCasesAndBoundariesǁtest_gilded_rose_initialization'


class TestGildedRoseQualityCap:
    """Tests specifically for quality boundary conditions (0 and 50)."""

    @pytest.mark.parametrize(
        "item_name,initial_quality,initial_sell_in",
        [
            ("Aged Brie", 50, 10),
            ("Backstage passes to a TAFKAL80ETC concert", 50, 10),
        ],
    )
    def test_quality_respects_upper_limit_50(
        self, item_name, initial_quality, initial_sell_in
    ):
        """Quality should never exceed 50."""
        items = [Item(item_name, initial_sell_in, initial_quality)]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 50

    @pytest.mark.parametrize(
        "item_name,initial_quality,initial_sell_in",
        [
            ("Normal Item", 0, 10),
            ("Normal Item", 0, -1),
        ],
    )
    def test_quality_respects_lower_limit_0(
        self, item_name, initial_quality, initial_sell_in
    ):
        """Quality should never be negative."""
        items = [Item(item_name, initial_sell_in, initial_quality)]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].quality == 0


class TestGildedRoseSellInBehavior:
    """Tests specifically for sell_in behavior."""

    @pytest.mark.parametrize(
        "item_name,initial_sell_in,expected_sell_in",
        [
            ("Normal Item", 10, 9),
            ("Aged Brie", 5, 4),
            ("Backstage passes to a TAFKAL80ETC concert", 3, 2),
            ("Normal Item", 0, -1),
            ("Normal Item", -5, -6),
        ],
    )
    def test_sell_in_decreases_except_sulfuras(self, item_name, initial_sell_in, expected_sell_in):
        """sell_in should decrease by 1 each day for all items except Sulfuras."""
        items = [Item(item_name, initial_sell_in, 25)]
        gilded_rose = GildedRose(items)
        gilded_rose.update_quality()

        assert items[0].sell_in == expected_sell_in

    def xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_orig(self):
        """Sulfuras sell_in should never decrease."""
        items = [Item("Sulfuras, Hand of Ragnaros", 10, 80)]
        gilded_rose = GildedRose(items)

        for _ in range(5):
            gilded_rose.update_quality()
            assert items[0].sell_in == 10

    def xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_1(self):
        """Sulfuras sell_in should never decrease."""
        items = None
        gilded_rose = GildedRose(items)

        for _ in range(5):
            gilded_rose.update_quality()
            assert items[0].sell_in == 10

    def xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_2(self):
        """Sulfuras sell_in should never decrease."""
        items = [Item(None, 10, 80)]
        gilded_rose = GildedRose(items)

        for _ in range(5):
            gilded_rose.update_quality()
            assert items[0].sell_in == 10

    def xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_3(self):
        """Sulfuras sell_in should never decrease."""
        items = [Item("Sulfuras, Hand of Ragnaros", None, 80)]
        gilded_rose = GildedRose(items)

        for _ in range(5):
            gilded_rose.update_quality()
            assert items[0].sell_in == 10

    def xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_4(self):
        """Sulfuras sell_in should never decrease."""
        items = [Item("Sulfuras, Hand of Ragnaros", 10, None)]
        gilded_rose = GildedRose(items)

        for _ in range(5):
            gilded_rose.update_quality()
            assert items[0].sell_in == 10

    def xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_5(self):
        """Sulfuras sell_in should never decrease."""
        items = [Item(10, 80)]
        gilded_rose = GildedRose(items)

        for _ in range(5):
            gilded_rose.update_quality()
            assert items[0].sell_in == 10

    def xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_6(self):
        """Sulfuras sell_in should never decrease."""
        items = [Item("Sulfuras, Hand of Ragnaros", 80)]
        gilded_rose = GildedRose(items)

        for _ in range(5):
            gilded_rose.update_quality()
            assert items[0].sell_in == 10

    def xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_7(self):
        """Sulfuras sell_in should never decrease."""
        items = [Item("Sulfuras, Hand of Ragnaros", 10, )]
        gilded_rose = GildedRose(items)

        for _ in range(5):
            gilded_rose.update_quality()
            assert items[0].sell_in == 10

    def xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_8(self):
        """Sulfuras sell_in should never decrease."""
        items = [Item("XXSulfuras, Hand of RagnarosXX", 10, 80)]
        gilded_rose = GildedRose(items)

        for _ in range(5):
            gilded_rose.update_quality()
            assert items[0].sell_in == 10

    def xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_9(self):
        """Sulfuras sell_in should never decrease."""
        items = [Item("sulfuras, hand of ragnaros", 10, 80)]
        gilded_rose = GildedRose(items)

        for _ in range(5):
            gilded_rose.update_quality()
            assert items[0].sell_in == 10

    def xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_10(self):
        """Sulfuras sell_in should never decrease."""
        items = [Item("SULFURAS, HAND OF RAGNAROS", 10, 80)]
        gilded_rose = GildedRose(items)

        for _ in range(5):
            gilded_rose.update_quality()
            assert items[0].sell_in == 10

    def xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_11(self):
        """Sulfuras sell_in should never decrease."""
        items = [Item("Sulfuras, Hand of Ragnaros", 11, 80)]
        gilded_rose = GildedRose(items)

        for _ in range(5):
            gilded_rose.update_quality()
            assert items[0].sell_in == 10

    def xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_12(self):
        """Sulfuras sell_in should never decrease."""
        items = [Item("Sulfuras, Hand of Ragnaros", 10, 81)]
        gilded_rose = GildedRose(items)

        for _ in range(5):
            gilded_rose.update_quality()
            assert items[0].sell_in == 10

    def xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_13(self):
        """Sulfuras sell_in should never decrease."""
        items = [Item("Sulfuras, Hand of Ragnaros", 10, 80)]
        gilded_rose = None

        for _ in range(5):
            gilded_rose.update_quality()
            assert items[0].sell_in == 10

    def xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_14(self):
        """Sulfuras sell_in should never decrease."""
        items = [Item("Sulfuras, Hand of Ragnaros", 10, 80)]
        gilded_rose = GildedRose(None)

        for _ in range(5):
            gilded_rose.update_quality()
            assert items[0].sell_in == 10

    def xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_15(self):
        """Sulfuras sell_in should never decrease."""
        items = [Item("Sulfuras, Hand of Ragnaros", 10, 80)]
        gilded_rose = GildedRose(items)

        for _ in range(None):
            gilded_rose.update_quality()
            assert items[0].sell_in == 10

    def xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_16(self):
        """Sulfuras sell_in should never decrease."""
        items = [Item("Sulfuras, Hand of Ragnaros", 10, 80)]
        gilded_rose = GildedRose(items)

        for _ in range(6):
            gilded_rose.update_quality()
            assert items[0].sell_in == 10

    def xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_17(self):
        """Sulfuras sell_in should never decrease."""
        items = [Item("Sulfuras, Hand of Ragnaros", 10, 80)]
        gilded_rose = GildedRose(items)

        for _ in range(5):
            gilded_rose.update_quality()
            assert items[1].sell_in == 10

    def xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_18(self):
        """Sulfuras sell_in should never decrease."""
        items = [Item("Sulfuras, Hand of Ragnaros", 10, 80)]
        gilded_rose = GildedRose(items)

        for _ in range(5):
            gilded_rose.update_quality()
            assert items[0].sell_in != 10

    def xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_19(self):
        """Sulfuras sell_in should never decrease."""
        items = [Item("Sulfuras, Hand of Ragnaros", 10, 80)]
        gilded_rose = GildedRose(items)

        for _ in range(5):
            gilded_rose.update_quality()
            assert items[0].sell_in == 11
    
    xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_1': xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_1, 
        'xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_2': xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_2, 
        'xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_3': xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_3, 
        'xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_4': xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_4, 
        'xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_5': xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_5, 
        'xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_6': xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_6, 
        'xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_7': xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_7, 
        'xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_8': xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_8, 
        'xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_9': xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_9, 
        'xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_10': xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_10, 
        'xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_11': xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_11, 
        'xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_12': xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_12, 
        'xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_13': xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_13, 
        'xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_14': xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_14, 
        'xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_15': xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_15, 
        'xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_16': xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_16, 
        'xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_17': xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_17, 
        'xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_18': xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_18, 
        'xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_19': xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_19
    }
    
    def test_sulfuras_sell_in_never_decreases(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_orig"), object.__getattribute__(self, "xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_mutants"), args, kwargs, self)
        return result 
    
    test_sulfuras_sell_in_never_decreases.__signature__ = _mutmut_signature(xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_orig)
    xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases__mutmut_orig.__name__ = 'xǁTestGildedRoseSellInBehaviorǁtest_sulfuras_sell_in_never_decreases'


class TestGildedRoseSequentialUpdates:
    """Tests for items over multiple update cycles."""

    def xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_orig(self):
        """Normal item should degrade consistently over multiple days."""
        items = [Item("Normal Item", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 9, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 9
        assert items[0].sell_in == 2

        # Day 2: quality 9 -> 8, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 8
        assert items[0].sell_in == 1

        # Day 3: quality 8 -> 7, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 7
        assert items[0].sell_in == 0

        # Day 4: quality 7 -> 5 (double degradation), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 5
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_1(self):
        """Normal item should degrade consistently over multiple days."""
        items = None
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 9, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 9
        assert items[0].sell_in == 2

        # Day 2: quality 9 -> 8, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 8
        assert items[0].sell_in == 1

        # Day 3: quality 8 -> 7, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 7
        assert items[0].sell_in == 0

        # Day 4: quality 7 -> 5 (double degradation), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 5
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_2(self):
        """Normal item should degrade consistently over multiple days."""
        items = [Item(None, 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 9, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 9
        assert items[0].sell_in == 2

        # Day 2: quality 9 -> 8, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 8
        assert items[0].sell_in == 1

        # Day 3: quality 8 -> 7, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 7
        assert items[0].sell_in == 0

        # Day 4: quality 7 -> 5 (double degradation), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 5
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_3(self):
        """Normal item should degrade consistently over multiple days."""
        items = [Item("Normal Item", None, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 9, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 9
        assert items[0].sell_in == 2

        # Day 2: quality 9 -> 8, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 8
        assert items[0].sell_in == 1

        # Day 3: quality 8 -> 7, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 7
        assert items[0].sell_in == 0

        # Day 4: quality 7 -> 5 (double degradation), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 5
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_4(self):
        """Normal item should degrade consistently over multiple days."""
        items = [Item("Normal Item", 3, None)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 9, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 9
        assert items[0].sell_in == 2

        # Day 2: quality 9 -> 8, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 8
        assert items[0].sell_in == 1

        # Day 3: quality 8 -> 7, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 7
        assert items[0].sell_in == 0

        # Day 4: quality 7 -> 5 (double degradation), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 5
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_5(self):
        """Normal item should degrade consistently over multiple days."""
        items = [Item(3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 9, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 9
        assert items[0].sell_in == 2

        # Day 2: quality 9 -> 8, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 8
        assert items[0].sell_in == 1

        # Day 3: quality 8 -> 7, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 7
        assert items[0].sell_in == 0

        # Day 4: quality 7 -> 5 (double degradation), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 5
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_6(self):
        """Normal item should degrade consistently over multiple days."""
        items = [Item("Normal Item", 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 9, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 9
        assert items[0].sell_in == 2

        # Day 2: quality 9 -> 8, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 8
        assert items[0].sell_in == 1

        # Day 3: quality 8 -> 7, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 7
        assert items[0].sell_in == 0

        # Day 4: quality 7 -> 5 (double degradation), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 5
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_7(self):
        """Normal item should degrade consistently over multiple days."""
        items = [Item("Normal Item", 3, )]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 9, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 9
        assert items[0].sell_in == 2

        # Day 2: quality 9 -> 8, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 8
        assert items[0].sell_in == 1

        # Day 3: quality 8 -> 7, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 7
        assert items[0].sell_in == 0

        # Day 4: quality 7 -> 5 (double degradation), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 5
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_8(self):
        """Normal item should degrade consistently over multiple days."""
        items = [Item("XXNormal ItemXX", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 9, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 9
        assert items[0].sell_in == 2

        # Day 2: quality 9 -> 8, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 8
        assert items[0].sell_in == 1

        # Day 3: quality 8 -> 7, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 7
        assert items[0].sell_in == 0

        # Day 4: quality 7 -> 5 (double degradation), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 5
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_9(self):
        """Normal item should degrade consistently over multiple days."""
        items = [Item("normal item", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 9, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 9
        assert items[0].sell_in == 2

        # Day 2: quality 9 -> 8, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 8
        assert items[0].sell_in == 1

        # Day 3: quality 8 -> 7, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 7
        assert items[0].sell_in == 0

        # Day 4: quality 7 -> 5 (double degradation), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 5
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_10(self):
        """Normal item should degrade consistently over multiple days."""
        items = [Item("NORMAL ITEM", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 9, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 9
        assert items[0].sell_in == 2

        # Day 2: quality 9 -> 8, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 8
        assert items[0].sell_in == 1

        # Day 3: quality 8 -> 7, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 7
        assert items[0].sell_in == 0

        # Day 4: quality 7 -> 5 (double degradation), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 5
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_11(self):
        """Normal item should degrade consistently over multiple days."""
        items = [Item("Normal Item", 4, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 9, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 9
        assert items[0].sell_in == 2

        # Day 2: quality 9 -> 8, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 8
        assert items[0].sell_in == 1

        # Day 3: quality 8 -> 7, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 7
        assert items[0].sell_in == 0

        # Day 4: quality 7 -> 5 (double degradation), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 5
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_12(self):
        """Normal item should degrade consistently over multiple days."""
        items = [Item("Normal Item", 3, 11)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 9, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 9
        assert items[0].sell_in == 2

        # Day 2: quality 9 -> 8, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 8
        assert items[0].sell_in == 1

        # Day 3: quality 8 -> 7, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 7
        assert items[0].sell_in == 0

        # Day 4: quality 7 -> 5 (double degradation), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 5
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_13(self):
        """Normal item should degrade consistently over multiple days."""
        items = [Item("Normal Item", 3, 10)]
        gilded_rose = None

        # Day 1: quality 10 -> 9, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 9
        assert items[0].sell_in == 2

        # Day 2: quality 9 -> 8, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 8
        assert items[0].sell_in == 1

        # Day 3: quality 8 -> 7, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 7
        assert items[0].sell_in == 0

        # Day 4: quality 7 -> 5 (double degradation), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 5
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_14(self):
        """Normal item should degrade consistently over multiple days."""
        items = [Item("Normal Item", 3, 10)]
        gilded_rose = GildedRose(None)

        # Day 1: quality 10 -> 9, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 9
        assert items[0].sell_in == 2

        # Day 2: quality 9 -> 8, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 8
        assert items[0].sell_in == 1

        # Day 3: quality 8 -> 7, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 7
        assert items[0].sell_in == 0

        # Day 4: quality 7 -> 5 (double degradation), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 5
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_15(self):
        """Normal item should degrade consistently over multiple days."""
        items = [Item("Normal Item", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 9, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[1].quality == 9
        assert items[0].sell_in == 2

        # Day 2: quality 9 -> 8, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 8
        assert items[0].sell_in == 1

        # Day 3: quality 8 -> 7, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 7
        assert items[0].sell_in == 0

        # Day 4: quality 7 -> 5 (double degradation), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 5
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_16(self):
        """Normal item should degrade consistently over multiple days."""
        items = [Item("Normal Item", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 9, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality != 9
        assert items[0].sell_in == 2

        # Day 2: quality 9 -> 8, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 8
        assert items[0].sell_in == 1

        # Day 3: quality 8 -> 7, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 7
        assert items[0].sell_in == 0

        # Day 4: quality 7 -> 5 (double degradation), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 5
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_17(self):
        """Normal item should degrade consistently over multiple days."""
        items = [Item("Normal Item", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 9, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 10
        assert items[0].sell_in == 2

        # Day 2: quality 9 -> 8, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 8
        assert items[0].sell_in == 1

        # Day 3: quality 8 -> 7, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 7
        assert items[0].sell_in == 0

        # Day 4: quality 7 -> 5 (double degradation), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 5
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_18(self):
        """Normal item should degrade consistently over multiple days."""
        items = [Item("Normal Item", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 9, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 9
        assert items[1].sell_in == 2

        # Day 2: quality 9 -> 8, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 8
        assert items[0].sell_in == 1

        # Day 3: quality 8 -> 7, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 7
        assert items[0].sell_in == 0

        # Day 4: quality 7 -> 5 (double degradation), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 5
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_19(self):
        """Normal item should degrade consistently over multiple days."""
        items = [Item("Normal Item", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 9, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 9
        assert items[0].sell_in != 2

        # Day 2: quality 9 -> 8, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 8
        assert items[0].sell_in == 1

        # Day 3: quality 8 -> 7, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 7
        assert items[0].sell_in == 0

        # Day 4: quality 7 -> 5 (double degradation), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 5
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_20(self):
        """Normal item should degrade consistently over multiple days."""
        items = [Item("Normal Item", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 9, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 9
        assert items[0].sell_in == 3

        # Day 2: quality 9 -> 8, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 8
        assert items[0].sell_in == 1

        # Day 3: quality 8 -> 7, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 7
        assert items[0].sell_in == 0

        # Day 4: quality 7 -> 5 (double degradation), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 5
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_21(self):
        """Normal item should degrade consistently over multiple days."""
        items = [Item("Normal Item", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 9, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 9
        assert items[0].sell_in == 2

        # Day 2: quality 9 -> 8, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[1].quality == 8
        assert items[0].sell_in == 1

        # Day 3: quality 8 -> 7, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 7
        assert items[0].sell_in == 0

        # Day 4: quality 7 -> 5 (double degradation), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 5
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_22(self):
        """Normal item should degrade consistently over multiple days."""
        items = [Item("Normal Item", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 9, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 9
        assert items[0].sell_in == 2

        # Day 2: quality 9 -> 8, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality != 8
        assert items[0].sell_in == 1

        # Day 3: quality 8 -> 7, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 7
        assert items[0].sell_in == 0

        # Day 4: quality 7 -> 5 (double degradation), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 5
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_23(self):
        """Normal item should degrade consistently over multiple days."""
        items = [Item("Normal Item", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 9, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 9
        assert items[0].sell_in == 2

        # Day 2: quality 9 -> 8, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 9
        assert items[0].sell_in == 1

        # Day 3: quality 8 -> 7, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 7
        assert items[0].sell_in == 0

        # Day 4: quality 7 -> 5 (double degradation), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 5
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_24(self):
        """Normal item should degrade consistently over multiple days."""
        items = [Item("Normal Item", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 9, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 9
        assert items[0].sell_in == 2

        # Day 2: quality 9 -> 8, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 8
        assert items[1].sell_in == 1

        # Day 3: quality 8 -> 7, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 7
        assert items[0].sell_in == 0

        # Day 4: quality 7 -> 5 (double degradation), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 5
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_25(self):
        """Normal item should degrade consistently over multiple days."""
        items = [Item("Normal Item", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 9, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 9
        assert items[0].sell_in == 2

        # Day 2: quality 9 -> 8, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 8
        assert items[0].sell_in != 1

        # Day 3: quality 8 -> 7, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 7
        assert items[0].sell_in == 0

        # Day 4: quality 7 -> 5 (double degradation), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 5
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_26(self):
        """Normal item should degrade consistently over multiple days."""
        items = [Item("Normal Item", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 9, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 9
        assert items[0].sell_in == 2

        # Day 2: quality 9 -> 8, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 8
        assert items[0].sell_in == 2

        # Day 3: quality 8 -> 7, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 7
        assert items[0].sell_in == 0

        # Day 4: quality 7 -> 5 (double degradation), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 5
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_27(self):
        """Normal item should degrade consistently over multiple days."""
        items = [Item("Normal Item", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 9, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 9
        assert items[0].sell_in == 2

        # Day 2: quality 9 -> 8, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 8
        assert items[0].sell_in == 1

        # Day 3: quality 8 -> 7, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[1].quality == 7
        assert items[0].sell_in == 0

        # Day 4: quality 7 -> 5 (double degradation), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 5
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_28(self):
        """Normal item should degrade consistently over multiple days."""
        items = [Item("Normal Item", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 9, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 9
        assert items[0].sell_in == 2

        # Day 2: quality 9 -> 8, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 8
        assert items[0].sell_in == 1

        # Day 3: quality 8 -> 7, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality != 7
        assert items[0].sell_in == 0

        # Day 4: quality 7 -> 5 (double degradation), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 5
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_29(self):
        """Normal item should degrade consistently over multiple days."""
        items = [Item("Normal Item", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 9, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 9
        assert items[0].sell_in == 2

        # Day 2: quality 9 -> 8, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 8
        assert items[0].sell_in == 1

        # Day 3: quality 8 -> 7, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 8
        assert items[0].sell_in == 0

        # Day 4: quality 7 -> 5 (double degradation), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 5
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_30(self):
        """Normal item should degrade consistently over multiple days."""
        items = [Item("Normal Item", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 9, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 9
        assert items[0].sell_in == 2

        # Day 2: quality 9 -> 8, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 8
        assert items[0].sell_in == 1

        # Day 3: quality 8 -> 7, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 7
        assert items[1].sell_in == 0

        # Day 4: quality 7 -> 5 (double degradation), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 5
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_31(self):
        """Normal item should degrade consistently over multiple days."""
        items = [Item("Normal Item", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 9, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 9
        assert items[0].sell_in == 2

        # Day 2: quality 9 -> 8, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 8
        assert items[0].sell_in == 1

        # Day 3: quality 8 -> 7, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 7
        assert items[0].sell_in != 0

        # Day 4: quality 7 -> 5 (double degradation), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 5
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_32(self):
        """Normal item should degrade consistently over multiple days."""
        items = [Item("Normal Item", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 9, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 9
        assert items[0].sell_in == 2

        # Day 2: quality 9 -> 8, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 8
        assert items[0].sell_in == 1

        # Day 3: quality 8 -> 7, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 7
        assert items[0].sell_in == 1

        # Day 4: quality 7 -> 5 (double degradation), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 5
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_33(self):
        """Normal item should degrade consistently over multiple days."""
        items = [Item("Normal Item", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 9, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 9
        assert items[0].sell_in == 2

        # Day 2: quality 9 -> 8, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 8
        assert items[0].sell_in == 1

        # Day 3: quality 8 -> 7, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 7
        assert items[0].sell_in == 0

        # Day 4: quality 7 -> 5 (double degradation), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[1].quality == 5
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_34(self):
        """Normal item should degrade consistently over multiple days."""
        items = [Item("Normal Item", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 9, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 9
        assert items[0].sell_in == 2

        # Day 2: quality 9 -> 8, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 8
        assert items[0].sell_in == 1

        # Day 3: quality 8 -> 7, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 7
        assert items[0].sell_in == 0

        # Day 4: quality 7 -> 5 (double degradation), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality != 5
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_35(self):
        """Normal item should degrade consistently over multiple days."""
        items = [Item("Normal Item", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 9, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 9
        assert items[0].sell_in == 2

        # Day 2: quality 9 -> 8, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 8
        assert items[0].sell_in == 1

        # Day 3: quality 8 -> 7, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 7
        assert items[0].sell_in == 0

        # Day 4: quality 7 -> 5 (double degradation), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 6
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_36(self):
        """Normal item should degrade consistently over multiple days."""
        items = [Item("Normal Item", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 9, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 9
        assert items[0].sell_in == 2

        # Day 2: quality 9 -> 8, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 8
        assert items[0].sell_in == 1

        # Day 3: quality 8 -> 7, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 7
        assert items[0].sell_in == 0

        # Day 4: quality 7 -> 5 (double degradation), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 5
        assert items[1].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_37(self):
        """Normal item should degrade consistently over multiple days."""
        items = [Item("Normal Item", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 9, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 9
        assert items[0].sell_in == 2

        # Day 2: quality 9 -> 8, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 8
        assert items[0].sell_in == 1

        # Day 3: quality 8 -> 7, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 7
        assert items[0].sell_in == 0

        # Day 4: quality 7 -> 5 (double degradation), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 5
        assert items[0].sell_in != -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_38(self):
        """Normal item should degrade consistently over multiple days."""
        items = [Item("Normal Item", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 9, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 9
        assert items[0].sell_in == 2

        # Day 2: quality 9 -> 8, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 8
        assert items[0].sell_in == 1

        # Day 3: quality 8 -> 7, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 7
        assert items[0].sell_in == 0

        # Day 4: quality 7 -> 5 (double degradation), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 5
        assert items[0].sell_in == +1

    def xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_39(self):
        """Normal item should degrade consistently over multiple days."""
        items = [Item("Normal Item", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 9, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 9
        assert items[0].sell_in == 2

        # Day 2: quality 9 -> 8, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 8
        assert items[0].sell_in == 1

        # Day 3: quality 8 -> 7, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 7
        assert items[0].sell_in == 0

        # Day 4: quality 7 -> 5 (double degradation), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 5
        assert items[0].sell_in == -2
    
    xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_1': xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_1, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_2': xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_2, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_3': xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_3, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_4': xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_4, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_5': xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_5, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_6': xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_6, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_7': xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_7, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_8': xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_8, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_9': xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_9, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_10': xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_10, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_11': xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_11, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_12': xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_12, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_13': xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_13, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_14': xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_14, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_15': xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_15, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_16': xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_16, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_17': xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_17, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_18': xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_18, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_19': xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_19, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_20': xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_20, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_21': xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_21, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_22': xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_22, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_23': xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_23, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_24': xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_24, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_25': xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_25, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_26': xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_26, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_27': xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_27, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_28': xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_28, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_29': xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_29, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_30': xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_30, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_31': xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_31, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_32': xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_32, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_33': xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_33, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_34': xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_34, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_35': xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_35, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_36': xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_36, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_37': xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_37, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_38': xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_38, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_39': xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_39
    }
    
    def test_normal_item_over_multiple_days(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_orig"), object.__getattribute__(self, "xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_mutants"), args, kwargs, self)
        return result 
    
    test_normal_item_over_multiple_days.__signature__ = _mutmut_signature(xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_orig)
    xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days__mutmut_orig.__name__ = 'xǁTestGildedRoseSequentialUpdatesǁtest_normal_item_over_multiple_days'

    def xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_orig(self):
        """Aged Brie should improve consistently over multiple days."""
        items = [Item("Aged Brie", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 11, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 11
        assert items[0].sell_in == 2

        # Day 2: quality 11 -> 12, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 12
        assert items[0].sell_in == 1

        # Day 3: quality 12 -> 13, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 13
        assert items[0].sell_in == 0

        # Day 4: quality 13 -> 15 (double improvement), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 15
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_1(self):
        """Aged Brie should improve consistently over multiple days."""
        items = None
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 11, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 11
        assert items[0].sell_in == 2

        # Day 2: quality 11 -> 12, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 12
        assert items[0].sell_in == 1

        # Day 3: quality 12 -> 13, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 13
        assert items[0].sell_in == 0

        # Day 4: quality 13 -> 15 (double improvement), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 15
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_2(self):
        """Aged Brie should improve consistently over multiple days."""
        items = [Item(None, 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 11, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 11
        assert items[0].sell_in == 2

        # Day 2: quality 11 -> 12, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 12
        assert items[0].sell_in == 1

        # Day 3: quality 12 -> 13, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 13
        assert items[0].sell_in == 0

        # Day 4: quality 13 -> 15 (double improvement), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 15
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_3(self):
        """Aged Brie should improve consistently over multiple days."""
        items = [Item("Aged Brie", None, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 11, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 11
        assert items[0].sell_in == 2

        # Day 2: quality 11 -> 12, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 12
        assert items[0].sell_in == 1

        # Day 3: quality 12 -> 13, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 13
        assert items[0].sell_in == 0

        # Day 4: quality 13 -> 15 (double improvement), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 15
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_4(self):
        """Aged Brie should improve consistently over multiple days."""
        items = [Item("Aged Brie", 3, None)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 11, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 11
        assert items[0].sell_in == 2

        # Day 2: quality 11 -> 12, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 12
        assert items[0].sell_in == 1

        # Day 3: quality 12 -> 13, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 13
        assert items[0].sell_in == 0

        # Day 4: quality 13 -> 15 (double improvement), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 15
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_5(self):
        """Aged Brie should improve consistently over multiple days."""
        items = [Item(3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 11, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 11
        assert items[0].sell_in == 2

        # Day 2: quality 11 -> 12, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 12
        assert items[0].sell_in == 1

        # Day 3: quality 12 -> 13, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 13
        assert items[0].sell_in == 0

        # Day 4: quality 13 -> 15 (double improvement), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 15
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_6(self):
        """Aged Brie should improve consistently over multiple days."""
        items = [Item("Aged Brie", 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 11, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 11
        assert items[0].sell_in == 2

        # Day 2: quality 11 -> 12, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 12
        assert items[0].sell_in == 1

        # Day 3: quality 12 -> 13, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 13
        assert items[0].sell_in == 0

        # Day 4: quality 13 -> 15 (double improvement), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 15
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_7(self):
        """Aged Brie should improve consistently over multiple days."""
        items = [Item("Aged Brie", 3, )]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 11, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 11
        assert items[0].sell_in == 2

        # Day 2: quality 11 -> 12, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 12
        assert items[0].sell_in == 1

        # Day 3: quality 12 -> 13, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 13
        assert items[0].sell_in == 0

        # Day 4: quality 13 -> 15 (double improvement), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 15
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_8(self):
        """Aged Brie should improve consistently over multiple days."""
        items = [Item("XXAged BrieXX", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 11, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 11
        assert items[0].sell_in == 2

        # Day 2: quality 11 -> 12, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 12
        assert items[0].sell_in == 1

        # Day 3: quality 12 -> 13, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 13
        assert items[0].sell_in == 0

        # Day 4: quality 13 -> 15 (double improvement), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 15
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_9(self):
        """Aged Brie should improve consistently over multiple days."""
        items = [Item("aged brie", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 11, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 11
        assert items[0].sell_in == 2

        # Day 2: quality 11 -> 12, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 12
        assert items[0].sell_in == 1

        # Day 3: quality 12 -> 13, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 13
        assert items[0].sell_in == 0

        # Day 4: quality 13 -> 15 (double improvement), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 15
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_10(self):
        """Aged Brie should improve consistently over multiple days."""
        items = [Item("AGED BRIE", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 11, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 11
        assert items[0].sell_in == 2

        # Day 2: quality 11 -> 12, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 12
        assert items[0].sell_in == 1

        # Day 3: quality 12 -> 13, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 13
        assert items[0].sell_in == 0

        # Day 4: quality 13 -> 15 (double improvement), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 15
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_11(self):
        """Aged Brie should improve consistently over multiple days."""
        items = [Item("Aged Brie", 4, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 11, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 11
        assert items[0].sell_in == 2

        # Day 2: quality 11 -> 12, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 12
        assert items[0].sell_in == 1

        # Day 3: quality 12 -> 13, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 13
        assert items[0].sell_in == 0

        # Day 4: quality 13 -> 15 (double improvement), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 15
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_12(self):
        """Aged Brie should improve consistently over multiple days."""
        items = [Item("Aged Brie", 3, 11)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 11, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 11
        assert items[0].sell_in == 2

        # Day 2: quality 11 -> 12, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 12
        assert items[0].sell_in == 1

        # Day 3: quality 12 -> 13, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 13
        assert items[0].sell_in == 0

        # Day 4: quality 13 -> 15 (double improvement), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 15
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_13(self):
        """Aged Brie should improve consistently over multiple days."""
        items = [Item("Aged Brie", 3, 10)]
        gilded_rose = None

        # Day 1: quality 10 -> 11, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 11
        assert items[0].sell_in == 2

        # Day 2: quality 11 -> 12, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 12
        assert items[0].sell_in == 1

        # Day 3: quality 12 -> 13, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 13
        assert items[0].sell_in == 0

        # Day 4: quality 13 -> 15 (double improvement), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 15
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_14(self):
        """Aged Brie should improve consistently over multiple days."""
        items = [Item("Aged Brie", 3, 10)]
        gilded_rose = GildedRose(None)

        # Day 1: quality 10 -> 11, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 11
        assert items[0].sell_in == 2

        # Day 2: quality 11 -> 12, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 12
        assert items[0].sell_in == 1

        # Day 3: quality 12 -> 13, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 13
        assert items[0].sell_in == 0

        # Day 4: quality 13 -> 15 (double improvement), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 15
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_15(self):
        """Aged Brie should improve consistently over multiple days."""
        items = [Item("Aged Brie", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 11, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[1].quality == 11
        assert items[0].sell_in == 2

        # Day 2: quality 11 -> 12, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 12
        assert items[0].sell_in == 1

        # Day 3: quality 12 -> 13, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 13
        assert items[0].sell_in == 0

        # Day 4: quality 13 -> 15 (double improvement), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 15
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_16(self):
        """Aged Brie should improve consistently over multiple days."""
        items = [Item("Aged Brie", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 11, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality != 11
        assert items[0].sell_in == 2

        # Day 2: quality 11 -> 12, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 12
        assert items[0].sell_in == 1

        # Day 3: quality 12 -> 13, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 13
        assert items[0].sell_in == 0

        # Day 4: quality 13 -> 15 (double improvement), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 15
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_17(self):
        """Aged Brie should improve consistently over multiple days."""
        items = [Item("Aged Brie", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 11, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 12
        assert items[0].sell_in == 2

        # Day 2: quality 11 -> 12, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 12
        assert items[0].sell_in == 1

        # Day 3: quality 12 -> 13, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 13
        assert items[0].sell_in == 0

        # Day 4: quality 13 -> 15 (double improvement), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 15
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_18(self):
        """Aged Brie should improve consistently over multiple days."""
        items = [Item("Aged Brie", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 11, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 11
        assert items[1].sell_in == 2

        # Day 2: quality 11 -> 12, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 12
        assert items[0].sell_in == 1

        # Day 3: quality 12 -> 13, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 13
        assert items[0].sell_in == 0

        # Day 4: quality 13 -> 15 (double improvement), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 15
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_19(self):
        """Aged Brie should improve consistently over multiple days."""
        items = [Item("Aged Brie", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 11, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 11
        assert items[0].sell_in != 2

        # Day 2: quality 11 -> 12, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 12
        assert items[0].sell_in == 1

        # Day 3: quality 12 -> 13, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 13
        assert items[0].sell_in == 0

        # Day 4: quality 13 -> 15 (double improvement), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 15
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_20(self):
        """Aged Brie should improve consistently over multiple days."""
        items = [Item("Aged Brie", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 11, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 11
        assert items[0].sell_in == 3

        # Day 2: quality 11 -> 12, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 12
        assert items[0].sell_in == 1

        # Day 3: quality 12 -> 13, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 13
        assert items[0].sell_in == 0

        # Day 4: quality 13 -> 15 (double improvement), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 15
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_21(self):
        """Aged Brie should improve consistently over multiple days."""
        items = [Item("Aged Brie", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 11, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 11
        assert items[0].sell_in == 2

        # Day 2: quality 11 -> 12, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[1].quality == 12
        assert items[0].sell_in == 1

        # Day 3: quality 12 -> 13, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 13
        assert items[0].sell_in == 0

        # Day 4: quality 13 -> 15 (double improvement), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 15
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_22(self):
        """Aged Brie should improve consistently over multiple days."""
        items = [Item("Aged Brie", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 11, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 11
        assert items[0].sell_in == 2

        # Day 2: quality 11 -> 12, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality != 12
        assert items[0].sell_in == 1

        # Day 3: quality 12 -> 13, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 13
        assert items[0].sell_in == 0

        # Day 4: quality 13 -> 15 (double improvement), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 15
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_23(self):
        """Aged Brie should improve consistently over multiple days."""
        items = [Item("Aged Brie", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 11, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 11
        assert items[0].sell_in == 2

        # Day 2: quality 11 -> 12, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 13
        assert items[0].sell_in == 1

        # Day 3: quality 12 -> 13, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 13
        assert items[0].sell_in == 0

        # Day 4: quality 13 -> 15 (double improvement), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 15
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_24(self):
        """Aged Brie should improve consistently over multiple days."""
        items = [Item("Aged Brie", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 11, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 11
        assert items[0].sell_in == 2

        # Day 2: quality 11 -> 12, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 12
        assert items[1].sell_in == 1

        # Day 3: quality 12 -> 13, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 13
        assert items[0].sell_in == 0

        # Day 4: quality 13 -> 15 (double improvement), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 15
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_25(self):
        """Aged Brie should improve consistently over multiple days."""
        items = [Item("Aged Brie", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 11, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 11
        assert items[0].sell_in == 2

        # Day 2: quality 11 -> 12, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 12
        assert items[0].sell_in != 1

        # Day 3: quality 12 -> 13, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 13
        assert items[0].sell_in == 0

        # Day 4: quality 13 -> 15 (double improvement), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 15
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_26(self):
        """Aged Brie should improve consistently over multiple days."""
        items = [Item("Aged Brie", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 11, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 11
        assert items[0].sell_in == 2

        # Day 2: quality 11 -> 12, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 12
        assert items[0].sell_in == 2

        # Day 3: quality 12 -> 13, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 13
        assert items[0].sell_in == 0

        # Day 4: quality 13 -> 15 (double improvement), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 15
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_27(self):
        """Aged Brie should improve consistently over multiple days."""
        items = [Item("Aged Brie", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 11, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 11
        assert items[0].sell_in == 2

        # Day 2: quality 11 -> 12, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 12
        assert items[0].sell_in == 1

        # Day 3: quality 12 -> 13, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[1].quality == 13
        assert items[0].sell_in == 0

        # Day 4: quality 13 -> 15 (double improvement), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 15
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_28(self):
        """Aged Brie should improve consistently over multiple days."""
        items = [Item("Aged Brie", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 11, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 11
        assert items[0].sell_in == 2

        # Day 2: quality 11 -> 12, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 12
        assert items[0].sell_in == 1

        # Day 3: quality 12 -> 13, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality != 13
        assert items[0].sell_in == 0

        # Day 4: quality 13 -> 15 (double improvement), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 15
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_29(self):
        """Aged Brie should improve consistently over multiple days."""
        items = [Item("Aged Brie", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 11, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 11
        assert items[0].sell_in == 2

        # Day 2: quality 11 -> 12, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 12
        assert items[0].sell_in == 1

        # Day 3: quality 12 -> 13, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 14
        assert items[0].sell_in == 0

        # Day 4: quality 13 -> 15 (double improvement), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 15
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_30(self):
        """Aged Brie should improve consistently over multiple days."""
        items = [Item("Aged Brie", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 11, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 11
        assert items[0].sell_in == 2

        # Day 2: quality 11 -> 12, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 12
        assert items[0].sell_in == 1

        # Day 3: quality 12 -> 13, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 13
        assert items[1].sell_in == 0

        # Day 4: quality 13 -> 15 (double improvement), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 15
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_31(self):
        """Aged Brie should improve consistently over multiple days."""
        items = [Item("Aged Brie", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 11, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 11
        assert items[0].sell_in == 2

        # Day 2: quality 11 -> 12, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 12
        assert items[0].sell_in == 1

        # Day 3: quality 12 -> 13, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 13
        assert items[0].sell_in != 0

        # Day 4: quality 13 -> 15 (double improvement), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 15
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_32(self):
        """Aged Brie should improve consistently over multiple days."""
        items = [Item("Aged Brie", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 11, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 11
        assert items[0].sell_in == 2

        # Day 2: quality 11 -> 12, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 12
        assert items[0].sell_in == 1

        # Day 3: quality 12 -> 13, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 13
        assert items[0].sell_in == 1

        # Day 4: quality 13 -> 15 (double improvement), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 15
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_33(self):
        """Aged Brie should improve consistently over multiple days."""
        items = [Item("Aged Brie", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 11, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 11
        assert items[0].sell_in == 2

        # Day 2: quality 11 -> 12, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 12
        assert items[0].sell_in == 1

        # Day 3: quality 12 -> 13, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 13
        assert items[0].sell_in == 0

        # Day 4: quality 13 -> 15 (double improvement), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[1].quality == 15
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_34(self):
        """Aged Brie should improve consistently over multiple days."""
        items = [Item("Aged Brie", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 11, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 11
        assert items[0].sell_in == 2

        # Day 2: quality 11 -> 12, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 12
        assert items[0].sell_in == 1

        # Day 3: quality 12 -> 13, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 13
        assert items[0].sell_in == 0

        # Day 4: quality 13 -> 15 (double improvement), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality != 15
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_35(self):
        """Aged Brie should improve consistently over multiple days."""
        items = [Item("Aged Brie", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 11, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 11
        assert items[0].sell_in == 2

        # Day 2: quality 11 -> 12, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 12
        assert items[0].sell_in == 1

        # Day 3: quality 12 -> 13, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 13
        assert items[0].sell_in == 0

        # Day 4: quality 13 -> 15 (double improvement), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 16
        assert items[0].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_36(self):
        """Aged Brie should improve consistently over multiple days."""
        items = [Item("Aged Brie", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 11, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 11
        assert items[0].sell_in == 2

        # Day 2: quality 11 -> 12, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 12
        assert items[0].sell_in == 1

        # Day 3: quality 12 -> 13, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 13
        assert items[0].sell_in == 0

        # Day 4: quality 13 -> 15 (double improvement), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 15
        assert items[1].sell_in == -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_37(self):
        """Aged Brie should improve consistently over multiple days."""
        items = [Item("Aged Brie", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 11, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 11
        assert items[0].sell_in == 2

        # Day 2: quality 11 -> 12, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 12
        assert items[0].sell_in == 1

        # Day 3: quality 12 -> 13, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 13
        assert items[0].sell_in == 0

        # Day 4: quality 13 -> 15 (double improvement), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 15
        assert items[0].sell_in != -1

    def xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_38(self):
        """Aged Brie should improve consistently over multiple days."""
        items = [Item("Aged Brie", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 11, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 11
        assert items[0].sell_in == 2

        # Day 2: quality 11 -> 12, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 12
        assert items[0].sell_in == 1

        # Day 3: quality 12 -> 13, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 13
        assert items[0].sell_in == 0

        # Day 4: quality 13 -> 15 (double improvement), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 15
        assert items[0].sell_in == +1

    def xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_39(self):
        """Aged Brie should improve consistently over multiple days."""
        items = [Item("Aged Brie", 3, 10)]
        gilded_rose = GildedRose(items)

        # Day 1: quality 10 -> 11, sell_in 3 -> 2
        gilded_rose.update_quality()
        assert items[0].quality == 11
        assert items[0].sell_in == 2

        # Day 2: quality 11 -> 12, sell_in 2 -> 1
        gilded_rose.update_quality()
        assert items[0].quality == 12
        assert items[0].sell_in == 1

        # Day 3: quality 12 -> 13, sell_in 1 -> 0
        gilded_rose.update_quality()
        assert items[0].quality == 13
        assert items[0].sell_in == 0

        # Day 4: quality 13 -> 15 (double improvement), sell_in 0 -> -1
        gilded_rose.update_quality()
        assert items[0].quality == 15
        assert items[0].sell_in == -2
    
    xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_1': xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_1, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_2': xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_2, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_3': xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_3, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_4': xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_4, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_5': xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_5, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_6': xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_6, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_7': xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_7, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_8': xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_8, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_9': xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_9, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_10': xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_10, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_11': xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_11, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_12': xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_12, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_13': xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_13, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_14': xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_14, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_15': xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_15, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_16': xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_16, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_17': xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_17, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_18': xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_18, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_19': xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_19, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_20': xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_20, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_21': xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_21, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_22': xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_22, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_23': xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_23, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_24': xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_24, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_25': xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_25, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_26': xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_26, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_27': xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_27, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_28': xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_28, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_29': xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_29, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_30': xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_30, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_31': xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_31, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_32': xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_32, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_33': xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_33, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_34': xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_34, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_35': xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_35, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_36': xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_36, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_37': xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_37, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_38': xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_38, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_39': xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_39
    }
    
    def test_aged_brie_over_multiple_days(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_orig"), object.__getattribute__(self, "xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_mutants"), args, kwargs, self)
        return result 
    
    test_aged_brie_over_multiple_days.__signature__ = _mutmut_signature(xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_orig)
    xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days__mutmut_orig.__name__ = 'xǁTestGildedRoseSequentialUpdatesǁtest_aged_brie_over_multiple_days'

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_orig(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 15, 20)]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_1(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = None
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_2(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item(None, 15, 20)]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_3(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", None, 20)]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_4(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 15, None)]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_5(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item(15, 20)]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_6(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 20)]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_7(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 15, )]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_8(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("XXBackstage passes to a TAFKAL80ETC concertXX", 15, 20)]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_9(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("backstage passes to a tafkal80etc concert", 15, 20)]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_10(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("BACKSTAGE PASSES TO A TAFKAL80ETC CONCERT", 15, 20)]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_11(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 16, 20)]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_12(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 15, 21)]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_13(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 15, 20)]
        gilded_rose = None

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_14(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 15, 20)]
        gilded_rose = GildedRose(None)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_15(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 15, 20)]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[1].quality == 21
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_16(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 15, 20)]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality != 21
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_17(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 15, 20)]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 22
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_18(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 15, 20)]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[1].sell_in == 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_19(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 15, 20)]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[0].sell_in != 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_20(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 15, 20)]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[0].sell_in == 15

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_21(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 15, 20)]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(None):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_22(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 15, 20)]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(5):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_23(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 15, 20)]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[1].sell_in == 10
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_24(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 15, 20)]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in != 10
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_25(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 15, 20)]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 11
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_26(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 15, 20)]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[1].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_27(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 15, 20)]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[0].quality != 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_28(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 15, 20)]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[0].quality == 26

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_29(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 15, 20)]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[1].quality == 27
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_30(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 15, 20)]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality != 27
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_31(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 15, 20)]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 28
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_32(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 15, 20)]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[1].sell_in == 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_33(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 15, 20)]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[0].sell_in != 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_34(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 15, 20)]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[0].sell_in == 10

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_35(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 15, 20)]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(None):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_36(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 15, 20)]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(5):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_37(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 15, 20)]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[1].sell_in == 5
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_38(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 15, 20)]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in != 5
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_39(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 15, 20)]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 6
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_40(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 15, 20)]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[1].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_41(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 15, 20)]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[0].quality != 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_42(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 15, 20)]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[0].quality == 36

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_43(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 15, 20)]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[1].quality == 38
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_44(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 15, 20)]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality != 38
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_45(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 15, 20)]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 39
        assert items[0].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_46(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 15, 20)]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[1].sell_in == 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_47(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 15, 20)]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[0].sell_in != 4

    def xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_48(self):
        """Backstage pass should improve at increasing rates as concert approaches."""
        items = [Item("Backstage passes to a TAFKAL80ETC concert", 15, 20)]
        gilded_rose = GildedRose(items)

        # Day 1: 15 days away, +1
        gilded_rose.update_quality()
        assert items[0].quality == 21
        assert items[0].sell_in == 14

        # Fast forward to 10 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 10
        assert items[0].quality == 25

        # Day at 10 days: +2
        gilded_rose.update_quality()
        assert items[0].quality == 27
        assert items[0].sell_in == 9

        # Fast forward to 5 days
        for _ in range(4):
            gilded_rose.update_quality()

        assert items[0].sell_in == 5
        assert items[0].quality == 35

        # Day at 5 days: +3
        gilded_rose.update_quality()
        assert items[0].quality == 38
        assert items[0].sell_in == 5
    
    xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_mutants : ClassVar[MutantDict] = {
    'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_1': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_1, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_2': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_2, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_3': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_3, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_4': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_4, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_5': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_5, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_6': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_6, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_7': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_7, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_8': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_8, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_9': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_9, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_10': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_10, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_11': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_11, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_12': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_12, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_13': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_13, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_14': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_14, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_15': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_15, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_16': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_16, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_17': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_17, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_18': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_18, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_19': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_19, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_20': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_20, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_21': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_21, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_22': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_22, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_23': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_23, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_24': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_24, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_25': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_25, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_26': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_26, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_27': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_27, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_28': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_28, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_29': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_29, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_30': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_30, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_31': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_31, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_32': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_32, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_33': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_33, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_34': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_34, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_35': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_35, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_36': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_36, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_37': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_37, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_38': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_38, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_39': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_39, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_40': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_40, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_41': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_41, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_42': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_42, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_43': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_43, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_44': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_44, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_45': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_45, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_46': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_46, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_47': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_47, 
        'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_48': xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_48
    }
    
    def test_backstage_pass_approaching_concert(self, *args, **kwargs):
        result = _mutmut_trampoline(object.__getattribute__(self, "xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_orig"), object.__getattribute__(self, "xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_mutants"), args, kwargs, self)
        return result 
    
    test_backstage_pass_approaching_concert.__signature__ = _mutmut_signature(xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_orig)
    xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert__mutmut_orig.__name__ = 'xǁTestGildedRoseSequentialUpdatesǁtest_backstage_pass_approaching_concert'


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

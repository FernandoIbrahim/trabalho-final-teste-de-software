"""
Implementação de Steps para Testes BDD - Gilded Rose
Using pytest-bdd framework

Este módulo implementa os steps (Given/When/Then) para executar
os cenários BDD definidos em GILDED_ROSE_BDD.feature

Uso:
    pytest --gherkin-terminal-reporter GILDED_ROSE_BDD.feature
"""

from typing import Dict, List, Tuple
import pytest
from pytest_bdd import given, when, then, scenario, scenarios, parsers

# Importar as classes do Gilded Rose
import sys
sys.path.insert(0, '/Users/fernandoibraim/Desktop/trabalho-final-testes/python')
from gilded_rose import Item, GildedRose


# ============================================================================
# PYTEST_BDD CONFIGURATION
# ============================================================================

# Carrega todos os cenários do arquivo .feature
scenarios('../GILDED_ROSE_BDD.feature')
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


# ============================================================================
# FIXTURES - Inicialização compartilhada
# ============================================================================

@pytest.fixture
def context():
    """Context para armazenar estado entre steps."""
    class Context:
        def __init__(self):
            self.items = []
            self.gilded_rose = None
            self.expected_qualities = []
            self.expected_sell_ins = []
    
    return Context()


# ============================================================================
# GIVEN STEPS - Setup/Contexto
# ============================================================================

@given(parsers.parse('que tenho um item "{item_name}" com qualidade {quality:d} e dias para vender {sell_in:d}'))
def step_create_single_item(context, item_name, quality, sell_in):
    """Cria um único item com nome, qualidade e dias para vender."""
    context.items = [Item(item_name, sell_in, quality)]
    context.gilded_rose = GildedRose(context.items)


@given('que o sistema Gilded Rose está inicializado')
def step_initialize_system(context):
    """Inicializa o sistema Gilded Rose vazio."""
    context.items = []
    context.gilded_rose = GildedRose([])


@given('possuo um inventário vazio')
def step_initialize_empty_inventory(context):
    """Garante que o inventário começa vazio."""
    context.items = []
    context.gilded_rose = GildedRose([])


@given(parsers.parse('que tenho um inventário vazio'))
def step_ensure_empty_inventory(context):
    """Cria um inventário vazio."""
    context.items = []
    context.gilded_rose = GildedRose([])


@given('que tenho os itens no inventário:')
def step_create_multiple_items(context):
    """Cria múltiplos itens a partir de uma tabela."""
    # Tabela esperada:
    # | Nome | Qualidade | Dias |
    context.items = []
    for row in context.table:
        item = Item(row['Nome'], int(row['Dias']), int(row['Qualidade']))
        context.items.append(item)
    context.gilded_rose = GildedRose(context.items)


@given(parsers.parse('que tenho itens com qualidades "{qualities}" para item normal'))
def step_create_items_with_qualities(context, qualities):
    """Cria múltiplos itens normais com qualidades especificadas."""
    context.items = []
    quality_list = [int(q.strip()) for q in qualities.split(',')]
    for quality in quality_list:
        item = Item("Normal Item", 10, quality)
        context.items.append(item)
    context.gilded_rose = GildedRose(context.items)


@given(parsers.parse('que tenho itens com qualidades "{qualities}" para Aged Brie'))
def step_create_aged_brie_with_qualities(context, qualities):
    """Cria múltiplos Aged Brie com qualidades especificadas."""
    context.items = []
    quality_list = [int(q.strip()) for q in qualities.split(',')]
    for quality in quality_list:
        item = Item("Aged Brie", 10, quality)
        context.items.append(item)
    context.gilded_rose = GildedRose(context.items)


# ============================================================================
# WHEN STEPS - Ações
# ============================================================================

@when('o sistema atualiza a qualidade')
def step_update_quality_once(context):
    """Atualiza a qualidade dos itens uma vez."""
    context.gilded_rose.update_quality()


@when(parsers.parse('o sistema atualiza a qualidade {times:d} vezes'))
def step_update_quality_multiple_times(context, times):
    """Atualiza a qualidade dos itens múltiplas vezes."""
    for _ in range(times):
        context.gilded_rose.update_quality()


@when('o sistema atualiza todos os itens')
def step_update_all_items(context):
    """Atualiza todos os itens no inventário."""
    context.gilded_rose.update_quality()


# ============================================================================
# THEN STEPS - Verificações
# ============================================================================

@then(parsers.parse('a qualidade deve ser {expected:d}'))
def step_check_quality(context, expected):
    """Verifica a qualidade do primeiro item."""
    assert context.items[0].quality == expected, \
        f"Esperado qualidade {expected}, mas obteve {context.items[0].quality}"


@then(parsers.parse('os dias para vender devem ser {expected:d}'))
def step_check_sell_in(context, expected):
    """Verifica os dias para vender do primeiro item."""
    assert context.items[0].sell_in == expected, \
        f"Esperado sell_in {expected}, mas obteve {context.items[0].sell_in}"


@then(parsers.parse('o item "{item_name}" deve ter qualidade {expected:d}'))
def step_check_item_quality_by_name(context, item_name, expected):
    """Verifica a qualidade de um item específico por nome."""
    item = next((i for i in context.items if i.name == item_name), None)
    assert item is not None, f"Item '{item_name}' não encontrado"
    assert item.quality == expected, \
        f"Item '{item_name}': esperado qualidade {expected}, mas obteve {item.quality}"


@then(parsers.parse('o item "{item_name}" deve ter dias para vender {expected:d}'))
def step_check_item_sell_in_by_name(context, item_name, expected):
    """Verifica os dias para vender de um item específico por nome."""
    item = next((i for i in context.items if i.name == item_name), None)
    assert item is not None, f"Item '{item_name}' não encontrado"
    assert item.sell_in == expected, \
        f"Item '{item_name}': esperado sell_in {expected}, mas obteve {item.sell_in}"


@then(parsers.parse('as qualidades devem ser "{expected_qualities}"'))
def step_check_multiple_qualities(context, expected_qualities):
    """Verifica as qualidades de múltiplos itens."""
    expected_list = [int(q.strip().strip('"')) for q in expected_qualities.split(',')]
    for i, expected in enumerate(expected_list):
        assert context.items[i].quality == expected, \
            f"Item {i}: esperado qualidade {expected}, mas obteve {context.items[i].quality}"


@then('nenhum erro deve ocorrer')
def step_no_error_occurred(context):
    """Verifica que nenhum erro foi lançado (fixture passa se chegou até aqui)."""
    assert True, "Nenhum erro deve ter ocorrido"


# ============================================================================
# COMPLEX ASSERTION CHAINS - Para cenários com múltiplos steps
# ============================================================================

@then(parsers.parse('a qualidade deve ser {q:d}\nE os dias para vender devem ser {s:d}'))
def step_check_quality_and_sell_in(context, q, s):
    """Verifica qualidade e sell_in em um só step."""
    step_check_quality(context, q)
    step_check_sell_in(context, s)


# ============================================================================
# PARAMETRIZATION HELPERS
# ============================================================================

@pytest.fixture(params=[
    ("Normal Item", 25, 10),
    ("Normal Item", 50, 10),
    ("Normal Item", 0, 10),
])
def normal_items_fixture(request):
    """Fixture parametrizada para testes de item normal."""
    item_name, quality, sell_in = request.param
    return Item(item_name, sell_in, quality)


@pytest.fixture(params=[
    ("Aged Brie", 25, 10),
    ("Aged Brie", 0, 10),
    ("Aged Brie", 50, 10),
])
def aged_brie_fixture(request):
    """Fixture parametrizada para testes de Aged Brie."""
    item_name, quality, sell_in = request.param
    return Item(item_name, sell_in, quality)


@pytest.fixture(params=[
    ("Backstage passes to a TAFKAL80ETC concert", 25, 11),
    ("Backstage passes to a TAFKAL80ETC concert", 25, 10),
    ("Backstage passes to a TAFKAL80ETC concert", 25, 5),
    ("Backstage passes to a TAFKAL80ETC concert", 25, 0),
])
def backstage_pass_fixture(request):
    """Fixture parametrizada para testes de Backstage Passes."""
    item_name, quality, sell_in = request.param
    return Item(item_name, sell_in, quality)


@pytest.fixture(params=[
    ("Sulfuras, Hand of Ragnaros", 80, 10),
    ("Sulfuras, Hand of Ragnaros", 80, -1),
])
def sulfuras_fixture(request):
    """Fixture parametrizada para testes de Sulfuras."""
    item_name, quality, sell_in = request.param
    return Item(item_name, sell_in, quality)


# ============================================================================
# HOOKS - Executado antes/depois de cenários
# ============================================================================

def x_before_scenario__mutmut_orig(scenario, context):
    """Executado antes de cada cenário."""
    # Reset context
    if not hasattr(context, 'items'):
        context.items = []
    if not hasattr(context, 'gilded_rose'):
        context.gilded_rose = None


# ============================================================================
# HOOKS - Executado antes/depois de cenários
# ============================================================================

def x_before_scenario__mutmut_1(scenario, context):
    """Executado antes de cada cenário."""
    # Reset context
    if hasattr(context, 'items'):
        context.items = []
    if not hasattr(context, 'gilded_rose'):
        context.gilded_rose = None


# ============================================================================
# HOOKS - Executado antes/depois de cenários
# ============================================================================

def x_before_scenario__mutmut_2(scenario, context):
    """Executado antes de cada cenário."""
    # Reset context
    if not hasattr(None, 'items'):
        context.items = []
    if not hasattr(context, 'gilded_rose'):
        context.gilded_rose = None


# ============================================================================
# HOOKS - Executado antes/depois de cenários
# ============================================================================

def x_before_scenario__mutmut_3(scenario, context):
    """Executado antes de cada cenário."""
    # Reset context
    if not hasattr(context, None):
        context.items = []
    if not hasattr(context, 'gilded_rose'):
        context.gilded_rose = None


# ============================================================================
# HOOKS - Executado antes/depois de cenários
# ============================================================================

def x_before_scenario__mutmut_4(scenario, context):
    """Executado antes de cada cenário."""
    # Reset context
    if not hasattr('items'):
        context.items = []
    if not hasattr(context, 'gilded_rose'):
        context.gilded_rose = None


# ============================================================================
# HOOKS - Executado antes/depois de cenários
# ============================================================================

def x_before_scenario__mutmut_5(scenario, context):
    """Executado antes de cada cenário."""
    # Reset context
    if not hasattr(context, ):
        context.items = []
    if not hasattr(context, 'gilded_rose'):
        context.gilded_rose = None


# ============================================================================
# HOOKS - Executado antes/depois de cenários
# ============================================================================

def x_before_scenario__mutmut_6(scenario, context):
    """Executado antes de cada cenário."""
    # Reset context
    if not hasattr(context, 'XXitemsXX'):
        context.items = []
    if not hasattr(context, 'gilded_rose'):
        context.gilded_rose = None


# ============================================================================
# HOOKS - Executado antes/depois de cenários
# ============================================================================

def x_before_scenario__mutmut_7(scenario, context):
    """Executado antes de cada cenário."""
    # Reset context
    if not hasattr(context, 'ITEMS'):
        context.items = []
    if not hasattr(context, 'gilded_rose'):
        context.gilded_rose = None


# ============================================================================
# HOOKS - Executado antes/depois de cenários
# ============================================================================

def x_before_scenario__mutmut_8(scenario, context):
    """Executado antes de cada cenário."""
    # Reset context
    if not hasattr(context, 'items'):
        context.items = None
    if not hasattr(context, 'gilded_rose'):
        context.gilded_rose = None


# ============================================================================
# HOOKS - Executado antes/depois de cenários
# ============================================================================

def x_before_scenario__mutmut_9(scenario, context):
    """Executado antes de cada cenário."""
    # Reset context
    if not hasattr(context, 'items'):
        context.items = []
    if hasattr(context, 'gilded_rose'):
        context.gilded_rose = None


# ============================================================================
# HOOKS - Executado antes/depois de cenários
# ============================================================================

def x_before_scenario__mutmut_10(scenario, context):
    """Executado antes de cada cenário."""
    # Reset context
    if not hasattr(context, 'items'):
        context.items = []
    if not hasattr(None, 'gilded_rose'):
        context.gilded_rose = None


# ============================================================================
# HOOKS - Executado antes/depois de cenários
# ============================================================================

def x_before_scenario__mutmut_11(scenario, context):
    """Executado antes de cada cenário."""
    # Reset context
    if not hasattr(context, 'items'):
        context.items = []
    if not hasattr(context, None):
        context.gilded_rose = None


# ============================================================================
# HOOKS - Executado antes/depois de cenários
# ============================================================================

def x_before_scenario__mutmut_12(scenario, context):
    """Executado antes de cada cenário."""
    # Reset context
    if not hasattr(context, 'items'):
        context.items = []
    if not hasattr('gilded_rose'):
        context.gilded_rose = None


# ============================================================================
# HOOKS - Executado antes/depois de cenários
# ============================================================================

def x_before_scenario__mutmut_13(scenario, context):
    """Executado antes de cada cenário."""
    # Reset context
    if not hasattr(context, 'items'):
        context.items = []
    if not hasattr(context, ):
        context.gilded_rose = None


# ============================================================================
# HOOKS - Executado antes/depois de cenários
# ============================================================================

def x_before_scenario__mutmut_14(scenario, context):
    """Executado antes de cada cenário."""
    # Reset context
    if not hasattr(context, 'items'):
        context.items = []
    if not hasattr(context, 'XXgilded_roseXX'):
        context.gilded_rose = None


# ============================================================================
# HOOKS - Executado antes/depois de cenários
# ============================================================================

def x_before_scenario__mutmut_15(scenario, context):
    """Executado antes de cada cenário."""
    # Reset context
    if not hasattr(context, 'items'):
        context.items = []
    if not hasattr(context, 'GILDED_ROSE'):
        context.gilded_rose = None


# ============================================================================
# HOOKS - Executado antes/depois de cenários
# ============================================================================

def x_before_scenario__mutmut_16(scenario, context):
    """Executado antes de cada cenário."""
    # Reset context
    if not hasattr(context, 'items'):
        context.items = []
    if not hasattr(context, 'gilded_rose'):
        context.gilded_rose = ""

x_before_scenario__mutmut_mutants : ClassVar[MutantDict] = {
'x_before_scenario__mutmut_1': x_before_scenario__mutmut_1, 
    'x_before_scenario__mutmut_2': x_before_scenario__mutmut_2, 
    'x_before_scenario__mutmut_3': x_before_scenario__mutmut_3, 
    'x_before_scenario__mutmut_4': x_before_scenario__mutmut_4, 
    'x_before_scenario__mutmut_5': x_before_scenario__mutmut_5, 
    'x_before_scenario__mutmut_6': x_before_scenario__mutmut_6, 
    'x_before_scenario__mutmut_7': x_before_scenario__mutmut_7, 
    'x_before_scenario__mutmut_8': x_before_scenario__mutmut_8, 
    'x_before_scenario__mutmut_9': x_before_scenario__mutmut_9, 
    'x_before_scenario__mutmut_10': x_before_scenario__mutmut_10, 
    'x_before_scenario__mutmut_11': x_before_scenario__mutmut_11, 
    'x_before_scenario__mutmut_12': x_before_scenario__mutmut_12, 
    'x_before_scenario__mutmut_13': x_before_scenario__mutmut_13, 
    'x_before_scenario__mutmut_14': x_before_scenario__mutmut_14, 
    'x_before_scenario__mutmut_15': x_before_scenario__mutmut_15, 
    'x_before_scenario__mutmut_16': x_before_scenario__mutmut_16
}

def before_scenario(*args, **kwargs):
    result = _mutmut_trampoline(x_before_scenario__mutmut_orig, x_before_scenario__mutmut_mutants, args, kwargs)
    return result 

before_scenario.__signature__ = _mutmut_signature(x_before_scenario__mutmut_orig)
x_before_scenario__mutmut_orig.__name__ = 'x_before_scenario'


def x_after_scenario__mutmut_orig(scenario, context):
    """Executado depois de cada cenário."""
    # Cleanup
    context.items = []
    context.gilded_rose = None


def x_after_scenario__mutmut_1(scenario, context):
    """Executado depois de cada cenário."""
    # Cleanup
    context.items = None
    context.gilded_rose = None


def x_after_scenario__mutmut_2(scenario, context):
    """Executado depois de cada cenário."""
    # Cleanup
    context.items = []
    context.gilded_rose = ""

x_after_scenario__mutmut_mutants : ClassVar[MutantDict] = {
'x_after_scenario__mutmut_1': x_after_scenario__mutmut_1, 
    'x_after_scenario__mutmut_2': x_after_scenario__mutmut_2
}

def after_scenario(*args, **kwargs):
    result = _mutmut_trampoline(x_after_scenario__mutmut_orig, x_after_scenario__mutmut_mutants, args, kwargs)
    return result 

after_scenario.__signature__ = _mutmut_signature(x_after_scenario__mutmut_orig)
x_after_scenario__mutmut_orig.__name__ = 'x_after_scenario'


# ============================================================================
# CUSTOM ASSERTIONS
# ============================================================================

def x_assert_item_unchanged__mutmut_orig(item: Item, original_quality: int, original_sell_in: int):
    """Verifica que um item não mudou (para Sulfuras)."""
    assert item.quality == original_quality, \
        f"Qualidade mudou! Esperado {original_quality}, obteve {item.quality}"
    assert item.sell_in == original_sell_in, \
        f"Sell_in mudou! Esperado {original_sell_in}, obteve {item.sell_in}"


# ============================================================================
# CUSTOM ASSERTIONS
# ============================================================================

def x_assert_item_unchanged__mutmut_1(item: Item, original_quality: int, original_sell_in: int):
    """Verifica que um item não mudou (para Sulfuras)."""
    assert item.quality != original_quality, \
        f"Qualidade mudou! Esperado {original_quality}, obteve {item.quality}"
    assert item.sell_in == original_sell_in, \
        f"Sell_in mudou! Esperado {original_sell_in}, obteve {item.sell_in}"


# ============================================================================
# CUSTOM ASSERTIONS
# ============================================================================

def x_assert_item_unchanged__mutmut_2(item: Item, original_quality: int, original_sell_in: int):
    """Verifica que um item não mudou (para Sulfuras)."""
    assert item.quality == original_quality, \
        f"Qualidade mudou! Esperado {original_quality}, obteve {item.quality}"
    assert item.sell_in != original_sell_in, \
        f"Sell_in mudou! Esperado {original_sell_in}, obteve {item.sell_in}"

x_assert_item_unchanged__mutmut_mutants : ClassVar[MutantDict] = {
'x_assert_item_unchanged__mutmut_1': x_assert_item_unchanged__mutmut_1, 
    'x_assert_item_unchanged__mutmut_2': x_assert_item_unchanged__mutmut_2
}

def assert_item_unchanged(*args, **kwargs):
    result = _mutmut_trampoline(x_assert_item_unchanged__mutmut_orig, x_assert_item_unchanged__mutmut_mutants, args, kwargs)
    return result 

assert_item_unchanged.__signature__ = _mutmut_signature(x_assert_item_unchanged__mutmut_orig)
x_assert_item_unchanged__mutmut_orig.__name__ = 'x_assert_item_unchanged'


def x_assert_quality_in_bounds__mutmut_orig(item: Item, min_quality: int = 0, max_quality: int = 50):
    """Verifica que a qualidade está dentro dos limites."""
    assert min_quality <= item.quality <= max_quality, \
        f"Qualidade {item.quality} fora dos limites [{min_quality}, {max_quality}]"


def x_assert_quality_in_bounds__mutmut_1(item: Item, min_quality: int = 1, max_quality: int = 50):
    """Verifica que a qualidade está dentro dos limites."""
    assert min_quality <= item.quality <= max_quality, \
        f"Qualidade {item.quality} fora dos limites [{min_quality}, {max_quality}]"


def x_assert_quality_in_bounds__mutmut_2(item: Item, min_quality: int = 0, max_quality: int = 51):
    """Verifica que a qualidade está dentro dos limites."""
    assert min_quality <= item.quality <= max_quality, \
        f"Qualidade {item.quality} fora dos limites [{min_quality}, {max_quality}]"


def x_assert_quality_in_bounds__mutmut_3(item: Item, min_quality: int = 0, max_quality: int = 50):
    """Verifica que a qualidade está dentro dos limites."""
    assert min_quality < item.quality <= max_quality, \
        f"Qualidade {item.quality} fora dos limites [{min_quality}, {max_quality}]"


def x_assert_quality_in_bounds__mutmut_4(item: Item, min_quality: int = 0, max_quality: int = 50):
    """Verifica que a qualidade está dentro dos limites."""
    assert min_quality <= item.quality < max_quality, \
        f"Qualidade {item.quality} fora dos limites [{min_quality}, {max_quality}]"

x_assert_quality_in_bounds__mutmut_mutants : ClassVar[MutantDict] = {
'x_assert_quality_in_bounds__mutmut_1': x_assert_quality_in_bounds__mutmut_1, 
    'x_assert_quality_in_bounds__mutmut_2': x_assert_quality_in_bounds__mutmut_2, 
    'x_assert_quality_in_bounds__mutmut_3': x_assert_quality_in_bounds__mutmut_3, 
    'x_assert_quality_in_bounds__mutmut_4': x_assert_quality_in_bounds__mutmut_4
}

def assert_quality_in_bounds(*args, **kwargs):
    result = _mutmut_trampoline(x_assert_quality_in_bounds__mutmut_orig, x_assert_quality_in_bounds__mutmut_mutants, args, kwargs)
    return result 

assert_quality_in_bounds.__signature__ = _mutmut_signature(x_assert_quality_in_bounds__mutmut_orig)
x_assert_quality_in_bounds__mutmut_orig.__name__ = 'x_assert_quality_in_bounds'


def x_assert_quality_decreased__mutmut_orig(item: Item, original_quality: int, expected_decrease: int):
    """Verifica que a qualidade diminuiu do valor esperado."""
    expected_quality = max(0, original_quality - expected_decrease)
    assert item.quality == expected_quality, \
        f"Qualidade esperada {expected_quality}, obteve {item.quality}"


def x_assert_quality_decreased__mutmut_1(item: Item, original_quality: int, expected_decrease: int):
    """Verifica que a qualidade diminuiu do valor esperado."""
    expected_quality = None
    assert item.quality == expected_quality, \
        f"Qualidade esperada {expected_quality}, obteve {item.quality}"


def x_assert_quality_decreased__mutmut_2(item: Item, original_quality: int, expected_decrease: int):
    """Verifica que a qualidade diminuiu do valor esperado."""
    expected_quality = max(None, original_quality - expected_decrease)
    assert item.quality == expected_quality, \
        f"Qualidade esperada {expected_quality}, obteve {item.quality}"


def x_assert_quality_decreased__mutmut_3(item: Item, original_quality: int, expected_decrease: int):
    """Verifica que a qualidade diminuiu do valor esperado."""
    expected_quality = max(0, None)
    assert item.quality == expected_quality, \
        f"Qualidade esperada {expected_quality}, obteve {item.quality}"


def x_assert_quality_decreased__mutmut_4(item: Item, original_quality: int, expected_decrease: int):
    """Verifica que a qualidade diminuiu do valor esperado."""
    expected_quality = max(original_quality - expected_decrease)
    assert item.quality == expected_quality, \
        f"Qualidade esperada {expected_quality}, obteve {item.quality}"


def x_assert_quality_decreased__mutmut_5(item: Item, original_quality: int, expected_decrease: int):
    """Verifica que a qualidade diminuiu do valor esperado."""
    expected_quality = max(0, )
    assert item.quality == expected_quality, \
        f"Qualidade esperada {expected_quality}, obteve {item.quality}"


def x_assert_quality_decreased__mutmut_6(item: Item, original_quality: int, expected_decrease: int):
    """Verifica que a qualidade diminuiu do valor esperado."""
    expected_quality = max(1, original_quality - expected_decrease)
    assert item.quality == expected_quality, \
        f"Qualidade esperada {expected_quality}, obteve {item.quality}"


def x_assert_quality_decreased__mutmut_7(item: Item, original_quality: int, expected_decrease: int):
    """Verifica que a qualidade diminuiu do valor esperado."""
    expected_quality = max(0, original_quality + expected_decrease)
    assert item.quality == expected_quality, \
        f"Qualidade esperada {expected_quality}, obteve {item.quality}"


def x_assert_quality_decreased__mutmut_8(item: Item, original_quality: int, expected_decrease: int):
    """Verifica que a qualidade diminuiu do valor esperado."""
    expected_quality = max(0, original_quality - expected_decrease)
    assert item.quality != expected_quality, \
        f"Qualidade esperada {expected_quality}, obteve {item.quality}"

x_assert_quality_decreased__mutmut_mutants : ClassVar[MutantDict] = {
'x_assert_quality_decreased__mutmut_1': x_assert_quality_decreased__mutmut_1, 
    'x_assert_quality_decreased__mutmut_2': x_assert_quality_decreased__mutmut_2, 
    'x_assert_quality_decreased__mutmut_3': x_assert_quality_decreased__mutmut_3, 
    'x_assert_quality_decreased__mutmut_4': x_assert_quality_decreased__mutmut_4, 
    'x_assert_quality_decreased__mutmut_5': x_assert_quality_decreased__mutmut_5, 
    'x_assert_quality_decreased__mutmut_6': x_assert_quality_decreased__mutmut_6, 
    'x_assert_quality_decreased__mutmut_7': x_assert_quality_decreased__mutmut_7, 
    'x_assert_quality_decreased__mutmut_8': x_assert_quality_decreased__mutmut_8
}

def assert_quality_decreased(*args, **kwargs):
    result = _mutmut_trampoline(x_assert_quality_decreased__mutmut_orig, x_assert_quality_decreased__mutmut_mutants, args, kwargs)
    return result 

assert_quality_decreased.__signature__ = _mutmut_signature(x_assert_quality_decreased__mutmut_orig)
x_assert_quality_decreased__mutmut_orig.__name__ = 'x_assert_quality_decreased'


def x_assert_quality_increased__mutmut_orig(item: Item, original_quality: int, expected_increase: int):
    """Verifica que a qualidade aumentou do valor esperado."""
    expected_quality = min(50, original_quality + expected_increase)
    assert item.quality == expected_quality, \
        f"Qualidade esperada {expected_quality}, obteve {item.quality}"


def x_assert_quality_increased__mutmut_1(item: Item, original_quality: int, expected_increase: int):
    """Verifica que a qualidade aumentou do valor esperado."""
    expected_quality = None
    assert item.quality == expected_quality, \
        f"Qualidade esperada {expected_quality}, obteve {item.quality}"


def x_assert_quality_increased__mutmut_2(item: Item, original_quality: int, expected_increase: int):
    """Verifica que a qualidade aumentou do valor esperado."""
    expected_quality = min(None, original_quality + expected_increase)
    assert item.quality == expected_quality, \
        f"Qualidade esperada {expected_quality}, obteve {item.quality}"


def x_assert_quality_increased__mutmut_3(item: Item, original_quality: int, expected_increase: int):
    """Verifica que a qualidade aumentou do valor esperado."""
    expected_quality = min(50, None)
    assert item.quality == expected_quality, \
        f"Qualidade esperada {expected_quality}, obteve {item.quality}"


def x_assert_quality_increased__mutmut_4(item: Item, original_quality: int, expected_increase: int):
    """Verifica que a qualidade aumentou do valor esperado."""
    expected_quality = min(original_quality + expected_increase)
    assert item.quality == expected_quality, \
        f"Qualidade esperada {expected_quality}, obteve {item.quality}"


def x_assert_quality_increased__mutmut_5(item: Item, original_quality: int, expected_increase: int):
    """Verifica que a qualidade aumentou do valor esperado."""
    expected_quality = min(50, )
    assert item.quality == expected_quality, \
        f"Qualidade esperada {expected_quality}, obteve {item.quality}"


def x_assert_quality_increased__mutmut_6(item: Item, original_quality: int, expected_increase: int):
    """Verifica que a qualidade aumentou do valor esperado."""
    expected_quality = min(51, original_quality + expected_increase)
    assert item.quality == expected_quality, \
        f"Qualidade esperada {expected_quality}, obteve {item.quality}"


def x_assert_quality_increased__mutmut_7(item: Item, original_quality: int, expected_increase: int):
    """Verifica que a qualidade aumentou do valor esperado."""
    expected_quality = min(50, original_quality - expected_increase)
    assert item.quality == expected_quality, \
        f"Qualidade esperada {expected_quality}, obteve {item.quality}"


def x_assert_quality_increased__mutmut_8(item: Item, original_quality: int, expected_increase: int):
    """Verifica que a qualidade aumentou do valor esperado."""
    expected_quality = min(50, original_quality + expected_increase)
    assert item.quality != expected_quality, \
        f"Qualidade esperada {expected_quality}, obteve {item.quality}"

x_assert_quality_increased__mutmut_mutants : ClassVar[MutantDict] = {
'x_assert_quality_increased__mutmut_1': x_assert_quality_increased__mutmut_1, 
    'x_assert_quality_increased__mutmut_2': x_assert_quality_increased__mutmut_2, 
    'x_assert_quality_increased__mutmut_3': x_assert_quality_increased__mutmut_3, 
    'x_assert_quality_increased__mutmut_4': x_assert_quality_increased__mutmut_4, 
    'x_assert_quality_increased__mutmut_5': x_assert_quality_increased__mutmut_5, 
    'x_assert_quality_increased__mutmut_6': x_assert_quality_increased__mutmut_6, 
    'x_assert_quality_increased__mutmut_7': x_assert_quality_increased__mutmut_7, 
    'x_assert_quality_increased__mutmut_8': x_assert_quality_increased__mutmut_8
}

def assert_quality_increased(*args, **kwargs):
    result = _mutmut_trampoline(x_assert_quality_increased__mutmut_orig, x_assert_quality_increased__mutmut_mutants, args, kwargs)
    return result 

assert_quality_increased.__signature__ = _mutmut_signature(x_assert_quality_increased__mutmut_orig)
x_assert_quality_increased__mutmut_orig.__name__ = 'x_assert_quality_increased'


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_orig():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("Normal Item", 10, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_1():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print(None)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("Normal Item", 10, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_2():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" / 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("Normal Item", 10, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_3():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("XX=XX" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("Normal Item", 10, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_4():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 71)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("Normal Item", 10, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_5():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print(None)
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("Normal Item", 10, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_6():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("XXEXEMPLO: Item normal com qualidade dentro dos limitesXX")
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("Normal Item", 10, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_7():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("exemplo: item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("Normal Item", 10, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_8():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: ITEM NORMAL COM QUALIDADE DENTRO DOS LIMITES")
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("Normal Item", 10, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_9():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print(None)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("Normal Item", 10, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_10():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" / 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("Normal Item", 10, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_11():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("XX=XX" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("Normal Item", 10, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_12():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 71)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("Normal Item", 10, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_13():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print(None)
    items = [Item("Normal Item", 10, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_14():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("XX✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10XX")
    items = [Item("Normal Item", 10, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_15():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("✓ given: criando item 'normal item' com qualidade 25 e dias 10")
    items = [Item("Normal Item", 10, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_16():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("✓ GIVEN: CRIANDO ITEM 'NORMAL ITEM' COM QUALIDADE 25 E DIAS 10")
    items = [Item("Normal Item", 10, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_17():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = None
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_18():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item(None, 10, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_19():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("Normal Item", None, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_20():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("Normal Item", 10, None)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_21():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item(10, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_22():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("Normal Item", 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_23():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("Normal Item", 10, )]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_24():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("XXNormal ItemXX", 10, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_25():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("normal item", 10, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_26():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("NORMAL ITEM", 10, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_27():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("Normal Item", 11, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_28():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("Normal Item", 10, 26)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_29():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("Normal Item", 10, 25)]
    gilded_rose = None
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_30():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("Normal Item", 10, 25)]
    gilded_rose = GildedRose(None)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_31():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("Normal Item", 10, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print(None)
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_32():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("Normal Item", 10, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("XX✓ When: Atualizando a qualidadeXX")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_33():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("Normal Item", 10, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ when: atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_34():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("Normal Item", 10, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ WHEN: ATUALIZANDO A QUALIDADE")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_35():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("Normal Item", 10, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print(None)
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_36():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("Normal Item", 10, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("XX✓ Then: Verificando resultadosXX")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_37():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("Normal Item", 10, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ then: verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_38():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("Normal Item", 10, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ THEN: VERIFICANDO RESULTADOS")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_39():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("Normal Item", 10, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[1].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_40():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("Normal Item", 10, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality != 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_41():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("Normal Item", 10, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 25, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_42():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("Normal Item", 10, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[1].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_43():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("Normal Item", 10, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[1].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_44():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("Normal Item", 10, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in != 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_45():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("Normal Item", 10, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 10, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_46():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("Normal Item", 10, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[1].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_47():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("Normal Item", 10, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(None)
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_48():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("Normal Item", 10, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[1].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_49():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("Normal Item", 10, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(None)
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_50():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("Normal Item", 10, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[1].sell_in} ✅")
    print("  PASSOU! ✅\n")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_51():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("Normal Item", 10, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print(None)


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_52():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("Normal Item", 10, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("XX  PASSOU! ✅\nXX")


# ============================================================================
# EXEMPLO DE USO DIRETO (sem pytest-bdd)
# ============================================================================

def x_example_manual_bdd_test__mutmut_53():
    """Exemplo de como testar manualmente sem pytest-bdd."""
    
    print("=" * 70)
    print("EXEMPLO: Item normal com qualidade dentro dos limites")
    print("=" * 70)
    
    # Given
    print("✓ Given: Criando item 'Normal Item' com qualidade 25 e dias 10")
    items = [Item("Normal Item", 10, 25)]
    gilded_rose = GildedRose(items)
    
    # When
    print("✓ When: Atualizando a qualidade")
    gilded_rose.update_quality()
    
    # Then
    print("✓ Then: Verificando resultados")
    assert items[0].quality == 24, f"Esperado 24, obteve {items[0].quality}"
    assert items[0].sell_in == 9, f"Esperado 9, obteve {items[0].sell_in}"
    
    print(f"  → Qualidade: {items[0].quality} ✅")
    print(f"  → Dias: {items[0].sell_in} ✅")
    print("  passou! ✅\n")

x_example_manual_bdd_test__mutmut_mutants : ClassVar[MutantDict] = {
'x_example_manual_bdd_test__mutmut_1': x_example_manual_bdd_test__mutmut_1, 
    'x_example_manual_bdd_test__mutmut_2': x_example_manual_bdd_test__mutmut_2, 
    'x_example_manual_bdd_test__mutmut_3': x_example_manual_bdd_test__mutmut_3, 
    'x_example_manual_bdd_test__mutmut_4': x_example_manual_bdd_test__mutmut_4, 
    'x_example_manual_bdd_test__mutmut_5': x_example_manual_bdd_test__mutmut_5, 
    'x_example_manual_bdd_test__mutmut_6': x_example_manual_bdd_test__mutmut_6, 
    'x_example_manual_bdd_test__mutmut_7': x_example_manual_bdd_test__mutmut_7, 
    'x_example_manual_bdd_test__mutmut_8': x_example_manual_bdd_test__mutmut_8, 
    'x_example_manual_bdd_test__mutmut_9': x_example_manual_bdd_test__mutmut_9, 
    'x_example_manual_bdd_test__mutmut_10': x_example_manual_bdd_test__mutmut_10, 
    'x_example_manual_bdd_test__mutmut_11': x_example_manual_bdd_test__mutmut_11, 
    'x_example_manual_bdd_test__mutmut_12': x_example_manual_bdd_test__mutmut_12, 
    'x_example_manual_bdd_test__mutmut_13': x_example_manual_bdd_test__mutmut_13, 
    'x_example_manual_bdd_test__mutmut_14': x_example_manual_bdd_test__mutmut_14, 
    'x_example_manual_bdd_test__mutmut_15': x_example_manual_bdd_test__mutmut_15, 
    'x_example_manual_bdd_test__mutmut_16': x_example_manual_bdd_test__mutmut_16, 
    'x_example_manual_bdd_test__mutmut_17': x_example_manual_bdd_test__mutmut_17, 
    'x_example_manual_bdd_test__mutmut_18': x_example_manual_bdd_test__mutmut_18, 
    'x_example_manual_bdd_test__mutmut_19': x_example_manual_bdd_test__mutmut_19, 
    'x_example_manual_bdd_test__mutmut_20': x_example_manual_bdd_test__mutmut_20, 
    'x_example_manual_bdd_test__mutmut_21': x_example_manual_bdd_test__mutmut_21, 
    'x_example_manual_bdd_test__mutmut_22': x_example_manual_bdd_test__mutmut_22, 
    'x_example_manual_bdd_test__mutmut_23': x_example_manual_bdd_test__mutmut_23, 
    'x_example_manual_bdd_test__mutmut_24': x_example_manual_bdd_test__mutmut_24, 
    'x_example_manual_bdd_test__mutmut_25': x_example_manual_bdd_test__mutmut_25, 
    'x_example_manual_bdd_test__mutmut_26': x_example_manual_bdd_test__mutmut_26, 
    'x_example_manual_bdd_test__mutmut_27': x_example_manual_bdd_test__mutmut_27, 
    'x_example_manual_bdd_test__mutmut_28': x_example_manual_bdd_test__mutmut_28, 
    'x_example_manual_bdd_test__mutmut_29': x_example_manual_bdd_test__mutmut_29, 
    'x_example_manual_bdd_test__mutmut_30': x_example_manual_bdd_test__mutmut_30, 
    'x_example_manual_bdd_test__mutmut_31': x_example_manual_bdd_test__mutmut_31, 
    'x_example_manual_bdd_test__mutmut_32': x_example_manual_bdd_test__mutmut_32, 
    'x_example_manual_bdd_test__mutmut_33': x_example_manual_bdd_test__mutmut_33, 
    'x_example_manual_bdd_test__mutmut_34': x_example_manual_bdd_test__mutmut_34, 
    'x_example_manual_bdd_test__mutmut_35': x_example_manual_bdd_test__mutmut_35, 
    'x_example_manual_bdd_test__mutmut_36': x_example_manual_bdd_test__mutmut_36, 
    'x_example_manual_bdd_test__mutmut_37': x_example_manual_bdd_test__mutmut_37, 
    'x_example_manual_bdd_test__mutmut_38': x_example_manual_bdd_test__mutmut_38, 
    'x_example_manual_bdd_test__mutmut_39': x_example_manual_bdd_test__mutmut_39, 
    'x_example_manual_bdd_test__mutmut_40': x_example_manual_bdd_test__mutmut_40, 
    'x_example_manual_bdd_test__mutmut_41': x_example_manual_bdd_test__mutmut_41, 
    'x_example_manual_bdd_test__mutmut_42': x_example_manual_bdd_test__mutmut_42, 
    'x_example_manual_bdd_test__mutmut_43': x_example_manual_bdd_test__mutmut_43, 
    'x_example_manual_bdd_test__mutmut_44': x_example_manual_bdd_test__mutmut_44, 
    'x_example_manual_bdd_test__mutmut_45': x_example_manual_bdd_test__mutmut_45, 
    'x_example_manual_bdd_test__mutmut_46': x_example_manual_bdd_test__mutmut_46, 
    'x_example_manual_bdd_test__mutmut_47': x_example_manual_bdd_test__mutmut_47, 
    'x_example_manual_bdd_test__mutmut_48': x_example_manual_bdd_test__mutmut_48, 
    'x_example_manual_bdd_test__mutmut_49': x_example_manual_bdd_test__mutmut_49, 
    'x_example_manual_bdd_test__mutmut_50': x_example_manual_bdd_test__mutmut_50, 
    'x_example_manual_bdd_test__mutmut_51': x_example_manual_bdd_test__mutmut_51, 
    'x_example_manual_bdd_test__mutmut_52': x_example_manual_bdd_test__mutmut_52, 
    'x_example_manual_bdd_test__mutmut_53': x_example_manual_bdd_test__mutmut_53
}

def example_manual_bdd_test(*args, **kwargs):
    result = _mutmut_trampoline(x_example_manual_bdd_test__mutmut_orig, x_example_manual_bdd_test__mutmut_mutants, args, kwargs)
    return result 

example_manual_bdd_test.__signature__ = _mutmut_signature(x_example_manual_bdd_test__mutmut_orig)
x_example_manual_bdd_test__mutmut_orig.__name__ = 'x_example_manual_bdd_test'


if __name__ == "__main__":
    # Executar exemplo manual
    example_manual_bdd_test()
    
    print("Para executar todos os cenários BDD:")
    print("  pytest --gherkin-terminal-reporter GILDED_ROSE_BDD.feature -v")
    print("\nOu com behave:")
    print("  behave features/")

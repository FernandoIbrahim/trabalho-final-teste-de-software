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
def x_pre_mutation__mutmut_orig(context):
    """Configuration for mutmut mutation testing"""
    # Only mutate the gilded_rose.py file
    if "gilded_rose.py" not in context.filename:
        context.skip = True
def x_pre_mutation__mutmut_1(context):
    """Configuration for mutmut mutation testing"""
    # Only mutate the gilded_rose.py file
    if "XXgilded_rose.pyXX" not in context.filename:
        context.skip = True
def x_pre_mutation__mutmut_2(context):
    """Configuration for mutmut mutation testing"""
    # Only mutate the gilded_rose.py file
    if "GILDED_ROSE.PY" not in context.filename:
        context.skip = True
def x_pre_mutation__mutmut_3(context):
    """Configuration for mutmut mutation testing"""
    # Only mutate the gilded_rose.py file
    if "gilded_rose.py" in context.filename:
        context.skip = True
def x_pre_mutation__mutmut_4(context):
    """Configuration for mutmut mutation testing"""
    # Only mutate the gilded_rose.py file
    if "gilded_rose.py" not in context.filename:
        context.skip = None
def x_pre_mutation__mutmut_5(context):
    """Configuration for mutmut mutation testing"""
    # Only mutate the gilded_rose.py file
    if "gilded_rose.py" not in context.filename:
        context.skip = False

x_pre_mutation__mutmut_mutants : ClassVar[MutantDict] = {
'x_pre_mutation__mutmut_1': x_pre_mutation__mutmut_1, 
    'x_pre_mutation__mutmut_2': x_pre_mutation__mutmut_2, 
    'x_pre_mutation__mutmut_3': x_pre_mutation__mutmut_3, 
    'x_pre_mutation__mutmut_4': x_pre_mutation__mutmut_4, 
    'x_pre_mutation__mutmut_5': x_pre_mutation__mutmut_5
}

def pre_mutation(*args, **kwargs):
    result = _mutmut_trampoline(x_pre_mutation__mutmut_orig, x_pre_mutation__mutmut_mutants, args, kwargs)
    return result 

pre_mutation.__signature__ = _mutmut_signature(x_pre_mutation__mutmut_orig)
x_pre_mutation__mutmut_orig.__name__ = 'x_pre_mutation'

def pre_mutation(context):
    """Configuration for mutmut mutation testing"""
    # Only mutate the gilded_rose.py file
    if "gilded_rose.py" not in context.filename:
        context.skip = True

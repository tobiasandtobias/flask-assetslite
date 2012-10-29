def listify(items):
    """
    Helper for ensuring something is a list.
    """
    return items if type(items) is list else [items]

"""Validation utility functions for OpenMotics services."""
from .const import _LOGGER


def get_key_for_word(dictionary, word):
    try:
        for key, value in dictionary.items():
            if value == word:
                return key
        return None

    except KeyError as er:
        _LOGGER.error(er)
        return None


def _obj_to_dict(obj):
    """Convert an object into a hash for debug."""
    return {
        key: getattr(obj, key)
        for key in dir(obj)
        if key[0] != "_" and not callable(getattr(obj, key))
    }

# def nice_print_node(node):
#     """Print a nice formatted node to the output (debug method)."""
#     node_dict = _obj_to_dict(node)
#     node_dict["values"] = {
#         value_id: _obj_to_dict(value) for value_id, value in node.values.items()
#     }

#     _LOGGER.info("FOUND NODE %s \n%s", node.product_name, node_dict)


# def get_config_value(node, value_index, tries=5):
#     """Return the current configuration value for a specific index."""
#     try:
#         for value in node.values.values():
#             if (
#                 value.command_class == const.COMMAND_CLASS_CONFIGURATION
#                 and value.index == value_index
#             ):
#                 return value.data
#     except RuntimeError:
#         # If we get a runtime error the dict has changed while
#         # we was looking for a value, just do it again
#         return (
#             None if tries <= 0 else get_config_value(node, value_index, tries=tries - 1)
#         )
#     return None

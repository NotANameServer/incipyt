from incipyt import variables

_stage = "__init__"


def default(var_key, default_value):
    """Set `default` field for an existing metadata.

    :param var_key: environment variable name
    :type var_key: `str`
    :param default_value: new default value for the environment variable
    :type default_value: `str`
    """
    if _stage not in ("add_to_structure", "pre"):
        raise RuntimeError(f"Metadata field default cannot be set during {_stage} stage")
    variables.metadata[var_key].default = default_value


def do_not_prompt(var_key):
    """Set `do_not_prompt` field to `True` for an existing metadata.

    :param var_key: environment variable name
    :type var_key: `str`
    """
    if _stage not in ("add_to_structure",):
        raise RuntimeError(f"Metadata field do_not_prompt cannot be set during {_stage} stage")
    variables.metadata[var_key].do_not_prompt = True


def required(var_key):
    """Set `required` field to `True` for an existing metadata.

    :param var_key: environment variable name
    :type var_key: `str`
    """
    if _stage not in ("__init__", "add_to_structure"):
        raise RuntimeError(f"Metadata field required cannot be set during {_stage} stage")
    variables.metadata[var_key].required = True

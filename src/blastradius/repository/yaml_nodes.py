"""Restricted YAML/JSON composition with deterministic source locations."""

import yaml
from yaml.nodes import MappingNode, Node, ScalarNode, SequenceNode

from ..model import GraphError


MAX_DOCUMENT_NODES = 20_000
MAX_DOCUMENT_DEPTH = 60
STANDARD_TAGS = frozenset({
    "tag:yaml.org,2002:map",
    "tag:yaml.org,2002:seq",
    "tag:yaml.org,2002:str",
})


class DocumentSyntaxError(ValueError):
    """A selected text file is malformed but not structurally unsafe."""


def compose_document(payload: bytes) -> Node:
    try:
        source = payload.decode("utf-8-sig")
    except UnicodeError:
        raise DocumentSyntaxError("Selected document is not valid UTF-8.") from None
    try:
        root = yaml.compose(source, Loader=yaml.BaseLoader)
    except yaml.YAMLError:
        raise DocumentSyntaxError("Selected document is not valid YAML or JSON.") from None
    if root is None:
        raise DocumentSyntaxError("Selected document is empty.")

    seen = set()
    count = 0

    def validate(node, depth):
        nonlocal count
        if depth > MAX_DOCUMENT_DEPTH:
            raise GraphError("Selected document exceeds the safe YAML depth limit.")
        identifier = id(node)
        if identifier in seen:
            raise GraphError("Selected document contains a YAML alias.")
        seen.add(identifier)
        count += 1
        if count > MAX_DOCUMENT_NODES:
            raise GraphError("Selected document exceeds the safe YAML node-count limit.")
        if node.tag not in STANDARD_TAGS:
            raise GraphError("Selected document contains a custom YAML tag.")
        if isinstance(node, MappingNode):
            keys = set()
            for key, value in node.value:
                if not isinstance(key, ScalarNode):
                    raise GraphError("Selected document contains a non-scalar mapping key.")
                if key.value == "<<":
                    raise GraphError("Selected document contains a YAML merge key.")
                if key.value in keys:
                    raise GraphError("Selected document contains a duplicate mapping key.")
                keys.add(key.value)
                validate(key, depth + 1)
                validate(value, depth + 1)
        elif isinstance(node, SequenceNode):
            for value in node.value:
                validate(value, depth + 1)
        elif not isinstance(node, ScalarNode):
            raise GraphError("Selected document contains an unsupported YAML node.")

    validate(root, 1)
    return root


def mapping(node):
    if not isinstance(node, MappingNode):
        return None
    return {key.value: value for key, value in node.value}


def sequence(node):
    return list(node.value) if isinstance(node, SequenceNode) else None


def scalar(node):
    return node.value if isinstance(node, ScalarNode) else None


def scalar_list(node):
    if isinstance(node, ScalarNode):
        return [node.value]
    if isinstance(node, SequenceNode) and all(isinstance(item, ScalarNode) for item in node.value):
        return [item.value for item in node.value]
    return None


def location(path, node):
    return {
        "path": path,
        "start_line": node.start_mark.line + 1,
        "start_column": node.start_mark.column + 1,
        "end_line": node.end_mark.line + 1,
        "end_column": node.end_mark.column + 1,
    }

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
CLOUDFORMATION_TAGS = frozenset("!" + name for name in (
    "Ref", "Condition", "Base64", "Cidr", "FindInMap", "GetAtt", "GetAZs", "ImportValue",
    "Join", "Select", "Split", "Sub", "Transform", "If", "Equals", "And", "Not", "Or", "Length", "ToJsonString",
))


class DocumentSyntaxError(ValueError):
    """A selected text file is malformed but not structurally unsafe."""


def compose_document(payload: bytes, *, allow_cloudformation_tags=False) -> Node:
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
        if node.tag not in STANDARD_TAGS and not (allow_cloudformation_tags and node.tag in CLOUDFORMATION_TAGS):
            raise GraphError("Selected document contains a custom YAML tag.")
        if isinstance(node, MappingNode):
            keys = set()
            for key, value in node.value:
                if not isinstance(key, ScalarNode) or key.tag != "tag:yaml.org,2002:str":
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
    if not isinstance(node, MappingNode) or node.tag != "tag:yaml.org,2002:map":
        return None
    return {key.value: value for key, value in node.value}


def sequence(node):
    return list(node.value) if isinstance(node, SequenceNode) and node.tag == "tag:yaml.org,2002:seq" else None


def scalar(node):
    return node.value if isinstance(node, ScalarNode) and node.tag == "tag:yaml.org,2002:str" else None


def scalar_list(node):
    if scalar(node) is not None:
        return [node.value]
    if sequence(node) is not None and all(scalar(item) is not None for item in node.value):
        return [item.value for item in node.value]
    return None


def intrinsic_locations(path, root):
    found = []
    pending = [root]
    while pending:
        node = pending.pop()
        if node.tag in CLOUDFORMATION_TAGS:
            found.append(location(path, node))
        if isinstance(node, MappingNode):
            for key, value in node.value:
                if key.value == "Ref" or key.value.startswith("Fn::"):
                    found.append(location(path, key))
                pending.extend((key, value))
        elif isinstance(node, SequenceNode):
            pending.extend(node.value)
    return sorted(found, key=lambda source: (source["start_line"], source["start_column"]))


def location(path, node):
    return {
        "path": path,
        "start_line": node.start_mark.line + 1,
        "start_column": node.start_mark.column + 1,
        "end_line": node.end_mark.line + 1,
        "end_column": node.end_mark.column + 1,
    }

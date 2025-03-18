"""Utility functions for the graphics module."""

from textual.widget import Widget


def set_only_class(obj: Widget, class_name: str) -> None:
    """Sets the only class of the object to the given class name, removes all others."""
    obj.remove_class(*obj.classes)
    obj.set_class(True, class_name)

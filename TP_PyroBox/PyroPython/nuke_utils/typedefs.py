"""Type definitions to be used by the functions of the package as well as any other modules depending on it"""


from __future__ import annotations

# Built-in imports
from typing import Dict, List, TypeVar, Union

"""A generic type variable that represents the different data types of the
values that could be held by Nuke's knobs"""
NukeKnobVal = TypeVar("NukeKnobVal", str, int, float, bool, "Format")  # type: ignore # noqa

NukeMetadataVal = TypeVar("NukeMetadataVal", str, int, float, bool, List)

MetadataReturnType = Union[Dict[str, NukeMetadataVal], NukeMetadataVal]

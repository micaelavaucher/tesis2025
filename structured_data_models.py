"""Structured data models for world generation."""

# ----------------------------------------- #
# Imports and Configs                       #
# ----------------------------------------- #
from pydantic import BaseModel
from typing import List

# ----------------------------------------- #
# Model Definitions                         #
# ----------------------------------------- #
class GeneratedItem(BaseModel):
    name: str
    descriptions: List[str]
    gettable: bool = True

class BlockedPassage(BaseModel):
    """Model for a blocked passage between locations."""
    location: str
    obstacle: str
    symmetric: bool = True

class GeneratedLocation(BaseModel):
    name: str
    descriptions: List[str]
    items: List[str] = []
    connecting_locations: List[str] = []
    blocked_passages: List[BlockedPassage] = []

class GeneratedCharacter(BaseModel):
    name: str
    descriptions: List[str]
    location: str
    inventory: List[str] = []

class GeneratedWorld(BaseModel):
    locations: List[GeneratedLocation]
    items: List[GeneratedItem]
    characters: List[GeneratedCharacter]
    player: GeneratedCharacter

class WorldExpansion(BaseModel):
    new_locations: List[GeneratedLocation]
    new_items: List[GeneratedItem]
    new_characters: List[GeneratedCharacter]
    connect_to_current: bool = True
"""Structured data models for the PAYADOR world system."""

#---- Imports -----------------------------------------------------------------
from pydantic import BaseModel
from typing import List, Optional

#---- Schema definitions ------------------------------------------------------
# Basic world component models
class MovedObject(BaseModel):
    object_name: str
    new_location: str

class BlockedPassageAvailable(BaseModel):
    location_name: str
    is_available: bool = True

class LocationChange(BaseModel):
    new_location: Optional[str] = None

# World update model
class WorldUpdate(BaseModel):
    """Model for structured world updates from language model."""
    moved_objects: List[MovedObject] = []
    blocked_passages_available: List[BlockedPassageAvailable] = []
    location_changed: LocationChange = LocationChange()
    narration: str = ""

# Narration models
class SceneNarration(BaseModel):
    """Model for structured scene narrations."""
    narration: str
    mood: str = "neutral"  # could be "tense", "peaceful", "mysterious", etc.
    
class GeneratedObjective(BaseModel):
    """Model for a generated objective."""
    type: str  # "item_to_location", "find_character", "get_item", "reach_location"
    components: List[str]  # Names of the components involved
    description: str  # Human-readable description

class ObjectiveDescription(BaseModel):
    """Model for structured objective descriptions."""
    description: str
    difficulty: str = "medium"  # could be "easy", "medium", "hard"

# Optional: World generation models
class GeneratedItem(BaseModel):
    name: str
    descriptions: List[str]
    gettable: bool = True

class GeneratedPuzzle(BaseModel):
    name: str
    descriptions: List[str]
    problem: str
    answer: str

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
    puzzles: List[GeneratedPuzzle] = []
    player: GeneratedCharacter
    objective: GeneratedObjective

class WorldExpansion(BaseModel):
    new_locations: List[GeneratedLocation]
    new_items: List[GeneratedItem]
    new_characters: List[GeneratedCharacter]
    new_puzzles: List[GeneratedPuzzle] = []
    connect_to_current: bool = True

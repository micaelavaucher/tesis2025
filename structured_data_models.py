"""Structured data models for the PAYADOR world system."""

#---- Imports -----------------------------------------------------------------
from pydantic import BaseModel, Field
from typing import List, Optional

#---- Schema definitions ------------------------------------------------------
# Basic world component models
class MovedObject(BaseModel):
    object_name: str = Field(description="Name of the object that was moved")
    new_location: str = Field(description="Name of the location where the object is now placed")

class BlockedPassageAvailable(BaseModel):
    location_name: str = Field(description="Name of the location where the blocked passage status changed")
    is_available: bool = Field(default=True, description="Whether the passage is now available (True) or blocked (False)")

class LocationChange(BaseModel):
    new_location: Optional[str] = Field(default=None, description="Name of the new location where the player moved, or None if no movement occurred")

# World update model
class WorldUpdate(BaseModel):
    """Model for structured world updates from language model."""
    moved_objects: List[MovedObject] = Field(default=[], description="List of objects that were moved to different locations")
    blocked_passages_available: List[BlockedPassageAvailable] = Field(default=[], description="List of blocked passages whose availability status changed")
    location_changed: LocationChange = Field(default=LocationChange(), description="Information about player location change")
    narration: str = Field(description="Narrative text describing what happened in the world")

class GeneratedObjective(BaseModel):
    """Model for a generated objective."""
    type: str = Field(description="Type of objective: 'item_to_location', 'find_character', 'get_item', or 'reach_location'")
    components: List[str] = Field(description="Names of the components involved in the objective (items, characters, locations)")
    description: str = Field(description="Clear, engaging description of what the player needs to accomplish")

class GeneratedItem(BaseModel):
    name: str = Field(description="Unique name of the item")
    descriptions: List[str] = Field(description="List of descriptive texts for the item from different perspectives or states")
    gettable: bool = Field(default=True, description="Whether the item can be picked up by the player")

class GeneratedPuzzle(BaseModel):
    name: str = Field(description="Unique name of the puzzle")
    descriptions: List[str] = Field(description="List of descriptive texts explaining the puzzle from different angles")
    problem: str = Field(description="Clear statement of the puzzle problem or challenge")
    answer: str = Field(description="The solution or answer to the puzzle")

class BlockedPassage(BaseModel):
    """Model for a blocked passage between locations."""
    location: str = Field(description="Name of the destination location that is blocked from the current location")
    obstacle: str = Field(description="Description of what is blocking the passage (e.g., 'locked door', 'fallen rocks')")
    symmetric: bool = Field(default=True, description="Whether the blockage works both ways (True) or only one direction (False)")

class GeneratedLocation(BaseModel):
    name: str = Field(description="Unique name of the location")
    descriptions: List[str] = Field(description="List of atmospheric descriptions of the location for variety")
    items: List[str] = Field(default=[], description="Names of items initially present in this location")
    connecting_locations: List[str] = Field(default=[], description="Names of locations directly accessible from this location")
    blocked_passages: List[BlockedPassage] = Field(default=[], description="List of passages that are currently blocked from this location")

class GeneratedCharacter(BaseModel):
    name: str = Field(description="Unique name of the character")
    descriptions: List[str] = Field(description="List of character descriptions including appearance and personality traits")
    location: str = Field(description="Name of the location where this character is initially placed")
    inventory: List[str] = Field(default=[], description="Names of items this character starts with")

class GeneratedWorld(BaseModel):
    locations: List[GeneratedLocation] = Field(description="All locations in the world")
    items: List[GeneratedItem] = Field(description="All items available in the world")
    characters: List[GeneratedCharacter] = Field(description="All non-player characters in the world")
    puzzles: List[GeneratedPuzzle] = Field(default=[], description="All puzzles that can be encountered in the world")
    player: GeneratedCharacter = Field(description="The player character with starting location and inventory")
    objective: GeneratedObjective = Field(description="The main objective the player needs to complete")

class WorldExpansion(BaseModel):
    new_locations: List[GeneratedLocation] = Field(description="New locations to add to the existing world")
    new_items: List[GeneratedItem] = Field(description="New items to add to the existing world")
    new_characters: List[GeneratedCharacter] = Field(description="New characters to add to the existing world")
    new_puzzles: List[GeneratedPuzzle] = Field(default=[], description="New puzzles to add to the existing world")
    connect_to_current: bool = Field(default=True, description="Whether to automatically connect new locations to the existing world")
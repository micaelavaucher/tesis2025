"""Structured data models for the PAYADOR world system with semantic connections."""

#---- Imports -----------------------------------------------------------------
from pydantic import BaseModel, Field
from typing import List, Optional, Union
from enum import Enum

#---- Enums and Types ---------------------------------------------------------
class PuzzleType(str, Enum):
    RIDDLE = "riddle"  # Adivinanza
    LOGIC = "logic"    # Problema lógico
    WORDPLAY = "wordplay"  # Juego de palabras
    OBSERVATION = "observation"  # Observar detalles del entorno
    SEQUENCE = "sequence"  # Ordenar cosas en secuencia
    CODE = "code"  # Descifrar códigos
    MEMORY = "memory"  # Recordar información previa

class ObjectiveType(str, Enum):
    REACH_LOCATION = "reach_location"  # Llegar a un lugar
    GET_ITEM = "get_item"  # Conseguir un objeto
    DELIVER_ITEM = "deliver_item"  # Entregar objeto a alguien/algún lugar
    FIND_CHARACTER = "find_character"  # Encontrar a un personaje
    SOLVE_MYSTERY = "solve_mystery"  # Resolver un misterio general

class ConnectionType(str, Enum):
    BLOCKS_PASSAGE = "blocks_passage"  # Bloquea el paso a una ubicación
    GIVES_ITEM = "gives_item"  # Da un objeto
    UNLOCKS_INFORMATION = "unlocks_information"  # Revela información importante
    ENABLES_OBJECTIVE = "enables_objective"  # Habilita completar el objetivo directamente

#---- Core Connection Models -------------------------------------------------
class WorldConnection(BaseModel):
    """Base model for connections between world elements."""
    connection_type: ConnectionType = Field(description="Type of connection this represents")
    description: str = Field(description="Human-readable description of why this connection exists")

class PassageConnection(WorldConnection):
    """Connection that blocks/unblocks a passage."""
    connection_type: ConnectionType = Field(default=ConnectionType.BLOCKS_PASSAGE)
    from_location: str = Field(description="Location where the passage originates")
    to_location: str = Field(description="Destination location that gets unblocked")
    
class ItemConnection(WorldConnection):
    """Connection that provides an item."""
    connection_type: ConnectionType = Field(default=ConnectionType.GIVES_ITEM)
    item_name: str = Field(description="Name of the item this connection provides")
    
class InformationConnection(WorldConnection):
    """Connection that provides crucial information."""
    connection_type: ConnectionType = Field(default=ConnectionType.UNLOCKS_INFORMATION)
    information: str = Field(description="The important information revealed")
    
class ObjectiveConnection(WorldConnection):
    """Connection that directly enables objective completion."""
    connection_type: ConnectionType = Field(default=ConnectionType.ENABLES_OBJECTIVE)

#---- Requirement Models -----------------------------------------------------
class Requirement(BaseModel):
    """Base model for requirements to unlock connections."""
    requirement_type: str = Field(description="Type of requirement")
    description: str = Field(description="What needs to be done to fulfill this requirement")

class ItemRequirement(Requirement):
    """Requirement to bring a specific item."""
    requirement_type: str = Field(default="item")
    item_name: str = Field(description="Name of the required item")
    
class PuzzleRequirement(Requirement):
    """Requirement to solve a puzzle."""
    requirement_type: str = Field(default="puzzle")
    puzzle_name: str = Field(description="Name of the puzzle that must be solved")

#---- Enhanced Models --------------------------------------------------------
class GeneratedPuzzle(BaseModel):
    name: str = Field(description="Unique name of the puzzle")
    puzzle_type: PuzzleType = Field(description="Type of puzzle")
    descriptions: List[str] = Field(description="List of descriptive texts explaining the puzzle")
    problem: str = Field(description="Clear statement of the puzzle problem")
    answer: str = Field(description="The solution to the puzzle")
    location: Optional[str] = Field(default=None, description="Location where puzzle is found, or None if given by character")
    proposed_by_character: Optional[str] = Field(default=None, description="Character who proposes this puzzle, or None if environmental")
    connections: List[Union[PassageConnection, ItemConnection, InformationConnection, ObjectiveConnection]] = Field(
        description="What this puzzle unlocks when solved"
    )
    relevance_to_objective: str = Field(description="How solving this puzzle helps achieve the main objective")

class GeneratedItem(BaseModel):
    name: str = Field(description="Unique name of the item")
    descriptions: List[str] = Field(description="List of descriptive texts for the item")
    gettable: bool = Field(default=True, description="Whether the item can be picked up")
    relevance_to_objective: Optional[str] = Field(default=None, description="How this item helps with the main objective, or None if decorative")
    required_for: List[str] = Field(default=[], description="Names of puzzles, characters, or locations this item is required for")

class CharacterInteraction(BaseModel):
    """Defines how a character interacts with the player."""
    gives_information: Optional[str] = Field(default=None, description="Important information the character provides")
    gives_item: Optional[str] = Field(default=None, description="Item the character gives")
    requires: List[Union[ItemRequirement, PuzzleRequirement]] = Field(default=[], description="What the character needs before helping")
    relevance_to_objective: str = Field(description="How this character helps achieve the main objective")

class GeneratedCharacter(BaseModel):
    name: str = Field(description="Unique name of the character")
    descriptions: List[str] = Field(description="List of character descriptions")
    location: str = Field(description="Location where this character is placed")
    inventory: List[str] = Field(default=[], description="Items this character starts with")
    interaction: Optional[CharacterInteraction] = Field(default=None, description="How this character can help the player, or None if just decorative")

class BlockedPassage(BaseModel):
    location: str = Field(description="Destination location that is blocked")
    obstacle_description: str = Field(description="Description of the physical obstacle")
    required_to_unblock: Union[ItemRequirement, PuzzleRequirement] = Field(description="What's needed to unblock this passage")
    relevance_to_objective: str = Field(description="Why accessing this location is important for the objective")

class GeneratedLocation(BaseModel):
    name: str = Field(description="Unique name of the location")
    descriptions: List[str] = Field(description="List of atmospheric descriptions")
    items: List[str] = Field(default=[], description="Names of items initially present")
    connecting_locations: List[str] = Field(default=[], description="Directly accessible locations")
    blocked_passages: List[BlockedPassage] = Field(default=[], description="Blocked passages with their requirements")
    relevance_to_objective: Optional[str] = Field(default=None, description="How this location relates to the main objective")

class ObjectiveComponent(BaseModel):
    """Represents a component involved in the objective."""
    name: str = Field(description="Name of the component (item, character, or location)")
    component_type: str = Field(description="Type: 'item', 'character', or 'location'")
    role_in_objective: str = Field(description="What role this component plays in completing the objective")

class GeneratedObjective(BaseModel):
    type: ObjectiveType = Field(description="Type of the main objective")
    components: List[ObjectiveComponent] = Field(description="All components involved in this objective")
    description: str = Field(description="Clear description of what the player needs to accomplish")
    success_conditions: List[str] = Field(description="Specific conditions that must be met to complete the objective")

class DependencyChain(BaseModel):
    """Represents a chain of dependencies leading to the objective."""
    chain_description: str = Field(description="Description of this dependency chain")
    steps: List[str] = Field(description="Ordered list of steps in this chain")
    elements_involved: List[str] = Field(description="Names of all world elements involved in this chain")

class GeneratedWorld(BaseModel):
    locations: List[GeneratedLocation] = Field(description="All locations in the world")
    items: List[GeneratedItem] = Field(description="All items in the world")
    characters: List[GeneratedCharacter] = Field(description="All non-player characters")
    puzzles: List[GeneratedPuzzle] = Field(description="All puzzles in the world")
    player: GeneratedCharacter = Field(description="The player character")
    objective: GeneratedObjective = Field(description="The main objective")
    dependency_chains: List[DependencyChain] = Field(description="Possible paths to complete the objective")
    world_theme: str = Field(description="Overall theme or setting of the world")
    narrative_context: str = Field(description="Background story that explains why everything is connected")

#---- World Update Models (existing, keeping for compatibility) --------------
class MovedObject(BaseModel):
    object_name: str = Field(description="Name of the object that was moved")
    new_location: str = Field(description="Name of the location where the object is now placed")

class BlockedPassageAvailable(BaseModel):
    location_name: str = Field(description="Name of the location where the blocked passage status changed")
    is_available: bool = Field(default=True, description="Whether the passage is now available")

class LocationChange(BaseModel):
    new_location: Optional[str] = Field(default=None, description="Name of the new location where the player moved")

class WorldUpdate(BaseModel):
    moved_objects: List[MovedObject] = Field(default=[], description="List of objects that were moved")
    blocked_passages_available: List[BlockedPassageAvailable] = Field(default=[], description="List of blocked passages that changed status")
    location_changed: LocationChange = Field(default=LocationChange(), description="Player location change information")
    narration: str = Field(description="Narrative text describing what happened")

#---- Expansion Models -------------------------------------------------------
class WorldExpansion(BaseModel):
    """Model for expanding existing worlds with new connected areas."""
    new_locations: List[GeneratedLocation] = Field(default=[], description="New locations to add")
    new_items: List[GeneratedItem] = Field(default=[], description="New items to add")
    new_characters: List[GeneratedCharacter] = Field(default=[], description="New characters to add")
    new_puzzles: List[GeneratedPuzzle] = Field(default=[], description="New puzzles to add")
    connections_to_existing: List[str] = Field(description="How the new content connects to existing world")
    expansion_narrative: str = Field(description="Story reason for why these new areas are now accessible")
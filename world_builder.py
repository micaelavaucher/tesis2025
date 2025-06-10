"""Module to generate and expand the world dynamically using LLMs."""

# ----------------------------------------- #
# Imports and Configs                       #
# ----------------------------------------- #
import json
from typing import Dict

from world import World, Location, Item, Character, Puzzle
from structured_data_models import GeneratedWorld, WorldExpansion

# ----------------------------------------- #
# Main functions for creating the world     #
# ----------------------------------------- #
def create_world_from_llm_response(world_data) -> World:
    """Parse structured LLM response and create a World object."""
    try:
        # Handle both dict and string inputs
        if isinstance(world_data, dict):
            data = world_data
        else:
            data = json.loads(world_data)
            
        # Parse the JSON response
        generated_world = GeneratedWorld.model_validate(data)

        # Create items first so they can be referenced
        items_dict: Dict[str, Item] = {}
        for item_data in generated_world.items:
            item = Item(
                name=item_data.name,
                descriptions=item_data.descriptions,
                gettable=item_data.gettable)
            items_dict[item_data.name] = item
        
        # Create puzzles
        puzzles_dict: Dict[str, Puzzle] = {}
        for puzzle_data in generated_world.puzzles:
            puzzle = Puzzle(
                name=puzzle_data.name,
                descriptions=puzzle_data.descriptions,
                problem=puzzle_data.problem,
                answer=puzzle_data.answer)
            puzzles_dict[puzzle_data.name] = puzzle
        
        # Create locations (without connections yet)
        locations_dict: Dict[str, Location] = {}
        for loc_data in generated_world.locations:
            location_items = [items_dict[item_name] for
                              item_name in loc_data.items if
                              item_name in items_dict]
            location = Location(
                name=loc_data.name,
                descriptions=loc_data.descriptions,
                items=location_items)
            locations_dict[loc_data.name] = location

        # Connect locations
        for loc_data in generated_world.locations:
            for connected_loc_name in loc_data.connecting_locations:
                if connected_loc_name in locations_dict:
                    locations_dict[loc_data.name].connecting_locations.append(locations_dict[connected_loc_name])
            
            # Handle blocked passages
            for blocked in loc_data.blocked_passages:
                if (blocked.location in locations_dict and 
                    blocked.obstacle in items_dict):
                    location = locations_dict[loc_data.name]
                    blocked_location = locations_dict[blocked.location]
                    
                    # Check if the locations are connected before blocking
                    if blocked_location not in location.connecting_locations:
                        # Connect the locations first
                        location.connecting_locations.append(blocked_location)
                        if blocked.symmetric:
                            blocked_location.connecting_locations.append(location)
                    
                    # Now block the passage
                    location.block_passage(
                        blocked_location, 
                        items_dict[blocked.obstacle],
                        blocked.symmetric)
        
        # Create the player character
        player_data = generated_world.player
        player_inventory = [items_dict[item_name] for
                            item_name in player_data.inventory if
                            item_name in items_dict]
        player_location = locations_dict.get(player_data.location)

        if not player_location:
            # Default to first location if specified location doesn't exist
            player_location = next(iter(locations_dict.values()))
        
        player = Character(
            name=player_data.name,
            descriptions=player_data.descriptions,
            location=player_location,
            inventory=player_inventory)
        
        # Create NPCs
        characters_list = []
        for char_data in generated_world.characters:
            char_inventory = [items_dict[item_name] for
                              item_name in char_data.inventory if
                              item_name in items_dict]
            char_location = locations_dict.get(char_data.location)

            if not char_location:
                # Default to player location if specified location doesn't exist
                char_location = player_location
            
            character = Character(
                name=char_data.name,
                descriptions=char_data.descriptions,
                location=char_location,
                inventory=char_inventory)
            characters_list.append(character)

        # Create the world
        world = World(player)

        # Add all elements to the world
        for location in locations_dict.values():
            world.add_location(location)
        
        for item in items_dict.values():
            world.add_item(item)

        for character in characters_list:
            world.add_character(character)
            
        for puzzle in puzzles_dict.values():
            world.add_puzzle(puzzle)

        # Set the objective if it exists
        if hasattr(generated_world, 'objective') and generated_world.objective:
            world.objective = set_objective_from_generated(
                generated_world.objective, 
                items_dict, 
                locations_dict, 
                characters_list, 
                player)
            print(f"Objective set: {world.objective}")

        return world
    except Exception as e:
        print(f"Error creating world from LLM response: {e}")
        import traceback
        traceback.print_exc()
        # Fallback to the default world
        import example_worlds
        return example_worlds.get_world("1")

def set_objective_from_generated(objective_data, items_dict, locations_dict, characters_list, player):
    """Create an objective tuple from generated data."""
    try:
        obj_type = objective_data.type.lower()
        components = objective_data.components
        
        print(f"Setting objective: type={obj_type}, components={components}")
        
        # Handle Spanish and English objective types
        if obj_type in ["get_item", "encontrar", "conseguir"]:
            if len(components) > 0:
                item_name = components[0]
                if item_name in items_dict:
                    return (player, items_dict[item_name])
        
        elif obj_type in ["find_character", "encontrar_personaje"]:
            if len(components) > 0:
                char_name = components[0]
                character = next((c for c in characters_list if c.name == char_name), None)
                if character:
                    return (player, character)
        
        elif obj_type in ["reach_location", "ir_a", "llegar_a"]:
            if len(components) > 0:
                location_name = components[0]
                if location_name in locations_dict:
                    return (player, locations_dict[location_name])
        
        elif obj_type in ["item_to_location", "llevar_objeto"]:
            if len(components) >= 2:
                item_name, location_name = components[0], components[1]
                if item_name in items_dict and location_name in locations_dict:
                    return (items_dict[item_name], locations_dict[location_name])
        
        # If no specific match, try to infer from description
        description = objective_data.description.lower()
        
        # Check if it's about finding an item
        for item_name in items_dict:
            if item_name.lower() in description:
                return (player, items_dict[item_name])
        
        # Check if it's about reaching a location
        for location_name in locations_dict:
            if location_name.lower() in description:
                return (player, locations_dict[location_name])
        
        # Check if it's about finding a character
        for character in characters_list:
            if character.name.lower() in description:
                return (player, character)
                
        print(f"Could not parse objective: {objective_data}")
        return None
        
    except Exception as e:
        print(f"Error setting objective: {e}")
        return None

def expand_world_from_llm_response(world: World, response: str) -> None:
    """Parse structured LLM response and expand an existing World object."""
    try:
        # Parse the JSON response
        expansion_data = json.loads(response)
        world_expansion = WorldExpansion.model_validate(expansion_data)

        # Create new items
        items_dict: Dict[str, Item] = {}
        for item_data in world_expansion.new_items:
            item = Item(
                name=item_data.name,
                descriptions=item_data.descriptions,
                gettable=item_data.gettable)
            items_dict[item_data.name] = item
            world.add_item(item)
        
        # Create new puzzles
        puzzles_dict: Dict[str, Puzzle] = {}
        for puzzle_data in world_expansion.new_puzzles:
            puzzle = Puzzle(
                name=puzzle_data.name,
                descriptions=puzzle_data.descriptions,
                problem=puzzle_data.problem,
                answer=puzzle_data.answer)
            puzzles_dict[puzzle_data.name] = puzzle
            world.add_puzzle(puzzle)
        
        # Create new locations
        locations_dict: Dict[str, Location] = {}
        for loc_data in world_expansion.new_locations:
            location_items = [items_dict[item_name] for item_name in loc_data.items if item_name in items_dict]
            location = Location(
                name=loc_data.name,
                descriptions=loc_data.descriptions,
                items=location_items
            )
            locations_dict[loc_data.name] = location
            world.add_location(location)

        # Connect new locations to each other
        for loc_data in world_expansion.new_locations:
            for connected_loc_name in loc_data.connecting_locations:
                if connected_loc_name in locations_dict:
                    locations_dict[loc_data.name].connecting_locations \
                        .append(locations_dict[connected_loc_name])
        
        # Connect to player's current location if specified
        if world_expansion.connect_to_current:
            for location in locations_dict.values():
                world.player.location.connecting_locations.append(location)
                location.connecting_locations.append(world.player.location)
        
        # Handle blocked passages
        for loc_data in world_expansion.new_locations:
            for blocked in loc_data.blocked_passages:
                if (blocked.location in locations_dict and
                    blocked.obstacle in items_dict):
                    location = locations_dict[loc_data.name]
                    blocked_location = locations_dict[blocked.location]
                    
                    # Check if the locations are connected before blocking
                    if blocked_location not in location.connecting_locations:
                        # Connect the locations first
                        location.connecting_locations.append(blocked_location)
                        if blocked.symmetric:
                            blocked_location.connecting_locations.append(location)
                    
                    # Now block the passage
                    location.block_passage(
                        blocked_location, 
                        items_dict[blocked.obstacle],
                        blocked.symmetric)
        
        # Create new characters
        for char_data in world_expansion.new_characters:
            char_inventory = [items_dict[item_name] for item_name in char_data.inventory if item_name in items_dict]
            char_location = locations_dict.get(char_data.location)
            
            if not char_location:
                # Default to player location if specified location doesn't exist
                char_location = world.player.location
                
            character = Character(
                name=char_data.name,
                descriptions=char_data.descriptions,
                location=char_location,
                inventory=char_inventory)
            world.add_character(character)
            
    except Exception as e:
        print(f"Error expanding world from LLM response: {e}")
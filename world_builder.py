"""Module to generate and expand the world dynamically using LLMs."""

# ----------------------------------------- #
# Imports and Configs                       #
# ----------------------------------------- #
import json
from typing import Dict

from world import World, Location, Item, Character
from structured_data_models import GeneratedWorld, WorldExpansion

# ----------------------------------------- #
# Main functions for creating the world     #
# ----------------------------------------- #
def create_world_from_llm_response(response: str) -> World:
    """Parse structured LLM response and create a World object."""
    try:
        # Parse the JSON response
        world_data = json.loads(response)
        generated_world = GeneratedWorld.model_validate(world_data)

        # Create items first so they can be referenced
        items_dict: Dict[str, Item] = {}
        for item_data in generated_world.items:
            item = Item(
                name=item_data.name,
                descriptions=item_data.descriptions,
                gettable=item_data.gettable)
            items_dict[item_data.name] = Item
        
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
                if blocked['location'] in locations_dict and blocked['obstacle'] in items_dict:
                    locations_dict[loc_data.name].block_passage(
                        locations_dict[blocked['location']],
                        items_dict[blocked['obstacle']],
                        blocked.get('symmetric', True))
        
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

        return world
    except Exception as e:
        print(f"Error creating world from LLM response: {e}")
        # Fallback to the default world
        from example_worlds import get_world_1
        return get_world_1()
    
def expand_world_from_llm_response(world: World, response: str) -> None:
    """Parse structured LLM response and expand an existing World object."""
    try:
        # Parse the JSON response
        expansion_data = json.loads(response)
        world_expansion = WorldExpansion.model_validate(expansion_data)

        # Create new items
        items_dict: Dict[str, Item] = []
        for item_data in world_expansion.new_items:
            item = Item(
                name=item_data.name,
                descriptions=item_data.descriptions,
                gettable=item_data.gettable)
            items_dict[item_data.name] = item
            world.add_item(item)
        
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
                if blocked["location"] in locations_dict and blocked["obstacle"] in items_dict:
                    locations_dict[loc_data.name].block_passage(
                        locations_dict[blocked["location"]], 
                        items_dict[blocked["obstacle"]],
                        blocked.get("symmetric", True))
        
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
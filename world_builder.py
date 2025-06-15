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
            
            # DEBUG: Print puzzle information
            print(f"🧩 Puzzle creado: {puzzle.name}")
            print(f"   Descripción: {puzzle.descriptions}")
            print(f"   Problema: {puzzle.problem}")
            print(f"   Respuesta: {puzzle.answer}")
            print()
        
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
        for blocked in loc_data.blocked_passages:
            if blocked.location in locations_dict:
                location = locations_dict[loc_data.name]
                blocked_location = locations_dict[blocked.location]
                
                # Check if the locations are connected before blocking
                if blocked_location not in location.connecting_locations:
                    # Connect the locations first
                    location.connecting_locations.append(blocked_location)
                    if blocked.symmetric:
                        blocked_location.connecting_locations.append(location)
                
                # DEBUG: Print blocking information
                print(f"🚪 Intentando bloquear pasaje: {location.name} -> {blocked_location.name}")
                print(f"   Obstáculo: {blocked.obstacle}")
                
                # Now block the passage - check if obstacle is a puzzle or an item
                blocking_element = None
                if blocked.obstacle in puzzles_dict:
                    blocking_element = puzzles_dict[blocked.obstacle]
                    print(f"   ✅ Puzzle encontrado: {blocking_element.name}")
                elif blocked.obstacle in items_dict:
                    blocking_element = items_dict[blocked.obstacle]
                    print(f"   ✅ Item encontrado: {blocking_element.name}")
                else:
                    print(f"   ❌ Obstáculo no encontrado en puzzles ni items")
                    # Try to find by partial name match
                    for puzzle_name, puzzle in puzzles_dict.items():
                        if blocked.obstacle.lower() in puzzle_name.lower() or puzzle_name.lower() in blocked.obstacle.lower():
                            blocking_element = puzzle
                            print(f"   ✅ Puzzle encontrado por coincidencia parcial: {puzzle_name}")
                            break
                    
                    if not blocking_element:
                        for item_name, item in items_dict.items():
                            if blocked.obstacle.lower() in item_name.lower() or item_name.lower() in blocked.obstacle.lower():
                                blocking_element = item
                                print(f"   ✅ Item encontrado por coincidencia parcial: {item_name}")
                                break
                
                if blocking_element:
                    location.block_passage(blocked_location, blocking_element, blocked.symmetric)
                    print(f"   ✅ Pasaje bloqueado exitosamente")
                else:
                    print(f"   ❌ No se pudo bloquear el pasaje - obstáculo no válido")
        
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

def inspect_generated_world(world: World, language: str = 'es') -> str:
    """Generate a concise inspection report of the generated world."""
    
    if language == 'es':
        report = "🌍 **INSPECCIÓN DEL MUNDO GENERADO** 🌍\n\n"
        
        # Basic world stats
        puzzles_count = 0
        if hasattr(world, 'puzzles'):
            if isinstance(world.puzzles, dict):
                puzzles_count = len(world.puzzles)
            elif isinstance(world.puzzles, list):
                puzzles_count = len(world.puzzles)
        
        report += f"📊 **Estadísticas básicas:**\n"
        report += f"• Ubicaciones: {len(world.locations)}\n"
        report += f"• Objetos: {len(world.items)}\n"
        report += f"• Personajes (NPCs): {len([c for c in world.characters.values() if c != world.player])}\n"
        report += f"• Puzzles: {puzzles_count}\n\n"
        
        # Locations with connections
        report += f"🏠 **Ubicaciones y conexiones:**\n"
        for loc_name, location in world.locations.items():
            connections = [conn.name for conn in location.connecting_locations]
            report += f"• {loc_name} → conecta con: {', '.join(connections) if connections else 'ninguna'}\n"
        report += "\n"
        
        # Blocked passages
        blocked_count = 0
        report += f"🚪 **Pasajes bloqueados:**\n"
        for location in world.locations.values():
            if hasattr(location, 'blocked_locations') and location.blocked_locations:
                for blocked_loc, blocking_element in location.blocked_locations.items():
                    blocked_count += 1
                    blocking_type = "🧩" if hasattr(blocking_element[1], 'problem') else "🔑"
                    report += f"• {location.name} → {blocked_loc} ({blocking_type} {blocking_element[1].name})\n"
        
        if blocked_count == 0:
            report += "• No hay pasajes bloqueados\n"
        report += "\n"
        
        # Puzzles summary
        if hasattr(world, 'puzzles') and world.puzzles:
            report += f"🧩 **Puzzles disponibles:**\n"
            
            # Handle both dict and list formats
            if isinstance(world.puzzles, dict):
                for puzzle_name, puzzle in world.puzzles.items():
                    problem_preview = puzzle.problem[:50] + "..." if len(puzzle.problem) > 50 else puzzle.problem
                    report += f"• {puzzle_name}: {problem_preview}\n"
            elif isinstance(world.puzzles, list):
                for puzzle in world.puzzles:
                    problem_preview = puzzle.problem[:50] + "..." if len(puzzle.problem) > 50 else puzzle.problem
                    report += f"• {puzzle.name}: {problem_preview}\n"
        else:
            report += f"🧩 **Puzzles:** No hay puzzles en el mundo\n"
        report += "\n"
        
        # Objective
        if hasattr(world, 'objective') and world.objective:
            obj_type = type(world.objective[1]).__name__
            obj_name = world.objective[1].name
            report += f"🎯 **Objetivo:** {world.objective[0].name} debe interactuar con {obj_name} ({obj_type})\n"
        else:
            report += f"🎯 **Objetivo:** No definido\n"
        
    else:
        report = "🌍 **GENERATED WORLD INSPECTION** 🌍\n\n"
        
        # Basic world stats
        puzzles_count = 0
        if hasattr(world, 'puzzles'):
            if isinstance(world.puzzles, dict):
                puzzles_count = len(world.puzzles)
            elif isinstance(world.puzzles, list):
                puzzles_count = len(world.puzzles)
        
        report += f"📊 **Basic stats:**\n"
        report += f"• Locations: {len(world.locations)}\n"
        report += f"• Items: {len(world.items)}\n"
        report += f"• Characters (NPCs): {len([c for c in world.characters.values() if c != world.player])}\n"
        report += f"• Puzzles: {puzzles_count}\n\n"
        
        # Locations with connections
        report += f"🏠 **Locations and connections:**\n"
        for loc_name, location in world.locations.items():
            connections = [conn.name for conn in location.connecting_locations]
            report += f"• {loc_name} → connects to: {', '.join(connections) if connections else 'none'}\n"
        report += "\n"
        
        # Blocked passages
        blocked_count = 0
        report += f"🚪 **Blocked passages:**\n"
        for location in world.locations.values():
            if hasattr(location, 'blocked_locations') and location.blocked_locations:
                for blocked_loc, blocking_element in location.blocked_locations.items():
                    blocked_count += 1
                    blocking_type = "🧩" if hasattr(blocking_element[1], 'problem') else "🔑"
                    report += f"• {location.name} → {blocked_loc} ({blocking_type} {blocking_element[1].name})\n"
        
        if blocked_count == 0:
            report += "• No blocked passages\n"
        report += "\n"
        
        # Puzzles summary
        if hasattr(world, 'puzzles') and world.puzzles:
            report += f"🧩 **Available puzzles:**\n"
            
            # Handle both dict and list formats
            if isinstance(world.puzzles, dict):
                for puzzle_name, puzzle in world.puzzles.items():
                    problem_preview = puzzle.problem[:50] + "..." if len(puzzle.problem) > 50 else puzzle.problem
                    report += f"• {puzzle_name}: {problem_preview}\n"
            elif isinstance(world.puzzles, list):
                for puzzle in world.puzzles:
                    problem_preview = puzzle.problem[:50] + "..." if len(puzzle.problem) > 50 else puzzle.problem
                    report += f"• {puzzle.name}: {problem_preview}\n"
        else:
            report += f"🧩 **Puzzles:** No puzzles in the world\n"
        report += "\n"
        
        # Objective
        if hasattr(world, 'objective') and world.objective:
            obj_type = type(world.objective[1]).__name__
            obj_name = world.objective[1].name
            report += f"🎯 **Objective:** {world.objective[0].name} must interact with {obj_name} ({obj_type})\n"
        else:
            report += f"🎯 **Objective:** Not defined\n"
    
    return report

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
                if blocked.location in locations_dict:
                    location = locations_dict[loc_data.name]
                    blocked_location = locations_dict[blocked.location]
                    
                    # Check if the locations are connected before blocking
                    if blocked_location not in location.connecting_locations:
                        # Connect the locations first
                        location.connecting_locations.append(blocked_location)
                        if blocked.symmetric:
                            blocked_location.connecting_locations.append(location)
                    
                    # Now block the passage - check if obstacle is a puzzle or an item
                    if blocked.obstacle in puzzles_dict:
                        location.block_passage(
                            blocked_location, 
                            puzzles_dict[blocked.obstacle],
                            blocked.symmetric)
                    elif blocked.obstacle in items_dict:
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
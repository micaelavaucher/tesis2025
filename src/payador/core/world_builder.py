"""Module to generate and expand the world dynamically using LLMs."""

# ----------------------------------------- #
# Imports and Configs                       #
# ----------------------------------------- #
import json
from typing import Dict

from .world import World, Location, Item, Character, Puzzle
from ..llm.structured_data_models import GeneratedWorld, WorldExpansion, RequirementType

# ----------------------------------------- #
# Main functions for creating the world     #
# ----------------------------------------- #
def create_world_from_llm_response(world_data) -> World:
    """Parse structured LLM response and create a World object."""
    try:
        # Handle GeneratedWorld objects, dict and string inputs
        if isinstance(world_data, GeneratedWorld):
            generated_world = world_data
        elif isinstance(world_data, dict):
            data = world_data
            generated_world = GeneratedWorld.model_validate(data)
        else:
            data = json.loads(world_data)
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
                answer=puzzle_data.answer,
                puzzle_type=getattr(puzzle_data, 'puzzle_type', 'riddle'),
                proposed_by_character=getattr(puzzle_data, 'proposed_by_character', None),
                proposed_by_item=getattr(puzzle_data, 'proposed_by_item', None),
                rewards=getattr(puzzle_data, 'rewards', []),
                relevance_to_objective=getattr(puzzle_data, 'relevance_to_objective', None)
            )
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

        # Connect locations (normal connections first)
        for loc_data in generated_world.locations:
            if loc_data.name in locations_dict:
                location = locations_dict[loc_data.name]
                for connected_loc_name in loc_data.connecting_locations:
                    if connected_loc_name in locations_dict:
                        connected_location = locations_dict[connected_loc_name]
                        if connected_location not in location.connecting_locations:
                            location.connecting_locations.append(connected_location)
                        # Make bidirectional connection
                        if location not in connected_location.connecting_locations:
                            connected_location.connecting_locations.append(location)

        # Handle blocked passages
        for loc_data in generated_world.locations:
            if loc_data.name in locations_dict:
                location = locations_dict[loc_data.name]
                
                for blocked in loc_data.blocked_passages:
                    if blocked.location in locations_dict:
                        blocked_location = locations_dict[blocked.location]
                        
                        # Ensure locations are connected before blocking
                        if blocked_location not in location.connecting_locations:
                            location.connecting_locations.append(blocked_location)
                            blocked_location.connecting_locations.append(location)
                                                
                        # Get blocking element based on requirement type
                        blocking_element = None
                        requirement = blocked.required_to_unblock
                        
                        req_type = requirement.requirement_type.value if hasattr(requirement.requirement_type, 'value') else str(requirement.requirement_type)
                        
                        if req_type in ["PUZZLE", "puzzle"]:
                            puzzle_name = getattr(requirement, 'puzzle_name', None)
                            if puzzle_name and puzzle_name in puzzles_dict:
                                blocking_element = puzzles_dict[puzzle_name]
                                
                        elif req_type in ["ITEM", "item"]:
                            item_name = getattr(requirement, 'item_name', None)
                            if item_name and item_name in items_dict:
                                blocking_element = items_dict[item_name]
                        
                        if blocking_element:
                            location.block_passage(blocked_location, blocking_element)

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

        print(generated_world.objective)

        # Set the objective if it exists
        if generated_world.objective:
            world.objective = set_objective_from_generated(
                generated_world.objective, 
                items_dict, 
                locations_dict, 
                characters_list, 
                player)

        return world
        
    except Exception as e:
        print(f"Error creating world from LLM response: {e}")
        import traceback
        traceback.print_exc()
        # Fallback to the default world
        import examples.example_worlds as example_worlds
        return example_worlds.get_world("1")

def set_objective_from_generated(objective_data, items_dict, locations_dict, characters_list, player):
    """Create an objective tuple from generated data."""
    try:
        # Handle enum values properly
        obj_type = objective_data.type.value if hasattr(objective_data.type, 'value') else str(objective_data.type)
        components = objective_data.components
                
        # Handle different objective types with new component system
        if obj_type in ["GET_ITEM", "get_item"]:
            # Find the item component
            for component in components:
                component_type = component.component_type.value if hasattr(component.component_type, 'value') else str(component.component_type)
                if component_type in ["ITEM", "item"]:
                    if component.name in items_dict:
                        return (player, items_dict[component.name])
        
        elif obj_type in ["REACH_LOCATION", "reach_location"]:
            # Find the location component
            for component in components:
                component_type = component.component_type.value if hasattr(component.component_type, 'value') else str(component.component_type)
                if component_type in ["LOCATION", "location"]:
                    if component.name in locations_dict:
                        return (player, locations_dict[component.name])
        
        elif obj_type in ["FIND_CHARACTER", "find_character"]:
            # Find the character component
            for component in components:
                component_type = component.component_type.value if hasattr(component.component_type, 'value') else str(component.component_type)
                if component_type in ["CHARACTER", "character"]:
                    character = next((c for c in characters_list if c.name == component.name), None)
                    if character:
                        return (player, character)
        
        elif obj_type in ["DELIVER_AN_ITEM", "deliver_an_item"]:
            # Need both item and location/character components
            item_component = None
            target_component = None
            
            for component in components:
                component_type = component.component_type.value if hasattr(component.component_type, 'value') else str(component.component_type)
                if component_type in ["ITEM", "item"]:
                    item_component = component
                elif component_type in ["LOCATION", "location", "CHARACTER", "character"]:
                    target_component = component
            
            if item_component and target_component:
                if item_component.name in items_dict:
                    target_type = target_component.component_type.value if hasattr(target_component.component_type, 'value') else str(target_component.component_type)
                    if target_type in ["LOCATION", "location"] and target_component.name in locations_dict:
                        return (items_dict[item_component.name], locations_dict[target_component.name])
                    elif target_type in ["CHARACTER", "character"]:
                        character = next((c for c in characters_list if c.name == target_component.name), None)
                        if character:
                            return (items_dict[item_component.name], character)
        
        elif obj_type in ["SOLVE_MYSTERY", "solve_mystery"]:
            # Create a proper MysteryObjective with clue validation
            from .world import MysteryObjective, MysteryClue
            
            # Validate and create clues
            valid_clues = []
            if hasattr(objective_data, 'mystery_clues') and objective_data.mystery_clues:
                for clue_data in objective_data.mystery_clues:
                    # Validate that the associated item exists
                    if clue_data.associated_item in items_dict:
                        # Validate item location if specified
                        if clue_data.item_location:
                            # Check if location exists
                            if clue_data.item_location in locations_dict:
                                # Check if item is actually in that location
                                location = locations_dict[clue_data.item_location]
                                item_in_location = clue_data.associated_item in [item.name for item in location.items]
                                if item_in_location:
                                    clue = MysteryClue(
                                        name=clue_data.name,
                                        description=clue_data.description,
                                        associated_item=clue_data.associated_item,
                                        relevance_to_mystery=clue_data.relevance_to_mystery,
                                        discovered=clue_data.discovered,
                                        item_location=clue_data.item_location
                                    )
                                    valid_clues.append(clue)
                                else:
                                    print(f"   ⚠️ Clue '{clue_data.name}' skipped: item '{clue_data.associated_item}' not found in location '{clue_data.item_location}'")
                            else:
                                print(f"   ⚠️ Clue '{clue_data.name}' skipped: location '{clue_data.item_location}' does not exist")
                        else:
                            # No specific location validation needed
                            clue = MysteryClue(
                                name=clue_data.name,
                                description=clue_data.description,
                                associated_item=clue_data.associated_item,
                                relevance_to_mystery=clue_data.relevance_to_mystery,
                                discovered=clue_data.discovered
                            )
                            valid_clues.append(clue)
                    else:
                        print(f"   ⚠️ Clue '{clue_data.name}' skipped: associated item '{clue_data.associated_item}' does not exist")
            
            # Only create mystery objective if there are valid clues
            if valid_clues:
                mystery_solution = getattr(objective_data, 'mystery_solution', 'Mystery solution not specified')
                mystery_objective = MysteryObjective(
                    name=f"Mystery: {objective_data.description}",
                    description=objective_data.description,
                    clues=valid_clues,
                    mystery_solution=mystery_solution
                )
                print(f"   ✅ Created mystery objective with {len(valid_clues)} valid clues")
                return (player, mystery_objective)
            else:
                print(f"   ❌ No valid clues for mystery objective - skipping mystery creation")
                return None
        
        # Fallback: try to infer from description
        description = objective_data.description.lower()
        
        # Check if it's about finding an item
        for item_name in items_dict:
            if item_name.lower() in description:
                return (player, items_dict[item_name])
        
        # Check if it's about reaching a location  
        for location_name in locations_dict:
            if location_name.lower() in description:
                return (player, locations_dict[location_name])
        
        print(f"   ❌ No se pudo establecer objetivo")
        return None
        
    except Exception as e:
        print(f"Error setting objective: {e}")
        import traceback
        traceback.print_exc()
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
        
        return report
        
    else:
        # English version (similar structure)
        report = "🌍 **GENERATED WORLD INSPECTION** 🌍\n\n"
        
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
        
        report += f"🏠 **Locations and connections:**\n"
        for loc_name, location in world.locations.items():
            connections = [conn.name for conn in location.connecting_locations]
            report += f"• {loc_name} → connects to: {', '.join(connections) if connections else 'none'}\n"
        report += "\n"
        
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
        
        if hasattr(world, 'puzzles') and world.puzzles:
            report += f"🧩 **Available puzzles:**\n"
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
                answer=puzzle_data.answer,
                puzzle_type=getattr(puzzle_data, 'puzzle_type', 'riddle'),
                proposed_by_character=getattr(puzzle_data, 'proposed_by_character', None),
                proposed_by_item=getattr(puzzle_data, 'proposed_by_item', None),
                rewards=getattr(puzzle_data, 'rewards', []),
                relevance_to_objective=getattr(puzzle_data, 'relevance_to_objective', None)
            )
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
            if loc_data.name in locations_dict:
                location = locations_dict[loc_data.name]
                for connected_loc_name in loc_data.connecting_locations:
                    if connected_loc_name in locations_dict:
                        connected_location = locations_dict[connected_loc_name]
                        if connected_location not in location.connecting_locations:
                            location.connecting_locations.append(connected_location)
        
        # Connect to existing world based on connections_to_existing
        for connection_desc in world_expansion.connections_to_existing:
            # This would need more sophisticated parsing based on the description
            # For now, connect to player's current location
            for location in locations_dict.values():
                world.player.location.connecting_locations.append(location)
                location.connecting_locations.append(world.player.location)
                break  # Just connect the first new location
        
        # Handle blocked passages in new locations
        for loc_data in world_expansion.new_locations:
            if loc_data.name in locations_dict:
                location = locations_dict[loc_data.name]
                
                for blocked in loc_data.blocked_passages:
                    if blocked.location in locations_dict:
                        blocked_location = locations_dict[blocked.location]
                        
                        # Ensure connection before blocking
                        if blocked_location not in location.connecting_locations:
                            location.connecting_locations.append(blocked_location)
                            blocked_location.connecting_locations.append(location)
                        
                        # Get blocking element based on requirement
                        blocking_element = None
                        requirement = blocked.required_to_unblock
                        
                        req_type = requirement.requirement_type.value if hasattr(requirement.requirement_type, 'value') else str(requirement.requirement_type)
                        
                        if req_type in ["PUZZLE", "puzzle"]:
                            puzzle_name = getattr(requirement, 'puzzle_name', None)
                            if puzzle_name and puzzle_name in puzzles_dict:
                                blocking_element = puzzles_dict[puzzle_name]
                        elif req_type in ["ITEM", "item"]:
                            item_name = getattr(requirement, 'item_name', None)
                            if item_name and item_name in items_dict:
                                blocking_element = items_dict[item_name]
                        
                        if blocking_element:
                            location.block_passage(blocked_location, blocking_element)
        
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
        import traceback
        traceback.print_exc()
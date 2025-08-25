"""Game logic and world management for PAYADOR.

This module contains the core game loop, world state management,
and game-related utility functions with intelligent memory integration.
"""

import re
import json
import os
import jsonpickle
import time
from ..llm.prompts import prompt_narrate_current_scene, prompt_world_update_structured, prompt_describe_objective
from .world_builder import inspect_generated_world
from ..config import PATH_GAMELOGS
from ..llm.structured_data_models import WorldUpdate
from ..llm.memory_system import create_memory_system

def generate_starting_narration(world, language, narrative_model):
    """Generate the starting narration for a world."""
    system_msg_current_scene, user_msg_current_scene = prompt_narrate_current_scene(
        world.render_world(language=language),
        previous_narrations=world.player.visited_locations[world.player.location.name],
        language=language, 
        starting_scene=True
    )
    starting_narration = narrative_model.prompt_model(system_msg=system_msg_current_scene, user_msg=user_msg_current_scene)
    world.player.visited_locations[world.player.location.name] += [starting_narration]
    
    # Add objective description
    if hasattr(world, 'objective') and world.objective:
        system_msg_objective, user_msg_objective = prompt_describe_objective(world.objective, language=language)
        narrated_objective = narrative_model.prompt_model(system_msg=system_msg_objective, user_msg=user_msg_objective)
        import re
        try:
            objective_texts = re.findall(r'#(.*?)#', narrated_objective, re.DOTALL)
            if objective_texts:
                objective_text = " ".join([t.strip() for t in objective_texts])
                # Fallback if objective is too short or incomplete
                if len(objective_text.split()) < 8 or not objective_text.strip().endswith(('.', '!', '?')):
                    print("⚠️ Objective seems incomplete, using full LLM response instead.")
                    if not narrated_objective.strip().endswith(('.', '!', '?')):
                        narrated_objective += '.'
                    starting_narration += f"\n\n🎯 {narrated_objective}"
                else:
                    starting_narration += f"\n\n🎯 {objective_text}"
            else:
                raise IndexError
        except (IndexError, TypeError):
            print("⚠️ No se pudo extraer el objetivo narrado con el formato #...#, usando la respuesta completa.")
            if not narrated_objective.strip().endswith(('.', '!', '?')):
                narrated_objective += '.'
            starting_narration += f"\n\n🎯 {narrated_objective}"
    else:
        print("ℹ️ No se encontró un objetivo principal en el mundo generado/cargado.")
    
    # Add formatted world state to starting narration
    world_state_formatted = world.format_world_state_for_chat(language=language)
    starting_narration += f"\n\n---\n{world_state_formatted}"
    
    return starting_narration

def create_world_state_summary(world, player_action, language='en'):
    """Create a rich contextual summary of the world state for memory embedding."""
    try:
        player_location = world.player.location.name
        
        location_description = ""
        if hasattr(world.player.location, 'descriptions') and world.player.location.descriptions:
            # Take the first description or join multiple descriptions
            if isinstance(world.player.location.descriptions, list):
                location_description = " ".join(world.player.location.descriptions)
            else:
                location_description = str(world.player.location.descriptions)
        elif hasattr(world.player.location, 'description'):
            location_description = world.player.location.description
        elif hasattr(world.player.location, 'desc'):
            location_description = world.player.location.desc
        
        # Safely get visible items in current location
        visible_items = []
        if hasattr(world.player.location, 'items') and world.player.location.items:
            visible_items = [item.name for item in world.player.location.items]
        
        # Get characters in current location (they are stored in world.characters, not location.characters)
        present_characters = []
        if hasattr(world, 'characters') and world.characters:
            for character in world.characters.values():
                if hasattr(character, 'location') and character.location is world.player.location:
                    # Don't include the player character in the list
                    if character is not world.player:
                        present_characters.append(character.name)
        
        # Safely get player inventory
        player_items = []
        if hasattr(world.player, 'inventory') and world.player.inventory:
            player_items = [item.name for item in world.player.inventory]
        
        # Extract key object from player action if possible
        key_object = ""
        action_words = player_action.lower().split()
        if hasattr(world, 'items') and world.items:
            for item_name, item in world.items.items():
                if any(word in item_name.lower() for word in action_words):
                    key_object = item_name
                    break
        
        # Build rich contextual summary
        if language == 'es':
            summary = f"Ubicación: {player_location}. "
            
            if location_description:
                summary += f"Descripción: {location_description[:100]}{'...' if len(location_description) > 100 else ''}. "
            
            if visible_items:
                summary += f"Objetos visibles: {', '.join(visible_items)}. "
            
            if present_characters:
                summary += f"Personajes presentes: {', '.join(present_characters)}. "
                
            if player_items:
                summary += f"Inventario del jugador: {', '.join(player_items)}. "
                
            if key_object:
                summary += f"Objeto clave de la acción: {key_object}. "
                
            summary += f"Acción realizada: {player_action}"
            
        else:
            summary = f"Location: {player_location}. "
            
            if location_description:
                summary += f"Description: {location_description[:100]}{'...' if len(location_description) > 100 else ''}. "
            
            if visible_items:
                summary += f"Visible items: {', '.join(visible_items)}. "
            
            if present_characters:
                summary += f"Present characters: {', '.join(present_characters)}. "
                
            if player_items:
                summary += f"Player inventory: {', '.join(player_items)}. "
                
            if key_object:
                summary += f"Key object in action: {key_object}. "
                
            summary += f"Action performed: {player_action}"
        
        return summary
        
    except Exception as e:
        print(f"⚠️ Error creating world state summary: {e}")
        # Fallback to basic summary
        if language == 'es':
            return f"Ubicación: {world.player.location.name}. Acción: {player_action}"
        else:
            return f"Location: {world.player.location.name}. Action: {player_action}"

def create_game_log_entry(world, language, log_filename, narrative_model_name, reasoning_model_name, world_id=None):
    """Create initial game log dictionary."""
    game_log_dictionary = {}
    game_log_dictionary["nickname"] = "anonymous"
    game_log_dictionary["language"] = language
    # Use provided world_id or generate new one
    game_log_dictionary["world_id"] = world_id or f"generated_{int(time.time())}"
    game_log_dictionary["narrative_model_name"] = narrative_model_name
    game_log_dictionary["reasoning_model_name"] = reasoning_model_name
    
    return game_log_dictionary

def initialize_game_state(world, language, log_filename, narrative_model_name, reasoning_model_name, starting_narration):
    """Initialize game state variables and create initial log entry."""
    last_player_position = world.player.location
    number_of_turns = 0
    
    game_log_dictionary = create_game_log_entry(world, language, log_filename, narrative_model_name, reasoning_model_name)
    game_log_dictionary[0] = {
        "date": time.ctime(time.time()),
        "initial_symbolic_world_state": jsonpickle.encode(world, unpicklable=True),
        "initial_rendered_world_state": world.render_world(language=language),
        "starting_narration": starting_narration
    }

    with open(os.path.join(PATH_GAMELOGS, log_filename), 'w', encoding='utf-8') as f:
        json.dump(game_log_dictionary, f, ensure_ascii=False, indent=4)
    
    return last_player_position, number_of_turns, game_log_dictionary

def generate_world_overview(world, language):
    """Generate a comprehensive overview of all locations, connections, items, and NPCs."""
    overview = ""
    
    if language == 'es':
        header = "🌎 Resumen del Mundo 🌍\n\n"
    else:
        header = "🌎 World Overview 🌍\n\n"
    
    overview += header
    
    # Get all locations
    locations = {}
    if hasattr(world, 'locations') and world.locations:
        locations = world.locations
    else:
        # Fallback: collect locations from player and character positions
        locations = {world.player.location.name: world.player.location}
        if hasattr(world, 'characters') and world.characters:
            for char in world.characters.values():
                if hasattr(char, 'location') and char.location:
                    locations[char.location.name] = char.location
    
    # Process each location
    for location_name, location in locations.items():
        overview += f"{location_name}:\n"
        
        # Connections
        connections = []
        if hasattr(location, 'connecting_locations') and location.connecting_locations:
            connections = [loc.name for loc in location.connecting_locations]
        
        if connections:
            if language == 'es':
                overview += f" - Conecta con:\n"
            else:
                overview += f" - Connects to:\n"
            for conn in connections:
                overview += f"   - {conn}\n"
        else:
            if language == 'es':
                overview += f" - Conecta con: Ninguna\n"
            else:
                overview += f" - Connects to: None\n"
        
        # Items in this location
        items = []
        if hasattr(location, 'items') and location.items:
            items = [item.name for item in location.items]
        
        if items:
            if language == 'es':
                overview += f" - Objetos:\n"
            else:
                overview += f" - Items:\n"
            for item in items:
                overview += f"   - {item}\n"
        else:
            if language == 'es':
                overview += f" - Objetos: Ninguno\n"
            else:
                overview += f" - Items: None\n"
        
        # NPCs in this location
        npcs = []
        if hasattr(world, 'characters') and world.characters:
            for char in world.characters.values():
                if (hasattr(char, 'location') and char.location is location and 
                    char is not world.player):  # Don't include the player
                    npcs.append(char.name)
        
        if npcs:
            if language == 'es':
                overview += f" - PNJs:\n"
            else:
                overview += f" - NPCs:\n"
            for npc in npcs:
                overview += f"   - {npc}\n"
        else:
            if language == 'es':
                overview += f" - PNJs: Ninguno\n"
            else:
                overview += f" - NPCs: None\n"
        
        overview += "\n"
    
    return overview

def get_objective_info(world, language):
    """Get formatted objective information for the player."""
    if not hasattr(world, 'objective') or not world.objective:
        if language == 'es':
            return "🎯 No se ha definido un objetivo específico para este mundo."
        else:
            return "🎯 No specific objective has been defined for this world."
    
    # Get the raw objective description
    raw_objective = ""
    
    # Handle different objective formats
    if hasattr(world.objective, 'description'):
        # New structured objective format
        raw_objective = world.objective.description
    elif isinstance(world.objective, tuple) and len(world.objective) >= 2:
        # Legacy tuple format
        obj_component = world.objective[1]
        if hasattr(obj_component, 'description'):
            raw_objective = obj_component.description
        else:
            # Fallback to basic description
            if language == 'es':
                raw_objective = f"Completar la tarea relacionada con {world.objective[0].__class__.__name__.lower()}."
            else:
                raw_objective = f"Complete the task related to {world.objective[0].__class__.__name__.lower()}."
    elif isinstance(world.objective, str):
        # Simple string objective
        raw_objective = world.objective
    else:
        # Fallback for unknown formats
        if language == 'es':
            raw_objective = "Objetivo no especificado claramente."
        else:
            raw_objective = "Objective not clearly specified."
    
    return raw_objective

def handle_debug_command(message, world, language):
    """Handle debug inspection commands."""
    message_lower = message.lower()
    
    if message_lower in ["inspect", "inspeccionar", "inspect world", "inspeccionar mundo"]:
        debug_info = inspect_generated_world(world, language)
        return debug_info.replace("<", r"\<").replace(">", r"\>")
    
    elif message_lower in ["see world", "ver mundo", "world overview", "resumen mundo"]:
        world_overview = generate_world_overview(world, language)
        return world_overview.replace("<", r"\<").replace(">", r"\>")
    
    elif message_lower in ["objective", "objetivo", "what is my objective", "what is my objective?", 
                           "cuál es mi objetivo", "cuál es mi objetivo?", "cual es mi objetivo", 
                           "cual es mi objetivo?", "my objective", "mi objetivo", "goal", "meta"]:
        objective_info = get_objective_info(world, language)
        return objective_info.replace("<", r"\<").replace(">", r"\>")
    
    return None

def process_player_input_structured(world, message, language, reasoning_model,
                                    number_of_turns, game_log_dictionary, memory_system=None):
    """Process player input using structured data models for more reliable parsing."""
    # Log input
    game_log_dictionary[number_of_turns]["date"] = time.ctime(time.time())
    game_log_dictionary[number_of_turns]["previous_symbolic_world_state"] = jsonpickle.encode(world, unpicklable=False)
    game_log_dictionary[number_of_turns]["previous_rendered_world_state"] = world.render_world(language=language)
    game_log_dictionary[number_of_turns]["user_input"] = message

    # Retrieve relevant memories if memory system is available
    relevant_memories_text = ""
    if memory_system:
        try:
            relevant_memories = memory_system.retrieve_relevant_memories(message, top_k=3)
            relevant_memories_text = memory_system.format_memories_for_prompt(relevant_memories, language)
        except Exception as e:
            print(f"⚠️ Error retrieving memories: {e}")
            relevant_memories_text = ""

    # Get structured world changes with memory augmentation
    system_msg_update, user_msg_update, expected_model = prompt_world_update_structured(
        world.render_world(language=language), message, language=language, relevant_memories=relevant_memories_text
    )
    
    try:
        # Try to get structured response
        full_prompt = system_msg_update + "\n\n" + user_msg_update
        # Convert Pydantic model to JSON schema for Gemini
        response_schema = expected_model.model_json_schema()
        
        response_json = reasoning_model.prompt_model_structured(
            prompt=full_prompt,
            response_schema=response_schema
        )
        
        if isinstance(response_json, dict):
            # Direct dict response
            world_update = WorldUpdate(**response_json)
        elif isinstance(response_json, str):
            # Parse JSON string if needed
            import json
            response_data = json.loads(response_json)
            world_update = WorldUpdate(**response_data)
        else:
            # Model instance response
            world_update = response_json
            
        # Show predicted outcomes
        print("🛠️ Predicted outcomes of the player input 🛠️")
        print(f"> Player input: {message}")
        print(f"{world_update.narration}\n")
        
        game_log_dictionary[number_of_turns]["predicted_outcomes"] = world_update.narration
        game_log_dictionary[number_of_turns]["structured_update"] = world_update.model_dump()
        
        # Update world using structured data
        world.update_from_structured(world_update)
        
        # Ingest new memory after successful processing
        if memory_system:
            try:
                # Create rich world state summary for better embedding
                world_state_summary = create_world_state_summary(world, message, language)
                
                memory_system.ingest_memory(
                    turn_number=number_of_turns,
                    player_action=message,
                    result_narration=world_update.narration,
                    world_state_summary=world_state_summary
                )
            except Exception as e:
                print(f"⚠️ Error ingesting memory: {e}")
        
    except Exception as e:
        print(f"⚠️ Structured processing failed: {e}")
        print("🔄 Falling back to legacy text processing...")
        
        # Fallback to legacy processing
        response_update = reasoning_model.prompt_model(system_msg=system_msg_update, user_msg=user_msg_update)
        
        print("🛠️ Predicted outcomes of the player input 🛠️")
        print(f"> Player input: {message}")
        try:
            predicted_outcomes = re.sub(r'#([^#]*?)#', '', response_update)
            print(f"{predicted_outcomes}\n")
            game_log_dictionary[number_of_turns]["predicted_outcomes"] = predicted_outcomes
        except Exception as e:
            print(f"Error: {e}")
        
        # Update world using legacy method
        world.update(response_update)
        game_log_dictionary[number_of_turns]["fallback_response"] = response_update
        
        # Try to ingest memory for fallback case too
        if memory_system:
            try:
                # Extract narration from fallback response
                narration_matches = re.findall(r'#([^#]*?)#', str(response_update))
                fallback_narration = narration_matches[0] if narration_matches else "Something happened in the world."
                
                # Create rich world state summary for better embedding
                world_state_summary = create_world_state_summary(world, message, language)
                
                memory_system.ingest_memory(
                    turn_number=number_of_turns,
                    player_action=message,
                    result_narration=fallback_narration,
                    world_state_summary=world_state_summary
                )
            except Exception as e:
                print(f"⚠️ Error ingesting fallback memory: {e}")

    game_log_dictionary[number_of_turns]["updated_symbolic_world_state"] = jsonpickle.encode(world, unpicklable=True)
    game_log_dictionary[number_of_turns]["updated_rendered_world_state"] = world.render_world(language=language)

    return world_update.narration if 'world_update' in locals() else (response_update if 'response_update' in locals() else "")

def generate_narration(world, last_player_position, response_update, language, narrative_model):
    """Generate appropriate narration based on player location and actions."""
    answer = ""
    
    if last_player_position is not world.player.location:
        # Narrate new scene
        system_msg_new_scene, user_msg_new_scene = prompt_narrate_current_scene(
            world.render_world(language=language),
            previous_narrations=world.player.visited_locations[world.player.location.name],
            language=language
        )
        new_scene_narration = narrative_model.prompt_model(system_msg=system_msg_new_scene, user_msg=user_msg_new_scene)
        world.player.visited_locations[world.player.location.name] += [new_scene_narration]
        answer += f"\n{new_scene_narration}\n\n"
        last_player_position = world.player.location
    else:
        # Narrate actions in current scene
        try:
            # Check if response_update is empty or None
            if not response_update or not response_update.strip():
                # Provide fallback narration
                if language == 'es':
                    answer += "Algo sucedió en el mundo.\n"
                else:
                    answer += "Something happened in the world.\n"
            # Check if response_update is already clean narration (from structured processing)
            elif isinstance(response_update, str) and not response_update.startswith(("- Moved object:", "- Blocked passages", "- Your location")):
                # This looks like clean narration, use it directly
                answer += f"{response_update}\n"
            else:
                # Try to extract narration from legacy format
                narration_matches = re.findall(r'#([^#]*?)#', str(response_update))
                if narration_matches:
                    answer += f"{narration_matches[0]}\n"
                else:
                    # No narration found in expected format, provide fallback
                    if language == 'es':
                        answer += "Algo sucedió en el mundo.\n"
                    else:
                        answer += "Something happened in the world.\n"
        except Exception as e:
            print(f"Error extracting narration: {e}")
            # Provide fallback narration
            if language == 'es':
                answer += "Algo sucedió en el mundo.\n"
            else:
                answer += "Something happened in the world.\n"

    return answer, last_player_position

def check_objective_completion(world, answer, language):
    """Check if objective is completed and add completion message."""
    if world.check_objective():
        if language == 'es':
            answer += "\n\n🎯¡Completaste el objetivo!"
        else:
            answer += "\n\n🎯You have completed your quest!"
    return answer

def save_game_log(game_log_dictionary, log_filename, number_of_turns, answer):
    """Save current game state to log file."""
    game_log_dictionary[number_of_turns]["narration"] = answer
    
    with open(os.path.join(PATH_GAMELOGS, log_filename), 'w', encoding='utf-8') as f:
        json.dump(game_log_dictionary, f, ensure_ascii=False, indent=4)

def create_game_loop(world, reasoning_model, narrative_model, language, log_filename, visited_locations, api_key=None, enable_rag=True):
    """Create the main game loop function with intelligent memory system."""
    last_player_position = world.player.location
    number_of_turns = 0
    
    # Generate a single persistent world_id for the entire session
    session_world_id = f"generated_{int(time.time())}"
    
    game_log_dictionary = create_game_log_entry(
        world, language, log_filename, 
        narrative_model.model_name if hasattr(narrative_model, 'model_name') else 'unknown', 
        reasoning_model.model_name if hasattr(reasoning_model, 'model_name') else 'unknown',
        world_id=session_world_id  # Use consistent world_id
    )

    # Initialize memory system with consistent world_id only if RAG is enabled
    memory_system = None
    if enable_rag:
        try:
            memory_system = create_memory_system(session_world_id, api_key)
            print(f"🧠 Intelligent memory system initialized for world {session_world_id}")
            
            # Load existing memories from previous logs if available
            if log_filename:
                memory_system.load_memories_from_logs(log_filename)
        except Exception as e:
            print(f"⚠️ Failed to initialize memory system: {e}")
            print("🔄 Continuing without memory enhancement...")
            memory_system = None
    else:
        print("🔇 RAG system disabled by configuration")

    def game_loop(message, history):
        nonlocal last_player_position, number_of_turns, game_log_dictionary

        # Handle debug commands
        debug_response = handle_debug_command(message, world, language)
        if debug_response:
            return debug_response

        number_of_turns += 1
        game_log_dictionary[number_of_turns] = {}

        # Track visited locations
        visited_locations.add(world.player.location.name)

        # Process input and update world with memory system
        response_update = process_player_input_structured(
            world, message, language, reasoning_model, 
            number_of_turns, game_log_dictionary, memory_system
        )

        # Generate narration
        answer, last_player_position = generate_narration(world, last_player_position, response_update, language, narrative_model)

        # Check objective completion
        answer = check_objective_completion(world, answer, language)

        # Append formatted world state to answer
        world_state_formatted = world.format_world_state_for_chat(language=language)
        answer += f"\n\n---\n{world_state_formatted}"

        # Print world state
        print(f"\n🌎 World state 🌍\n>Player input: {message}\n{world.render_world(language=language)}\n")

        # Save game log
        save_game_log(game_log_dictionary, log_filename, number_of_turns, answer)

        return answer.replace("<", r"\<").replace(">", r"\>")

    return game_loop

"""Game logic and world management for PAYADOR.

This module contains the core game loop, world state management,
and game-related utility functions with intelligent memory integration.
"""

import re
import json
import os
import jsonpickle
import time
from prompts import prompt_narrate_current_scene, prompt_world_update_structured
from world_builder import inspect_generated_world
from config import PATH_GAMELOGS
from structured_data_models import WorldUpdate
from memory_system import create_memory_system

def create_game_log_entry(world, language, log_filename, narrative_model_name, reasoning_model_name):
    """Create initial game log dictionary."""
    game_log_dictionary = {}
    game_log_dictionary["nickname"] = "anonymous"
    game_log_dictionary["language"] = language
    game_log_dictionary["world_id"] = f"generated_{int(time.time())}"
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

def handle_debug_command(message, world, language):
    """Handle debug inspection commands."""
    if message.lower() in ["inspect", "inspeccionar", "inspect world", "inspeccionar mundo"]:
        debug_info = inspect_generated_world(world, language)
        return debug_info.replace("<", r"\<").replace(">", r"\>")
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
                memory_system.ingest_memory(
                    turn_number=number_of_turns,
                    player_action=message,
                    result_narration=world_update.narration,
                    world_state_summary=""  # Could be enhanced with a summary if needed
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
                
                memory_system.ingest_memory(
                    turn_number=number_of_turns,
                    player_action=message,
                    result_narration=fallback_narration
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

def create_game_loop(world, reasoning_model, narrative_model, language, log_filename, visited_locations, api_key=None):
    """Create the main game loop function with intelligent memory system."""
    last_player_position = world.player.location
    number_of_turns = 0
    game_log_dictionary = create_game_log_entry(world, language, log_filename, narrative_model.model_name if hasattr(narrative_model, 'model_name') else 'unknown', reasoning_model.model_name if hasattr(reasoning_model, 'model_name') else 'unknown')

    # Initialize memory system
    world_id = game_log_dictionary["world_id"]
    memory_system = None
    try:
        memory_system = create_memory_system(world_id, api_key)
        print(f"🧠 Intelligent memory system initialized for world {world_id}")
        
        # Load existing memories from previous logs if available
        if log_filename:
            memory_system.load_memories_from_logs(log_filename)
    except Exception as e:
        print(f"⚠️ Failed to initialize memory system: {e}")
        print("🔄 Continuing without memory enhancement...")

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
        if language == 'es':
            answer += f"\n\n---\n🌍 **Estado del mundo:**\n{world_state_formatted}"
        else:
            answer += f"\n\n---\n🌍 **World state:**\n{world_state_formatted}"

        # Print world state
        print(f"\n🌎 World state 🌍\n>Player input: {message}\n{world.render_world(language=language)}\n")

        # Save game log
        save_game_log(game_log_dictionary, log_filename, number_of_turns, answer)

        return answer.replace("<", r"\<").replace(">", r"\>")

    return game_loop

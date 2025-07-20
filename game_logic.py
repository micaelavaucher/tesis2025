"""Game logic and world management for PAYADOR.

This module contains the core game loop, world state management,
and game-related utility functions.
"""

import re
import json
import os
import jsonpickle
import time
from prompts import prompt_narrate_current_scene, prompt_world_update
from world_builder import inspect_generated_world
from config import PATH_GAMELOGS

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

def process_player_input(world, message, language, reasoning_model, number_of_turns, game_log_dictionary):
    """Process player input and update world state."""
    # Log input
    game_log_dictionary[number_of_turns]["date"] = time.ctime(time.time())
    game_log_dictionary[number_of_turns]["previous_symbolic_world_state"] = jsonpickle.encode(world, unpicklable=False)
    game_log_dictionary[number_of_turns]["previous_rendered_world_state"] = world.render_world(language=language)
    game_log_dictionary[number_of_turns]["user_input"] = message

    # Get world changes
    system_msg_update, user_msg_update = prompt_world_update(world.render_world(language=language), message, language=language)
    response_update = reasoning_model.prompt_model(system_msg=system_msg_update, user_msg=user_msg_update)

    # Show predicted outcomes
    print("🛠️ Predicted outcomes of the player input 🛠️")
    print(f"> Player input: {message}")
    try:
        predicted_outcomes = re.sub(r'#([^#]*?)#', '', response_update)
        print(f"{predicted_outcomes}\n")
        game_log_dictionary[number_of_turns]["predicted_outcomes"] = predicted_outcomes
    except Exception as e:
        print(f"Error: {e}")

    # Update world
    world.update(response_update)
    game_log_dictionary[number_of_turns]["updated_symbolic_world_state"] = jsonpickle.encode(world, unpicklable=True)
    game_log_dictionary[number_of_turns]["updated_rendered_world_state"] = world.render_world(language=language)

    return response_update

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
            answer += f"{re.findall(r'#([^#]*?)#', response_update)[0]}\n"
        except Exception as e:
            print(f"Error: {e}")

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

def create_game_loop(world, reasoning_model, narrative_model, language, log_filename, visited_locations):
    """Create the main game loop function."""
    last_player_position = world.player.location
    number_of_turns = 0
    game_log_dictionary = create_game_log_entry(world, language, log_filename, narrative_model.model_name if hasattr(narrative_model, 'model_name') else 'unknown', reasoning_model.model_name if hasattr(reasoning_model, 'model_name') else 'unknown')

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

        # Process input and update world
        response_update = process_player_input(world, message, language, reasoning_model, number_of_turns, game_log_dictionary)

        # Generate narration
        answer, last_player_position = generate_narration(world, last_player_position, response_update, language, narrative_model)

        # Check objective completion
        answer = check_objective_completion(world, answer, language)

        # Print world state
        print(f"\n🌎 World state 🌍\n>Player input: {message}\n{world.render_world(language=language)}\n")

        # Save game log
        save_game_log(game_log_dictionary, log_filename, number_of_turns, answer)

        return answer.replace("<", r"\<").replace(">", r"\>")

    return game_loop

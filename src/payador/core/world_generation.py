"""World generation logic for PAYADOR.

This module handles world generation workflows for different modes,
providing simplified world generation functions that are UI-independent.
"""

import re
import time
import json
import os
import jsonpickle
from ..llm.generation_pipeline import run_step_1_concept, run_step_2_skeleton, run_step_3_details, run_step_4_puzzles, run_step_5_expansion, create_world_incrementally
from .world_builder import create_world_from_llm_response
from ..llm.prompts import prompt_narrate_current_scene, prompt_describe_objective
from ..ui.ui_components import get_progress_messages
from ..config import PATH_GAMELOGS

def validate_world_objective(world, language, generation_attempts, max_attempts):
    """Validate that the generated world has an objective."""
    if not hasattr(world, 'objective') or not world.objective:
        if generation_attempts < max_attempts:
            return False, get_progress_messages(language)['NO_OBJECTIVE_WARNING']
        else:
            raise ValueError("Failed to generate a world with a defined objective")
    else:
        return True, get_progress_messages(language)['SUCCESS']

def generate_world_step_by_step(inspo, language):
    """Generate world step by step with progress reporting."""
    progress_messages = []
    
    # Step 1: Concept
    concept = run_step_1_concept(inspo, language)
    progress_messages.append(get_progress_messages(language)['STEP_1_COMPLETE'].format(title=concept.title))
    
    # Step 2: Skeleton
    skeleton = run_step_2_skeleton(concept, language)
    completion_msg = get_progress_messages(language)['STEP_2_COMPLETE'].format(
        locations=len(skeleton.key_locations),
        items=len(skeleton.key_items),
        characters=len(skeleton.key_characters)
    )
    progress_messages.append(completion_msg)
    
    # Step 3: Details
    world_basic = run_step_3_details(concept, skeleton, language)
    completion_msg = get_progress_messages(language)['STEP_3_COMPLETE'].format(
        locations=len(world_basic.locations),
        items=len(world_basic.items)
    )
    progress_messages.append(completion_msg)
    
    # Step 4: Puzzles
    world_with_puzzles = run_step_4_puzzles(world_basic, language)
    completion_msg = get_progress_messages(language)['STEP_4_COMPLETE'].format(
        puzzles=len(world_with_puzzles.puzzles)
    )
    progress_messages.append(completion_msg)
    
    # Step 5: Expansion
    generated_world = run_step_5_expansion(world_with_puzzles, language)
    completion_msg = get_progress_messages(language)['STEP_5_COMPLETE'].format(
        locations=len(generated_world.locations)
    )
    progress_messages.append(completion_msg)
    
    return generated_world, progress_messages

def generate_world_simple(theme, language):
    """Generate world using simple pipeline without UI progress."""
    max_attempts = 3
    generation_attempts = 0
    world = None
    
    while generation_attempts < max_attempts and (world is None or not hasattr(world, 'objective') or not world.objective):
        generation_attempts += 1
        if generation_attempts > 1:
            if language == 'es':
                print(f"🔄 Intento {generation_attempts}/{max_attempts}: Regenerando mundo porque falta el objetivo...")
            else:
                print(f"🔄 Attempt {generation_attempts}/{max_attempts}: Regenerating world because objective is missing...")
        
        try:
            generated_world = create_world_incrementally(theme, progress_callback=None, language=language)
            world = create_world_from_llm_response(generated_world)
            
            if not hasattr(world, 'objective') or not world.objective:
                if generation_attempts < max_attempts:
                    if language == 'es':
                        print("⚠️ El mundo generado no tiene un objetivo definido. Intentando de nuevo...")
                    else:
                        print("⚠️ Generated world has no defined objective. Trying again...")
                    continue
                else:
                    if language == 'es':
                        print("❌ No se pudo generar un mundo con objetivo después de varios intentos. Usando mundo predefinido.")
                    else:
                        print("❌ Failed to generate a world with objective after several attempts. Using preset world.")
                    return None
            else:
                if language == 'es':
                    print("✅ ¡Nuevo mundo creado exitosamente con objetivo definido!")
                else:
                    print("✅ New world created successfully with defined objective!")
                return world
                
        except Exception as e:
            print(f"🛑 Error crítico al crear el mundo desde la respuesta del LLM: {e}")
            if language == 'es':
                print("\n‼️ Recurriendo a un mundo predefinido de emergencia...")
            else:
                print("\n‼️ Falling back to an emergency preset world...")
            return None
    
    return world

def create_world_with_starting_narration(world, language, narrative_model, log_filename, reasoning_model_name, narrative_model_name):
    """Create world state with starting narration and save initial game state."""
    
    # Generate starting narration
    system_msg_current_scene, user_msg_current_scene = prompt_narrate_current_scene(
        world.render_world(language=language),
        previous_narrations=world.player.visited_locations[world.player.location.name],
        language=language,
        starting_scene=True
    )
    starting_narration = narrative_model.prompt_model(system_msg=system_msg_current_scene, user_msg=user_msg_current_scene)
    
    # Generate objective description
    if hasattr(world, 'objective') and world.objective:
        system_msg_objective, user_msg_objective = prompt_describe_objective(world.objective, language=language)
        narrated_objective = narrative_model.prompt_model(system_msg=system_msg_objective, user_msg=user_msg_objective)
        
        try:
            objective_text = re.findall(r'#([^#]*?)#', narrated_objective)[0]
            if not objective_text.strip().endswith(('.', '!', '?')):
                objective_text += '.'
            starting_narration += f"\n\n🎯 {objective_text}"
        except (IndexError, TypeError):
            if not narrated_objective.strip().endswith(('.', '!', '?')):
                narrated_objective += '.'
            starting_narration += f"\n\n🎯 {narrated_objective}"
    
    # Add formatted world state to starting narration
    world_state_formatted = world.format_world_state_for_chat(language=language)
    starting_narration += f"\n\n---\n{world_state_formatted}"
    
    # Initialize game state
    last_player_position = world.player.location
    number_of_turns = 0
    game_log_dictionary = {}
    game_log_dictionary["nickname"] = "anonymous"
    game_log_dictionary["language"] = language
    game_log_dictionary["world_id"] = f"generated_{int(time.time())}"
    game_log_dictionary["narrative_model_name"] = narrative_model_name
    game_log_dictionary["reasoning_model_name"] = reasoning_model_name
    game_log_dictionary[0] = {
        "date": time.ctime(time.time()),
        "initial_symbolic_world_state": jsonpickle.encode(world, unpicklable=True),
        "initial_rendered_world_state": world.render_world(language=language),
        "starting_narration": starting_narration
    }
    
    # Save initial game state
    try:
        with open(os.path.join(PATH_GAMELOGS, log_filename), 'w', encoding='utf-8') as f:
            json.dump(game_log_dictionary, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"⚠️ Warning: Could not save game log: {e}")
    
    return starting_narration

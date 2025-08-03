"""World generation logic for PAYADOR.

This module handles world generation workflows for different modes,
including step-by-step progress reporting for the UI.
"""

import gradio as gr
import re
import time
import json
import os
import jsonpickle
from generation_pipeline import run_step_1_concept, run_step_2_skeleton, run_step_3_details, run_step_4_puzzles, run_step_5_expansion, create_world_incrementally
from world_builder import create_world_from_llm_response
from prompts import prompt_narrate_current_scene, prompt_describe_objective
from ui_components import get_progress_messages
from config import PATH_GAMELOGS

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
    
    # Import individual step functions
    concept = run_step_1_concept(inspo)
    yield progress_messages, get_progress_messages(language)['STEP_1_COMPLETE'].format(title=concept.title)
    
    skeleton = run_step_2_skeleton(concept)
    completion_msg = get_progress_messages(language)['STEP_2_COMPLETE'].format(
        locations=len(skeleton.key_locations),
        items=len(skeleton.key_items),
        characters=len(skeleton.key_characters)
    )
    yield progress_messages, completion_msg
    
    world_basic = run_step_3_details(concept, skeleton)
    completion_msg = get_progress_messages(language)['STEP_3_COMPLETE'].format(
        locations=len(world_basic.locations),
        items=len(world_basic.items)
    )
    yield progress_messages, completion_msg
    
    world_with_puzzles = run_step_4_puzzles(world_basic)
    completion_msg = get_progress_messages(language)['STEP_4_COMPLETE'].format(
        puzzles=len(world_with_puzzles.puzzles)
    )
    yield progress_messages, completion_msg
    
    generated_world = run_step_5_expansion(world_with_puzzles)
    completion_msg = get_progress_messages(language)['STEP_5_COMPLETE'].format(
        locations=len(generated_world.locations)
    )
    yield progress_messages, completion_msg
    
    return generated_world

def create_world_with_progress(inspo, language, narrative_model, reasoning_model_name, narrative_model_name, log_filename, world_ref, game_loop_ref=None):
    """Create world with detailed progress reporting for UI."""
    progress_messages = []
    messages = get_progress_messages(language)
    
    # Show initial progress
    yield (
        gr.update(),  # pre_game
        gr.update(),  # main_game
        [],  # chat
        gr.update(),  # error_output
        gr.update(interactive=False, value="Generando..."),  # button
        gr.update(value=messages['INIT'], visible=True)  # progress
    )
    
    max_attempts = 3
    generation_attempts = 0
    world = None
    
    while generation_attempts < max_attempts and (world is None or not hasattr(world, 'objective') or not world.objective):
        generation_attempts += 1
        
        if generation_attempts > 1:
            retry_msg = messages['RETRY'].format(attempt=generation_attempts, max_attempts=max_attempts)
            progress_messages.append(retry_msg)
            yield (
                gr.update(), gr.update(), [], gr.update(),
                gr.update(interactive=False, value="Generando..."),
                gr.update(value="\n".join(progress_messages))
            )
        
        # Step 1: Concept
        progress_messages.append(messages['STEP_1'])
        yield (
            gr.update(), gr.update(), [], gr.update(),
            gr.update(interactive=False, value="Generando..."),
            gr.update(value="\n".join(progress_messages))
        )
        
        concept = run_step_1_concept(inspo)
        progress_messages.append(messages['STEP_1_COMPLETE'].format(title=concept.title))
        yield (
            gr.update(), gr.update(), [], gr.update(),
            gr.update(interactive=False, value="Generando..."),
            gr.update(value="\n".join(progress_messages))
        )
        
        # Step 2: Skeleton
        progress_messages.append(messages['STEP_2'])
        yield (
            gr.update(), gr.update(), [], gr.update(),
            gr.update(interactive=False, value="Generando..."),
            gr.update(value="\n".join(progress_messages))
        )
        
        skeleton = run_step_2_skeleton(concept)
        progress_messages.append(messages['STEP_2_COMPLETE'].format(
            locations=len(skeleton.key_locations),
            items=len(skeleton.key_items),
            characters=len(skeleton.key_characters)
        ))
        yield (
            gr.update(), gr.update(), [], gr.update(),
            gr.update(interactive=False, value="Generando..."),
            gr.update(value="\n".join(progress_messages))
        )
        
        # Step 3: Details
        progress_messages.append(messages['STEP_3'])
        yield (
            gr.update(), gr.update(), [], gr.update(),
            gr.update(interactive=False, value="Generando..."),
            gr.update(value="\n".join(progress_messages))
        )
        
        world_basic = run_step_3_details(concept, skeleton)
        progress_messages.append(messages['STEP_3_COMPLETE'].format(
            locations=len(world_basic.locations),
            items=len(world_basic.items)
        ))
        yield (
            gr.update(), gr.update(), [], gr.update(),
            gr.update(interactive=False, value="Generando..."),
            gr.update(value="\n".join(progress_messages))
        )
        
        # Step 4: Puzzles
        progress_messages.append(messages['STEP_4'])
        yield (
            gr.update(), gr.update(), [], gr.update(),
            gr.update(interactive=False, value="Generando..."),
            gr.update(value="\n".join(progress_messages))
        )
        
        world_with_puzzles = run_step_4_puzzles(world_basic)
        progress_messages.append(messages['STEP_4_COMPLETE'].format(
            puzzles=len(world_with_puzzles.puzzles)
        ))
        yield (
            gr.update(), gr.update(), [], gr.update(),
            gr.update(interactive=False, value="Generando..."),
            gr.update(value="\n".join(progress_messages))
        )
        
        # # Step 5: Expansion
        # progress_messages.append(messages['STEP_5'])
        # yield (
        #     gr.update(), gr.update(), [], gr.update(),
        #     gr.update(interactive=False, value="Generando..."),
        #     gr.update(value="\n".join(progress_messages))
        # )
        
        # generated_world = run_step_5_expansion(world_with_puzzles)
        # progress_messages.append(messages['STEP_5_COMPLETE'].format(
        #     locations=len(generated_world.locations)
        # ))
        # yield (
        #     gr.update(), gr.update(), [], gr.update(),
        #     gr.update(interactive=False, value="Generando..."),
        #     gr.update(value="\n".join(progress_messages))
        # )
        
        progress_messages.append(messages['PIPELINE_COMPLETE'])
        progress_messages.append(messages['BUILDING_WORLD'])
        yield (
            gr.update(), gr.update(), [], gr.update(),
            gr.update(interactive=False, value="Generando..."),
            gr.update(value="\n".join(progress_messages))
        )
        
        # world = create_world_from_llm_response(generated_world)
        world = create_world_from_llm_response(world_with_puzzles)
        
        try:
            is_valid, validation_msg = validate_world_objective(world, language, generation_attempts, max_attempts)
            progress_messages.append(validation_msg)
            
            if is_valid:
                yield (
                    gr.update(), gr.update(), [], gr.update(),
                    gr.update(interactive=False, value="Generando..."),
                    gr.update(value="\n".join(progress_messages))
                )
                break
            else:
                yield (
                    gr.update(), gr.update(), [], gr.update(),
                    gr.update(interactive=False, value="Generando..."),
                    gr.update(value="\n".join(progress_messages))
                )
                continue
                
        except Exception as e:
            if generation_attempts >= max_attempts:
                raise e
            error_msg = f"Error on attempt {generation_attempts}: {e}"
            progress_messages.append(error_msg)
            yield (
                gr.update(), gr.update(), [], gr.update(),
                gr.update(interactive=False, value="Generando..."),
                gr.update(value="\n".join(progress_messages))
            )
            continue
    
    # Generate narration
    progress_messages.append(messages['NARRATION'])
    yield (
        gr.update(), gr.update(), [], gr.update(),
        gr.update(interactive=False, value="Generando..."),
        gr.update(value="\n".join(progress_messages))
    )
    
    system_msg_current_scene, user_msg_current_scene = prompt_narrate_current_scene(
        world.render_world(language=language),
        previous_narrations=world.player.visited_locations[world.player.location.name],
        language=language,
        starting_scene=True
    )
    starting_narration = narrative_model.prompt_model(system_msg=system_msg_current_scene, user_msg=user_msg_current_scene)
    
    # Generate objective description
    if hasattr(world, 'objective') and world.objective:
        progress_messages.append(messages['OBJECTIVE'])
        yield (
            gr.update(), gr.update(), [], gr.update(),
            gr.update(interactive=False, value="Generando..."),
            gr.update(value="\n".join(progress_messages))
        )
        
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
    
    # Save world state
    progress_messages.append(messages['SAVING'])
    yield (
        gr.update(), gr.update(), [], gr.update(),
        gr.update(interactive=False, value="Generando..."),
        gr.update(value="\n".join(progress_messages))
    )
    
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
    
    with open(os.path.join(PATH_GAMELOGS, log_filename), 'w', encoding='utf-8') as f:
        json.dump(game_log_dictionary, f, ensure_ascii=False, indent=4)
    
    # Store world reference for game loop
    world_ref['world'] = world
    
    # Reset game loop reference when new world is created
    if game_loop_ref is not None:
        game_loop_ref['game_loop'] = None
    
    progress_messages.append(messages['COMPLETE'])
    
    # Return final UI state
    yield (
        gr.update(visible=False),  # pre_game hidden
        gr.update(visible=True),   # main_game visible
        [{"role": "assistant", "content": starting_narration}],  # chat with initial narration
        gr.update(value="", visible=False),  # error_output hidden
        gr.update(value="Crear mundo", interactive=True),  # button enabled
        gr.update(value="\n".join(progress_messages), visible=False)  # progress hidden
    )

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
            generated_world = create_world_incrementally(theme, progress_callback=None)
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

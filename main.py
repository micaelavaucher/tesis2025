"""Implement the main loop for the PAYADOR approach, described in Fig.3 of the paper.

The main steps in the loop are:
- Describe the ficional world in simple sentences
- Get the player input
- Prompt a model to predict the outcomes in the world, after the actions described by the player.
"""

import re
import sys
import configparser

import example_worlds
from models import get_llm
from prompts import (
    prompt_narrate_current_scene,
    prompt_world_update,
    prompt_world_update_structured,
    prompt_generate_world,
    prompt_expand_world,
    prompt_describe_objective,
    should_expand_world)
from structured_data_models import GeneratedWorld, WorldExpansion
from world_builder import (
    create_world_from_llm_response, expand_world_from_llm_response)


# Load configuration
config = configparser.ConfigParser()
config.read('config.ini')

# Get language and model settings from config
language = config['Options']['Language']
reasoning_model_name = config['Models']['ReasoningModel']
narrative_model_name = config['Models']['NarrativeModel']

# Check if we should use a preset world or generate a new one
use_preset = len(sys.argv) > 1 and sys.argv[1] in ["0", "1", "2"]

# Initialize the models
reasoning_model = get_llm(reasoning_model_name)
narrative_model = get_llm(narrative_model_name)

# Welcome the user
if language == 'es':
    print("""
PAYADOR es un enfoque para abordar el problema de actualización del mundo en Narrativa Interactiva.
Esta prueba de concepto está destinada a facilitar la investigación en el problema mencionado y otras tareas relacionadas.

El sistema imprimirá el 🌎 Estado del mundo 🌍 actual y una posible 📖 narración 📖 para él.
Luego se te pedirá que ingreses alguna(s) acción(es), y el sistema tratará de predecir los resultados.

Ingresa "q" para salir.
""")
else:
    print("""
PAYADOR is an approach to tackle the world-update problem in Interactive Storytelling.
This proof of concept is intended to ease research on the aforementioned problem and other related tasks. 

The system will print the current 🌎 World state 🌍 and a possible 📖 narration 📖 for it.
Then you will be asked to enter some action(s), and the system will try to predict the outcomes. 

Enter "q" to quit.
""")

# Generate or load a world
if use_preset:
    world_id = sys.argv[1]
    world = example_worlds.get_world(world_id, language=language)
    if language == 'es':
        print("Usando mundo predefinido...")
    else:
        print("Using preset world...")
else:
    if language == 'es':
        print("Generando un nuevo mundo...")
    else:
        print("Generating a new world...")
    
    world_prompt = prompt_generate_world(language=language)
    
    # Try structured generation first, fallback to regular if it fails
    try:
        if hasattr(reasoning_model, 'prompt_model_structured'):
            world_response = reasoning_model. \
                prompt_model_structured(world_prompt, GeneratedWorld)
        # else:
            # Fallback for models that don't support structured output
            # world_response = reasoning_model.prompt_model("Generate a fictional world for an interactive story.", world_prompt)
    except Exception as e:
        print(f"Error with structured generation: {e}")
        # world_response = reasoning_model.prompt_model("Generate a fictional world for an interactive story.", world_prompt)

    # For debugging
    if language == 'es':
        print("Respuesta de generación de mundo recibida, creando mundo...")
    else:
        print("World generation response received, creating world...")

    try:
        # Handle both structured and unstructured responses
        if isinstance(world_response, dict):
            world = create_world_from_llm_response(world_response)
        else:
            world = create_world_from_llm_response(world_response)
        
        if language == 'es':
            print("¡Nuevo mundo creado exitosamente!")
        else:
            print("New world created successfully!")
    except Exception as e:
        print(f"Error creating world: {e}")
        if language == 'es':
            print("\nRecurriendo a mundo predefinido...")
        else:
            print("\nFalling back to preset world...")
        world = example_worlds.get_world("1", language=language)

last_player_position = None

# Generate a description of the starting scene
if not use_preset or last_player_position is None:
    last_player_position = world.player.location
    
    system_msg_current_scene, user_msg_current_scene = prompt_narrate_current_scene(
        world.render_world(language=language),
        previous_narrations=world.player.visited_locations[world.player.location.name],
        language=language, 
        starting_scene=True
    )
    starting_narration = narrative_model.prompt_model(system_msg=system_msg_current_scene, user_msg=user_msg_current_scene)
    world.player.visited_locations[world.player.location.name].append(starting_narration)
    
    if language == 'es':
        print("\n📖 Narración inicial 📖")
    else:
        print("\n📖 Starting narration 📖")
    print(f"{starting_narration}\n")

# In the objective narration section:
if hasattr(world, 'objective') and world.objective:
    system_msg_objective, user_msg_objective = prompt_describe_objective(world.objective, language=language)
    narrated_objective = narrative_model.prompt_model(system_msg=system_msg_objective, user_msg=user_msg_objective)
    
    try:
        objective_text = re.findall(r'#([^#]*?)#', narrated_objective)[0]
        if language == 'es':
            print(f"🎯 Objetivo: {objective_text}\n")
        else:
            print(f"🎯 Objective: {objective_text}\n")
    except Exception as e:
        if language == 'es':
            print(f"🎯 Objetivo: {narrated_objective}\n")
        else:
            print(f"🎯 Objective: {narrated_objective}\n")
else:
    print("DEBUG: No objective found in world")

# Track player's position and visited locations
last_player_position = world.player.location
visited_locations = set()
expansion_cooldown = 0

while(True):
    # Show the state of the world
    print(f"🌎 World state 🌍\n{world.render_world(language=language)}\n")

    # Track visited locations
    visited_locations.add(world.player.location.name)

    # If the player is in a different place, narrate the scene
    if last_player_position is not world.player.location:
        last_player_position = world.player.location
        system_msg_scene, user_msg_scene = prompt_narrate_current_scene(
            world.render_world(language=language), 
            previous_narrations=world.player.visited_locations[world.player.location.name],
            language=language
        )
        response_scene = narrative_model.prompt_model(system_msg=system_msg_scene, user_msg=user_msg_scene)
        
        if language == 'es':
            print("\n📖 Narración de la escena 📖")
        else:
            print("\n📖 Narration of the scene 📖")
        
        try:
            print(f"{response_scene}\n")
            world.player.visited_locations[world.player.location.name].append(response_scene)
        except Exception as e:
            print(f"Error: {e}")

    # Take the input from the user
    if language == 'es':
        user_input = input("\n¿Qué quieres hacer?\n\t\t\t👉 ")
    else:
        user_input = input("\nWhat do you want to do?\n\t\t\t👉 ")
    
    if user_input == "q":
        break

    # Create the prompt and run the model - try structured first
    try:
        if hasattr(reasoning_model, 'prompt_model_structured'):
            system_msg_update, user_msg_update, schema = prompt_world_update_structured(
                world.render_world(language=language), user_input, language=language)
            
            # Create full prompt for structured call
            full_prompt = system_msg_update + "\n\n" + user_msg_update
            response_update = reasoning_model.prompt_model_structured(full_prompt, schema)
            
            # Use structured processing
            if response_update:
                # Extract narration from structured data
                narration = response_update.get("narration", "")
                
                if language == 'es':
                    print("\n🛠️ Resultados predichos de la entrada del jugador 🛠️")
                else:
                    print("\n🛠️ Predicted outcomes of the player input 🛠️")
                print(f"{narration}\n")
                
                # Update world with structured data
                world.update_structured(response_update)
            else:
                raise Exception("Empty structured response")
                
        else:
            raise Exception("Model doesn't support structured output")
            
    except Exception as e:
        # Fallback to traditional text-based approach
        print(f"Structured approach failed ({e}), using traditional approach...")
        
        system_msg_update, user_msg_update = prompt_world_update(
            world.render_world(language=language), user_input, language=language)
        response_update = reasoning_model.prompt_model(system_msg=system_msg_update, user_msg=user_msg_update)

        # Show the detected changes in the fictional world
        if language == 'es':
            print("\n🛠️ Resultados predichos de la entrada del jugador 🛠️")
        else:
            print("\n🛠️ Predicted outcomes of the player input 🛠️")
        
        try:
            predicted_outcomes = re.sub(r'#([^#]*?)#','',response_update)
            print(f"{predicted_outcomes}\n")
        except Exception as e:
            print(f"Error: {e}")

        # Show a narration for those changes
        if language == 'es':
            print("\n📖 Narración de los resultados predichos 📖")
        else:
            print("\n📖 Narration of the predicted outcomes 📖")
        
        try:
            narration = re.findall(r'#([^#]*?)#',response_update)[0]
            print(f"{narration}\n")
        except Exception as e:
            print(f"Error: {e}")

        # Parse the response and update the world
        world.update(response_update)

    # Check if objective is completed
    if hasattr(world, 'check_objective') and world.check_objective():
        if language == 'es':
            print("\n🎯 ¡Completaste el objetivo! 🎯")
            print("¡Felicidades! Has completado tu misión.")
        else:
            print("\n🎯 You have completed your quest! 🎯")
            print("Congratulations! You have finished your mission.")
        
        # Ask if player wants to continue exploring
        if language == 'es':
            continue_choice = input("\n¿Quieres continuar explorando? (s/n): ")
        else:
            continue_choice = input("\nDo you want to continue exploring? (y/n): ")
        
        if continue_choice.lower() in ['n', 'no']:
            break

    # Check if we should expand the world
    expansion_cooldown -= 1

    # Expansion conditions:
    # 1. Player explicitly requests exploration
    # 2. Player has visited all available locations
    # 3. Cooldown period has passed
    should_expand = (
        should_expand_world(user_input) or
        (len(visited_locations) >= len(world.locations))
    ) and expansion_cooldown <= 0

    if should_expand:
        if language == 'es':
            print("\n🌱 Expandiendo el mundo...🌱")
        else:
            print("\n🌱 Expanding the world...🌱")

        expansion_prompt = prompt_expand_world(
            world.render_world(language=language),
            world.player.location.name,
            language=language)
        
        try:
            if hasattr(reasoning_model, 'prompt_model_structured'):
                expansion_response = reasoning_model.prompt_model_structured(expansion_prompt, WorldExpansion.model_json_schema())
            else:
                expansion_response = reasoning_model.prompt_model("Expand the world.", expansion_prompt)
            
            expand_world_from_llm_response(world, expansion_response)
            
            if language == 'es':
                print("¡Mundo expandido con nuevas áreas para explorar!\n")
            else:
                print("World expanded with new areas to explore!\n")

            # Set cooldown to prevent too frequent expansions
            expansion_cooldown = 5
        except Exception as e:
            if language == 'es':
                print(f"Error expandiendo mundo: {e}")
            else:
                print(f"Error expanding world: {e}")
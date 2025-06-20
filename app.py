import gradio as gr
import re
import time
import json
import os
import jsonpickle
import configparser
import example_worlds

from models import get_llm
from prompts import (
    prompt_narrate_current_scene, 
    prompt_world_update, 
    prompt_describe_objective,
    prompt_generate_world,
    prompt_generate_turtle_world_validation,
    prompt_expand_world,
    should_expand_world
)

from structured_data_models import GeneratedWorld, WorldExpansion
from world_builder import (
    create_world_from_llm_response, expand_world_from_llm_response
)

PATH_GAMELOGS = 'logs'

# config
config = configparser.ConfigParser()
config.read('config.ini')

# language of the game
language = config['Options']['Language']

# Initialize the model 
reasoning_model_name = config['Models']['ReasoningModel']
narrative_model_name = config['Models']['NarrativeModel']
reasoning_model = get_llm(reasoning_model_name)
narrative_model = get_llm(narrative_model_name)

# Create a name for the log file
timestamp = time.time()
today =  time.gmtime(timestamp)
log_filename =  f"{today[0]}_{today[1]}_{today[2]}_{str(int(time.time()))[-5:]}.json"

# Initialize world expansion variables
visited_locations = set()

# The game loop
def game_loop(message, history):
    global last_player_position
    global number_of_turns
    global game_log_dictionary

    # DEBUG: Comando especial para inspeccionar puzzles
    if message.lower() in ["inspect puzzles", "inspeccionar puzzles", "debug puzzles", "debug", "inspect"]:
        debug_info = "🧩 **Información de Puzzles:**\n\n"
        
        if hasattr(world, 'puzzles') and world.puzzles:
            for puzzle_name, puzzle in world.puzzles.items():
                debug_info += f"**{puzzle_name}:**\n"
                debug_info += f"- Descripción: {', '.join(puzzle.descriptions)}\n"
                debug_info += f"- Problema: {puzzle.problem}\n"
                debug_info += f"- Respuesta: {puzzle.answer}\n\n"
        else:
            debug_info += "No se encontraron puzzles en el mundo.\n\n"
            
        debug_info += "🚪 **Pasajes Bloqueados:**\n\n"
        blocked_found = False
        for location in world.locations.values():
            if hasattr(location, 'blocked_locations') and location.blocked_locations:
                for blocked_loc, blocking_element in location.blocked_locations.items():
                    blocked_found = True
                    blocking_type = type(blocking_element[1]).__name__
                    debug_info += f"- {location.name} → {blocked_loc} (bloqueado por: {blocking_element[1].name} [{blocking_type}])\n"
        
        if not blocked_found:
            debug_info += "No se encontraron pasajes bloqueados.\n"
            
        return debug_info.replace("<",r"\<").replace(">", r"\>")

    # DEBUG: Comando especial para inspeccionar el mundo
    if message.lower() in ["inspect", "inspeccionar", "inspect world", "inspeccionar mundo"]:
        from world_builder import inspect_generated_world
        debug_info = inspect_generated_world(world, language)
        return debug_info.replace("<",r"\<").replace(">", r"\>")

    number_of_turns+=1
    game_log_dictionary[number_of_turns] = {}
    game_log_dictionary[number_of_turns]["date"] = time.ctime(time.time())
    game_log_dictionary[number_of_turns]["previous_symbolic_world_state"] = jsonpickle.encode(world, unpicklable=False)
    game_log_dictionary[number_of_turns]["previous_rendered_world_state"] = world.render_world(language=language)
    game_log_dictionary[number_of_turns]["user_input"] = message

    # Track visited locations
    visited_locations.add(world.player.location.name)

    answer = ""

    # Get the changes in the world
    system_msg_update, user_msg_update = prompt_world_update(world.render_world(language=language), message, language=language)
    response_update = reasoning_model.prompt_model(system_msg=system_msg_update, user_msg=user_msg_update)

    # Show the detected changes in the fictional world
    print("🛠️ Predicted outcomes of the player input 🛠️")
    print(f"> Player input: {message}")
    try:
        predicted_outcomes = re.sub(r'#([^#]*?)#','',response_update) 
        print(f"{predicted_outcomes}\n")
        game_log_dictionary[number_of_turns]["predicted_outcomes"] = predicted_outcomes

    except Exception as e:
        print (f"Error: {e}")
    
    # World update
    world.update(response_update)
    game_log_dictionary[number_of_turns]["updated_symbolic_world_state"] = jsonpickle.encode(world, unpicklable=True)
    game_log_dictionary[number_of_turns]["updated_rendered_world_state"] = world.render_world(language=language)
    
    if last_player_position is not world.player.location:
        # Narrate new scene
        last_player_position = world.player.location
        system_msg_new_scene, user_msg_new_scene = prompt_narrate_current_scene(
            world.render_world(language=language),
            previous_narrations = world.player.visited_locations[world.player.location.name],
            language=language)

        new_scene_narration = narrative_model.prompt_model(system_msg=system_msg_new_scene, user_msg=user_msg_new_scene)
        world.player.visited_locations[world.player.location.name]+=[new_scene_narration] 
        answer += f"\n{new_scene_narration}\n\n"
    else:
        # Narrate actions in the current scene
        try:
            answer+= f"{re.findall(r'#([^#]*?)#',response_update)[0]}\n"
        except Exception as e:
            print (f"Error: {e}")

    # Check if objective is completed
    if world.check_objective():
        if language=='es':
            answer += "\n\n🎯¡Completaste el objetivo!"
        else:
            answer += "\n\n🎯You have completed your quest!"

    print(f"\n🌎 World state 🌍\n>Player input: {message}\n{world.render_world(language=language)}\n")

    game_log_dictionary[number_of_turns]["narration"] = answer

    # Dump the whole gamelog to a json file after this turn
    with open(os.path.join(PATH_GAMELOGS,log_filename), 'w', encoding='utf-8') as f:
        json.dump(game_log_dictionary, f, ensure_ascii=False, indent=4)
    
    return answer.replace("<",r"\<").replace(">", r"\>")

generation_mode = config['Options'].get('GenerationMode', 'preset') # 'preset' es el valor por defecto si no existe la clave

if generation_mode == 'generate':
    if language == 'es':
        print("⚙️ Modo de generación: Generando un nuevo mundo desde cero...")
    else:
        print("⚙️ Generation mode: Generating a new world from scratch...")

    # world_prompt = prompt_generate_world(language=language)
    world_prompt = prompt_generate_turtle_world_validation(language=language)

    try:
        if hasattr(reasoning_model, 'prompt_model_structured'):
            world_response = reasoning_model.prompt_model_structured(world_prompt, GeneratedWorld)
        else:
            print("⚠️ El modelo de razonamiento no soporta 'prompt_model_structured'. Usando generación de texto plano.")
            world_id = config["Options"]["WorldID"]
            world = example_worlds.get_world(world_id, language=language)
            
    except Exception as e:
        print(f"⚠️ La generación estructurada falló ({e}), usando generación de texto plano como fallback.")
        world_id = config["Options"]["WorldID"]
        world = example_worlds.get_world(world_id, language=language)

    try:
        world = create_world_from_llm_response(world_response)
        if language == 'es':
            print("✅ ¡Nuevo mundo creado exitosamente!")
        else:
            print("✅ New world created successfully!")
            
    except Exception as e:
        print(f"🛑 Error crítico al crear el mundo desde la respuesta del LLM: {e}")
        if language == 'es':
            print("\n‼️ Recurriendo a un mundo predefinido de emergencia (ID: 0)...")
        else:
            print("\n‼️ Falling back to an emergency preset world (ID: 0)...")
        world_id = config["Options"]["WorldID"]
        world = example_worlds.get_world(world_id, language=language)

else: # generation_mode == 'preset'
    if language == 'es':
        print("⚙️ Modo de generación: Usando mundo predefinido...")
    else:
        print("⚙️ Generation mode: Using preset world...")
    world_id = config["Options"]["WorldID"]
    world = example_worlds.get_world(world_id, language=language)

# Initialize variables
last_player_position = world.player.location
number_of_turns = 0
game_log_dictionary = {}
game_log_dictionary["nickname"] = "anonymous"
game_log_dictionary["language"] = language
game_log_dictionary["world_id"] = f"generated_{int(time.time())}" if generation_mode.lower() == 'generate' else config["Options"]["WorldID"]
game_log_dictionary["narrative_model_name"] = narrative_model_name
game_log_dictionary["reasoning_model_name"] = reasoning_model_name

print(f"\n🌎 World state 🌍\n{world.render_world(language=language)}\n")
game_log_dictionary[0] = {}
game_log_dictionary[0]["date"] = time.ctime(time.time())
game_log_dictionary[0]["initial_symbolic_world_state"] = jsonpickle.encode(world, unpicklable=True)
game_log_dictionary[0]["initial_rendered_world_state"] = world.render_world(language=language)

# Generate a description of the starting scene
system_msg_current_scene, user_msg_current_scene = prompt_narrate_current_scene(
    world.render_world(language=language),
    previous_narrations = world.player.visited_locations[world.player.location.name],
    language=language, 
    starting_scene=True
    )
starting_narration = narrative_model.prompt_model(system_msg=system_msg_current_scene, user_msg=user_msg_current_scene)
world.player.visited_locations[world.player.location.name]+=[starting_narration]

# Generate a description of the main objective
if hasattr(world, 'objective') and world.objective:
    system_msg_objective, user_msg_objective = prompt_describe_objective(world.objective, language=language)
    narrated_objective = narrative_model.prompt_model(system_msg=system_msg_objective, user_msg=user_msg_objective)
    try:
        objective_text = re.findall(r'#([^#]*?)#', narrated_objective)[0]
        starting_narration += f"\n\n🎯 {objective_text}"
    except (IndexError, TypeError):
        print("⚠️ No se pudo extraer el objetivo narrado con el formato #...#, usando la respuesta completa.")
        starting_narration += f"\n\n🎯 {narrated_objective}"
else:
    print("ℹ️ No se encontró un objetivo principal en el mundo generado/cargado.")

game_log_dictionary[0]["starting_narration"] = starting_narration

with open(os.path.join(PATH_GAMELOGS,log_filename), 'w', encoding='utf-8') as f:
    json.dump(game_log_dictionary, f, ensure_ascii=False, indent=4)

# Instantiate the Gradio app
gradio_interface = gr.ChatInterface(
    fn=game_loop,
    chatbot = gr.Chatbot(
        height="85vh",
        value=[{"role": "assistant", "content": starting_narration.replace("<",r"\<").replace(">", r"\>")}],
        bubble_full_width = False, 
        show_copy_button = False,
        type='messages',
    ),
    textbox=gr.Textbox(placeholder="What do you want to do?", container=False, scale=5),
    title="PAYADOR",
    theme="Soft",
    type='messages',
    autoscroll=True,
)

gradio_interface.launch(inbrowser=False)

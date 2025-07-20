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
)

from generation_pipeline import create_world_incrementally
from world_builder import create_world_from_llm_response

PATH_GAMELOGS = 'logs'

# config
config = configparser.ConfigParser()
config.read('config.ini')

# language of the game
language = config['Options']['Language']

def launch_main_interface(world, starting_narration):
    # Inicialización variables de turno
    global last_player_position, number_of_turns, game_log_dictionary
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

    with open(os.path.join(PATH_GAMELOGS,log_filename), 'w', encoding='utf-8') as f:
        json.dump(game_log_dictionary, f, ensure_ascii=False, indent=4)

    gr.ChatInterface(
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
    ).launch()


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

if generation_mode == "inspiration":
    if language == "es":
        TITLE = "# 🌱 PAYADOR: Modo inspiración"
        PROMPT_LABEL = "Escribí una frase o temática para inspirar la creación del mundo:"
        TEXTBOX_LABEL = "Frase o temática"
        CREATE_BUTTON_TEXT = "Crear mundo"
        ERROR_LABEL = "Error"
        SPINNER_TEXT = "Generando mundo..."
        GENERATE_WORLD= "Crear mundo"
        TEXTBOX_PLACEHOLDER = "¿Qué quieres hacer?"
    else:
        TITLE = "# 🌱 PAYADOR: Inspiration Mode"
        PROMPT_LABEL = "Write a theme or idea to inspire the world:"
        TEXTBOX_LABEL = "Theme or idea"
        CREATE_BUTTON_TEXT = "Create world"
        ERROR_LABEL = "Error"
        SPINNER_TEXT = "Generating world..."
        GENERATE_WORLD= "Create world"
        TEXTBOX_PLACEHOLDER = "What do you want to do next?"

    with gr.Blocks() as interfaz:
        with gr.Column(visible=True) as pre_game:
            gr.Markdown(TITLE)
            gr.Markdown(PROMPT_LABEL)
            inspo_input = gr.Textbox(label=TEXTBOX_LABEL)
            generar_btn = gr.Button(GENERATE_WORLD, elem_id="generar-btn")
            error_output = gr.Textbox(visible=False, label=ERROR_LABEL)
            spinner = gr.HTML(visible=False) 

        with gr.Column(visible=False) as main_game:
            chat = gr.Chatbot(
                height="85vh",
                bubble_full_width=False, 
                show_copy_button=False,
                type='messages'
            )
            textbox = gr.Textbox(placeholder=TEXTBOX_PLACEHOLDER, container=False, scale=5)

        # Función que muestra el spinner y desactiva botón
        def preparar_creacion():
            spinner_html = """
            <div style='text-align:center;'>
              <div class='loader'></div>
              <p>Generando mundo...</p>
            </div>
            <style>
              .loader {
                border: 6px solid #f3f3f3;
                border-top: 6px solid #3b82f6;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: auto;
              }
              @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
              }
            </style>
            """
            return gr.update(value=SPINNER_TEXT, interactive=False), gr.update(value=spinner_html, visible=True)


        def build_world_and_start(inspo):
            try:
                global world, last_player_position, number_of_turns, game_log_dictionary

                print(f"[INFO] Generando mundo desde inspiración: '{inspo}'")
                
                # Maximum number of generation attempts
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
                    
                    # Usar el nuevo pipeline incremental con la inspiración como tema
                    generated_world = create_world_incrementally(inspo)
                    world = create_world_from_llm_response(generated_world)
                    
                    try:
                        # Verificar que el mundo tiene un objetivo
                        if not hasattr(world, 'objective') or not world.objective:
                            if generation_attempts < max_attempts:
                                if language == 'es':
                                    print("⚠️ El mundo generado no tiene un objetivo definido. Intentando de nuevo...")
                                else:
                                    print("⚠️ Generated world has no defined objective. Trying again...")
                                continue
                            else:
                                if language == 'es':
                                    print("❌ No se pudo generar un mundo con objetivo después de varios intentos.")
                                else:
                                    print("❌ Failed to generate a world with objective after several attempts.")
                                raise ValueError("Failed to generate a world with a defined objective")
                        else:
                            if language == 'es':
                                print("✅ ¡Nuevo mundo creado exitosamente con objetivo definido!")
                            else:
                                print("✅ New world created successfully with defined objective!")
                    except Exception as e:
                        if generation_attempts >= max_attempts:
                            raise e
                        print(f"Error on attempt {generation_attempts}: {e}")
                        continue
                
                # print("world:", world.model_dump() if hasattr(world, 'model_dump') else str(world))

                # Narración escena inicial
                system_msg_current_scene, user_msg_current_scene = prompt_narrate_current_scene(
                    world.render_world(language=language),
                    previous_narrations=world.player.visited_locations[world.player.location.name],
                    language=language,
                    starting_scene=True
                )
                starting_narration = narrative_model.prompt_model(system_msg=system_msg_current_scene, user_msg=user_msg_current_scene)

                # Objetivo
                if hasattr(world, 'objective') and world.objective:
                    system_msg_objective, user_msg_objective = prompt_describe_objective(world.objective, language=language)
                    narrated_objective = narrative_model.prompt_model(system_msg=system_msg_objective, user_msg=user_msg_objective)
                    
                    try:
                        # Try to extract formatted objective text between # characters
                        objective_text = re.findall(r'#([^#]*?)#', narrated_objective)[0]
                        # Make sure the objective text has proper punctuation
                        if not objective_text.strip().endswith(('.', '!', '?')):
                            objective_text += '.'
                        starting_narration += f"\n\n🎯 {objective_text}"
                    except (IndexError, TypeError):
                        print("⚠️ No se pudo extraer el objetivo narrado con el formato #...#, usando la respuesta completa.")
                        # Make sure we have a complete sentence for the objective
                        if not narrated_objective.strip().endswith(('.', '!', '?')):
                            narrated_objective += '.'
                        starting_narration += f"\n\n🎯 {narrated_objective}"

                # Inicializar variables globales
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

                with open(os.path.join(PATH_GAMELOGS,log_filename), 'w', encoding='utf-8') as f:
                    json.dump(game_log_dictionary, f, ensure_ascii=False, indent=4)

                # Mostrar interfaz principal
                # Ocultar cargando y mostrar interfaz principal
                return (
                    gr.update(visible=False),        # pre_game
                    gr.update(visible=True),         # main_game
                    [{"role": "assistant", "content": starting_narration}],  # chat
                    gr.update(value="", visible=False),  # error_output oculto y vacío
                    gr.update(value="Crear mundo", interactive=True),        # botón
                    gr.update(value="", visible=False)                       # spinner oculto
                )

            except Exception as e:
                print(f"[ERROR] {e}")
                return (
                    gr.update(visible=True),
                    gr.update(visible=False),
                    [],
                    gr.update(value=f"❌ Error generando el mundo: {str(e)}", visible=True),
                    gr.update(value=""""""),
                    gr.update(value="", visible=False) 
                )

        # Encadenamiento: spinner y luego creación
        generar_btn.click(
            fn=preparar_creacion,
            outputs=[generar_btn, spinner]
        ).then(
            fn=build_world_and_start,
            inputs=inspo_input,
            outputs=[pre_game, main_game, chat, error_output, generar_btn, spinner]
        )

        def game_loop_wrapper(message, history):
            # Mostrar mensaje del usuario
            history.append({"role": "user", "content": message})
            
            # Obtener respuesta del modelo
            respuesta = game_loop(message, history)

            # Agregar respuesta del asistente
            history.append({"role": "assistant", "content": respuesta})

            return history, ""  # Borrar textbox para permitir seguir jugando


        textbox.submit(
            fn=game_loop_wrapper,
            inputs=[textbox, chat],
            outputs=[chat, textbox]
        )

    interfaz.launch(inbrowser=False)
    exit()

if generation_mode == 'generate':
    if language == 'es':
        print("⚙️ Modo de generación: Generando un nuevo mundo desde cero...")
    else:
        print("⚙️ Generation mode: Generating a new world from scratch...")

    # Maximum number of generation attempts
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
            generated_world = create_world_incrementally("aventura misteriosa")
            world = create_world_from_llm_response(generated_world)
            
            # Verificar que el mundo tiene un objetivo
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
                    world_id = config["Options"]["WorldID"]
                    world = example_worlds.get_world(world_id, language=language)
            else:
                if language == 'es':
                    print("✅ ¡Nuevo mundo creado exitosamente con objetivo definido!")
                else:
                    print("✅ New world created successfully with defined objective!")
                
        except Exception as e:
            print(f"🛑 Error crítico al crear el mundo desde la respuesta del LLM: {e}")
            if language == 'es':
                print("\n‼️ Recurriendo a un mundo predefinido de emergencia (ID: 0)...")
            else:
                print("\n‼️ Falling back to an emergency preset world (ID: 0)...")
            world_id = config["Options"]["WorldID"]
            world = example_worlds.get_world(world_id, language=language)
            break

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
        # Make sure the objective text has proper punctuation
        if not objective_text.strip().endswith(('.', '!', '?')):
            objective_text += '.'
        starting_narration += f"\n\n🎯 {objective_text}"
    except (IndexError, TypeError):
        print("⚠️ No se pudo extraer el objetivo narrado con el formato #...#, usando la respuesta completa.")
        # Make sure we have a complete sentence for the objective
        if not narrated_objective.strip().endswith(('.', '!', '?')):
            narrated_objective += '.'
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

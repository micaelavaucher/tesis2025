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
            progress_output = gr.Textbox(visible=False, label="Progreso", lines=10, interactive=False)

        with gr.Column(visible=False) as main_game:
            chat = gr.Chatbot(
                height="85vh",
                bubble_full_width=False, 
                show_copy_button=False,
                type='messages'
            )
            textbox = gr.Textbox(placeholder=TEXTBOX_PLACEHOLDER, container=False, scale=5)

        def build_world_and_start(inspo):
            try:
                global world, last_player_position, number_of_turns, game_log_dictionary

                print(f"[INFO] Generando mundo desde inspiración: '{inspo}'")
                
                # Lista para acumular mensajes de progreso
                progress_messages = []
                
                # Mostrar área de progreso e inhabilitar botón
                yield (
                    gr.update(),  # pre_game sin cambios
                    gr.update(),  # main_game sin cambios
                    [],  # chat sin cambios
                    gr.update(),  # error_output sin cambios
                    gr.update(interactive=False, value="Generando..."),  # botón inhabilitado
                    gr.update(value="⚙️ Iniciando generación del mundo...", visible=True)  # progreso visible
                )
                
                # Maximum number of generation attempts
                max_attempts = 3
                generation_attempts = 0
                world = None
                
                while generation_attempts < max_attempts and (world is None or not hasattr(world, 'objective') or not world.objective):
                    generation_attempts += 1
                    if generation_attempts > 1:
                        if language == 'es':
                            retry_msg = f"🔄 Intento {generation_attempts}/{max_attempts}: Regenerando mundo porque falta el objetivo..."
                        else:
                            retry_msg = f"🔄 Attempt {generation_attempts}/{max_attempts}: Regenerating world because objective is missing..."
                        print(retry_msg)
                        progress_messages.append(retry_msg)
                        yield (
                            gr.update(),
                            gr.update(),
                            [],
                            gr.update(),
                            gr.update(interactive=False, value="Generando..."),
                            gr.update(value="\n".join(progress_messages))
                        )
                    
                    # Crear callback que actualice el progreso en tiempo real
                    def progress_callback(message):
                        progress_messages.append(message)
                        # NO hacemos yield aquí porque estamos dentro de create_world_incrementally
                    
                    # Usar el nuevo pipeline incremental con la inspiración como tema
                    # Vamos a hacer esto paso a paso para poder mostrar progreso
                    from generation_pipeline import run_step_1_concept, run_step_2_skeleton, run_step_3_details, run_step_4_puzzles, run_step_5_expansion
                    
                    # Paso 1: Concepto
                    step_msg = "📝 Paso 1: Generando concepto del mundo..."
                    progress_messages.append(step_msg)
                    yield (
                        gr.update(),
                        gr.update(),
                        [],
                        gr.update(),
                        gr.update(interactive=False, value="Generando..."),
                        gr.update(value="\n".join(progress_messages))
                    )
                    
                    concept = run_step_1_concept(inspo)
                    completion_msg = f"✅ Concepto creado: '{concept.title}'"
                    progress_messages.append(completion_msg)
                    yield (
                        gr.update(),
                        gr.update(),
                        [],
                        gr.update(),
                        gr.update(interactive=False, value="Generando..."),
                        gr.update(value="\n".join(progress_messages))
                    )
                    
                    # Paso 2: Esqueleto
                    step_msg = "🦴 Paso 2: Creando esqueleto del mundo..."
                    progress_messages.append(step_msg)
                    yield (
                        gr.update(),
                        gr.update(),
                        [],
                        gr.update(),
                        gr.update(interactive=False, value="Generando..."),
                        gr.update(value="\n".join(progress_messages))
                    )
                    
                    skeleton = run_step_2_skeleton(concept)
                    completion_msg = f"✅ Esqueleto creado con {len(skeleton.key_locations)} ubicaciones, {len(skeleton.key_items)} objetos y {len(skeleton.key_characters)} personajes"
                    progress_messages.append(completion_msg)
                    yield (
                        gr.update(),
                        gr.update(),
                        [],
                        gr.update(),
                        gr.update(interactive=False, value="Generando..."),
                        gr.update(value="\n".join(progress_messages))
                    )
                    
                    # Paso 3: Detalles
                    step_msg = "🌍 Paso 3: Desarrollando detalles y conexiones..."
                    progress_messages.append(step_msg)
                    yield (
                        gr.update(),
                        gr.update(),
                        [],
                        gr.update(),
                        gr.update(interactive=False, value="Generando..."),
                        gr.update(value="\n".join(progress_messages))
                    )
                    
                    world_basic = run_step_3_details(concept, skeleton)
                    completion_msg = f"✅ Mundo base creado con {len(world_basic.locations)} ubicaciones y {len(world_basic.items)} objetos"
                    progress_messages.append(completion_msg)
                    yield (
                        gr.update(),
                        gr.update(),
                        [],
                        gr.update(),
                        gr.update(interactive=False, value="Generando..."),
                        gr.update(value="\n".join(progress_messages))
                    )
                    
                    # Paso 4: Puzzles
                    step_msg = "🧩 Paso 4: Añadiendo puzzles y obstáculos..."
                    progress_messages.append(step_msg)
                    yield (
                        gr.update(),
                        gr.update(),
                        [],
                        gr.update(),
                        gr.update(interactive=False, value="Generando..."),
                        gr.update(value="\n".join(progress_messages))
                    )
                    
                    world_with_puzzles = run_step_4_puzzles(world_basic)
                    completion_msg = f"✅ Puzzles añadidos: {len(world_with_puzzles.puzzles)} puzzles en total"
                    progress_messages.append(completion_msg)
                    yield (
                        gr.update(),
                        gr.update(),
                        [],
                        gr.update(),
                        gr.update(interactive=False, value="Generando..."),
                        gr.update(value="\n".join(progress_messages))
                    )
                    
                    # Paso 5: Expansión
                    step_msg = "🎨 Paso 5: Expandiendo con contenido adicional..."
                    progress_messages.append(step_msg)
                    yield (
                        gr.update(),
                        gr.update(),
                        [],
                        gr.update(),
                        gr.update(interactive=False, value="Generando..."),
                        gr.update(value="\n".join(progress_messages))
                    )
                    
                    generated_world = run_step_5_expansion(world_with_puzzles)
                    completion_msg = f"✅ Expansión completada: mundo final con {len(generated_world.locations)} ubicaciones"
                    progress_messages.append(completion_msg)
                    yield (
                        gr.update(),
                        gr.update(),
                        [],
                        gr.update(),
                        gr.update(interactive=False, value="Generando..."),
                        gr.update(value="\n".join(progress_messages))
                    )
                    
                    final_msg = "🌱 ¡Generación incremental completada exitosamente!"
                    progress_messages.append(final_msg)
                    yield (
                        gr.update(),
                        gr.update(),
                        [],
                        gr.update(),
                        gr.update(interactive=False, value="Generando..."),
                        gr.update(value="\n".join(progress_messages))
                    )
                    
                    progress_messages.append("🔧 Construyendo mundo desde respuesta del LLM...")
                    yield (
                        gr.update(),
                        gr.update(),
                        [],
                        gr.update(),
                        gr.update(interactive=False, value="Generando..."),
                        gr.update(value="\n".join(progress_messages))
                    )
                    
                    world = create_world_from_llm_response(generated_world)
                    
                    try:
                        # Verificar que el mundo tiene un objetivo
                        if not hasattr(world, 'objective') or not world.objective:
                            if generation_attempts < max_attempts:
                                if language == 'es':
                                    retry_msg = "⚠️ El mundo generado no tiene un objetivo definido. Intentando de nuevo..."
                                else:
                                    retry_msg = "⚠️ Generated world has no defined objective. Trying again..."
                                print(retry_msg)
                                progress_messages.append(retry_msg)
                                yield (
                                    gr.update(),
                                    gr.update(),
                                    [],
                                    gr.update(),
                                    gr.update(interactive=False, value="Generando..."),
                                    gr.update(value="\n".join(progress_messages))
                                )
                                continue
                            else:
                                if language == 'es':
                                    error_msg = "❌ No se pudo generar un mundo con objetivo después de varios intentos."
                                else:
                                    error_msg = "❌ Failed to generate a world with objective after several attempts."
                                print(error_msg)
                                raise ValueError("Failed to generate a world with a defined objective")
                        else:
                            if language == 'es':
                                success_msg = "✅ ¡Nuevo mundo creado exitosamente con objetivo definido!"
                            else:
                                success_msg = "✅ New world created successfully with defined objective!"
                            print(success_msg)
                            progress_messages.append(success_msg)
                            yield (
                                gr.update(),
                                gr.update(),
                                [],
                                gr.update(),
                                gr.update(interactive=False, value="Generando..."),
                                gr.update(value="\n".join(progress_messages))
                            )
                    except Exception as e:
                        if generation_attempts >= max_attempts:
                            raise e
                        error_msg = f"Error on attempt {generation_attempts}: {e}"
                        print(error_msg)
                        progress_messages.append(error_msg)
                        yield (
                            gr.update(),
                            gr.update(),
                            [],
                            gr.update(),
                            gr.update(interactive=False, value="Generando..."),
                            gr.update(value="\n".join(progress_messages))
                        )
                        continue
                
                # Generar narración inicial
                progress_messages.append("📖 Generando narración inicial...")
                yield (
                    gr.update(),
                    gr.update(),
                    [],
                    gr.update(),
                    gr.update(interactive=False, value="Generando..."),
                    gr.update(value="\n".join(progress_messages))
                )

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
                    progress_messages.append("🎯 Generando descripción del objetivo...")
                    yield (
                        gr.update(),
                        gr.update(),
                        [],
                        gr.update(),
                        gr.update(interactive=False, value="Generando..."),
                        gr.update(value="\n".join(progress_messages))
                    )
                    
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

                progress_messages.append("💾 Guardando estado inicial del mundo...")
                yield (
                    gr.update(),
                    gr.update(),
                    [],
                    gr.update(),
                    gr.update(interactive=False, value="Generando..."),
                    gr.update(value="\n".join(progress_messages))
                )

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

                progress_messages.append("🎉 ¡Mundo generado exitosamente! Iniciando juego...")
                
                # Mostrar interfaz principal
                yield (
                    gr.update(visible=False),        # pre_game oculto
                    gr.update(visible=True),         # main_game visible
                    [{"role": "assistant", "content": starting_narration}],  # chat con narración inicial
                    gr.update(value="", visible=False),  # error_output oculto y vacío
                    gr.update(value="Crear mundo", interactive=True),        # botón habilitado de nuevo
                    gr.update(value="\n".join(progress_messages), visible=False)  # progreso oculto al final
                )

            except Exception as e:
                print(f"[ERROR] {e}")
                yield (
                    gr.update(visible=True),         # pre_game visible (para mostrar error)
                    gr.update(visible=False),        # main_game oculto
                    [],                              # chat vacío
                    gr.update(value=f"❌ Error generando el mundo: {str(e)}", visible=True),  # error visible
                    gr.update(value="Crear mundo", interactive=True),                        # botón habilitado
                    gr.update(value="", visible=False)                                       # progreso oculto
                )

        # Encadenamiento directo para generación
        generar_btn.click(
            fn=build_world_and_start,
            inputs=inspo_input,
            outputs=[pre_game, main_game, chat, error_output, generar_btn, progress_output]
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
            generated_world = create_world_incrementally("aventura misteriosa", progress_callback=None)
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

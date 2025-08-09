"""PAYADOR - Dynamic Text Adventure World Generator

Main application entry point. This module orchestrates the different
generation modes and initializes the appropriate interface.
"""

from models import get_llm
from config import load_config, get_language, get_generation_mode, get_model_names, create_log_filename, get_world_id
from app_interface import create_inspiration_interface, create_standard_interface, generate_starting_narration
from world_generation import generate_world_simple
from game_logic import initialize_game_state
import example_worlds

# Load configuration
config = load_config()
language = get_language(config)
generation_mode = get_generation_mode(config)
reasoning_model_name, narrative_model_name = get_model_names(config)
log_filename = create_log_filename()

# Initialize models
reasoning_model = get_llm(reasoning_model_name)
narrative_model = get_llm(narrative_model_name)

# Initialize world expansion variables
visited_locations = set()

if generation_mode == "inspiration":
    # Launch inspiration mode interface
    interfaz = create_inspiration_interface(
        language, narrative_model, reasoning_model, 
        reasoning_model_name, narrative_model_name, 
        log_filename, visited_locations
    )
    interfaz.launch(inbrowser=False)
    exit()

elif generation_mode == 'generate':
    if language == 'es':
        print("⚙️ Modo de generación: Generando un nuevo mundo desde cero...")
    else:
        print("⚙️ Generation mode: Generating a new world from scratch...")

    from generation_pipeline import create_world_incrementally_generate
    from world_builder import create_world_from_llm_response
    generated_world = create_world_incrementally_generate(language)
    world = create_world_from_llm_response(generated_world)
    
    if world is None:
        # Fallback to preset world
        world_id = get_world_id(config)
        world = example_worlds.get_world(world_id, language=language)

else:  # generation_mode == 'preset'
    if language == 'es':
        print("⚙️ Modo de generación: Usando mundo predefinido...")
    else:
        print("⚙️ Generation mode: Using preset world...")
    world_id = get_world_id(config)
    world = example_worlds.get_world(world_id, language=language)

# Initialize game state for preset/generate modes
print(f"\n🌎 World state 🌍\n{world.render_world(language=language)}\n")

# Generate starting narration
starting_narration = generate_starting_narration(world, language, narrative_model)

# Initialize game variables
last_player_position, number_of_turns, game_log_dictionary = initialize_game_state(
    world, language, log_filename, narrative_model_name, reasoning_model_name, starting_narration
)

# Launch standard interface
gradio_interface = create_standard_interface(
    world, starting_narration, language, reasoning_model, 
    narrative_model, log_filename, visited_locations
)

gradio_interface.launch(inbrowser=False)

"""Incremental world generation pipeline for PAYADOR.

This module implements a step-by-step world generation system,
dividing the process into logical and sequential phases to improve
the coherence and quality of the final world.
"""

#---- Imports -----------------------------------------------------------------
from structured_data_models import (
    WorldConcept, 
    WorldSkeleton, 
    GeneratedWorld
)
from models import get_llm
import prompts
import configparser

#---- Pipeline Functions -----------------------------------------------------

def run_step_1_concept(theme: str, language) -> WorldConcept:
    """
    Generation of the general concept of the world.
    
    Args:
        theme: Base theme or concept for the world 
        
    Returns:
        WorldConcept: Validated object with the concept of the world
    """
    model = get_llm()
    prompt_text = prompts.PROMPT_STEP_1_CONCEPT_BY_THEME(theme=theme, language=language)
    print(f"[INFO] Generating world concept with theme: '{theme}'")
    print(f"[INFO] Prompt text: {prompt_text}")
    concept_response = model.prompt_model_structured(prompt_text, WorldConcept)

    # Convert dict to WorldConcept if needed
    if isinstance(concept_response, dict):
        concept = WorldConcept(**concept_response)
    else:
        concept = concept_response

    print(f"[INFO] Concepto generado: {concept.title} - {concept.backstory}")
    return concept

def run_step_1_generate_concept(language) -> WorldConcept:
    """
    Generation of the general concept of the world.
        
    Returns:
        WorldConcept: Validated object with the concept of the world
    """
    model = get_llm()
    prompt_text = prompts.PROMPT_STEP_1_CONCEPT(language=language)
    print(f"[INFO] Generating a new world concept")
    print(f"[INFO] Prompt text: {prompt_text}")
    concept_response = model.prompt_model_structured(prompt_text, WorldConcept)

    # Convert dict to WorldConcept if needed
    if isinstance(concept_response, dict):
        concept = WorldConcept(**concept_response)
    else:
        concept = concept_response

    print(f"[INFO] Concepto generado: {concept.title} - {concept.backstory}")
    return concept

def run_step_2_skeleton(concept: WorldConcept, language) -> WorldSkeleton:
    """
    Generation of the skeleton with key entities.
    
    Args:
        concept: World's concept from step from the previous step
        
    Returns:
        WorldSkeleton: Validated object with the key entities
    """
    model = get_llm()
    prompt_text = prompts.PROMPT_STEP_2_SKELETON(
        title=concept.title,
        backstory=concept.backstory,
        player_concept=concept.player_concept,
        main_objective=concept.main_objective,
        language=language
    )
    
    skeleton_response = model.prompt_model_structured(prompt_text, WorldSkeleton)
    
    if isinstance(skeleton_response, dict):
        return WorldSkeleton(**skeleton_response)
    else:
        return skeleton_response

def run_step_3_details(concept: WorldConcept, skeleton: WorldSkeleton, language) -> GeneratedWorld:
    """
    Generation of details and connections of the main route.
    
    Args:
        concept: World's concept from step 1
        skeleton: Skeleton from the previous step
        
    Returns:
        GeneratedWorld: Partially completed object with the main route
    """
    model = get_llm()
    
    # Preparar los datos del esqueleto para el prompt
    skeleton_data = f"""
    Ubicaciones clave:
    {chr(10).join([f"- {loc.name}: {loc.purpose}" for loc in skeleton.key_locations])}

    Objetos clave:
    {chr(10).join([f"- {item.name}: {item.purpose}" for item in skeleton.key_items])}

    Personajes clave:
    {chr(10).join([f"- {char.name}: {char.purpose}" for char in skeleton.key_characters])}
    """
    
    prompt_text = prompts.PROMPT_STEP_3_DETAILS(
        title=concept.title,
        backstory=concept.backstory,
        player_concept=concept.player_concept,
        main_objective=concept.main_objective,
        skeleton_data=skeleton_data,
        language=language
    )
    
    world_response = model.prompt_model_structured(prompt_text, GeneratedWorld)
    
    if isinstance(world_response, dict):
        return GeneratedWorld(**world_response)
    else:
        return world_response

def run_step_4_puzzles(world_data: GeneratedWorld, language) -> GeneratedWorld:
    """
    Generation of dependency chains with integrated puzzles.
    
    Args:
        world_data: World from the previous step
        
    Returns:
        GeneratedWorld: Modified object with complex dependency chains
    """
    model = get_llm()
    
    world_json = world_data.model_dump_json(indent=2)
    
    prompt_text = prompts.PROMPT_STEP_4_PUZZLES(
        world_data=world_json,
        language=language
    )
    
    enhanced_world_response = model.prompt_model_structured(prompt_text, GeneratedWorld)
    
    if isinstance(enhanced_world_response, dict):
        return GeneratedWorld(**enhanced_world_response)
    else:
        return enhanced_world_response

def run_step_5_expansion(world_data: GeneratedWorld, language) -> GeneratedWorld:
    """
    Paso 5: Expansion with optional content.
    
    Args:
        world_data: World from the previous step
        
    Returns:
        GeneratedWorld: Final and complete object
    """
    model = get_llm()
    
    world_json = world_data.model_dump_json(indent=2)
    
    prompt_text = prompts.PROMPT_STEP_5_EXPANSION(
        world_data=world_json,
        language=language
    )
    
    final_world_response = model.prompt_model_structured(prompt_text, GeneratedWorld)
    
    if isinstance(final_world_response, dict):
        return GeneratedWorld(**final_world_response)
    else:
        return final_world_response

def create_world_incrementally(theme: str, language: str, progress_callback=None) -> GeneratedWorld:
    """
    Main orchestrator of the incremental generation pipeline.
    
    Executes all steps sequentially to create a complete world.
    
    Args:
        theme: Base theme or concept for the world
        progress_callback: Optional function to call with progress updates
        
    Returns:
        GeneratedWorld: Fully generated and validated world
    """
    print(f"⚙️ Iniciando generación incremental del mundo con tema: '{theme}'")
    
    # Paso 1: Generar el concepto general
    step_msg = "📝 Paso 1: Generando concepto del mundo..."
    print(step_msg)
    if progress_callback:
        progress_callback(step_msg)
    concept = run_step_1_concept(theme, language)
    completion_msg = f"✅ Concepto creado: '{concept.title}'"
    print(completion_msg)
    if progress_callback:
        progress_callback(completion_msg)
    
    # Paso 2: Crear el esqueleto con entidades clave (with verification)
    step_msg = "🦴 Paso 2: Creando esqueleto del mundo..."
    print(step_msg)
    if progress_callback:
        progress_callback(step_msg)
    max_attempts = 3
    skeleton = None
    for attempt in range(1, max_attempts + 1):
        skeleton = run_step_2_skeleton(concept, language)
        # Verify skeleton sizes
        valid_locations = hasattr(skeleton, 'key_locations') and skeleton.key_locations and isinstance(skeleton.key_locations, list)
        valid_items = hasattr(skeleton, 'key_items') and skeleton.key_items and isinstance(skeleton.key_items, list)
        valid_characters = hasattr(skeleton, 'key_characters') and skeleton.key_characters and isinstance(skeleton.key_characters, list)
        config = configparser.ConfigParser()
        config.read('config.ini')
        def parse_range(value):
            if '-' in value:
                return tuple(map(int, value.split('-')))
            return int(value), int(value)
        locations_range = parse_range(config['Size_World']['Locations'])
        objects_range = parse_range(config['Size_World']['Objects'])
        npcs_range = parse_range(config['Size_World']['NPCs'])
        size_ok = (
            valid_locations and locations_range[0] <= len(skeleton.key_locations) <= locations_range[1] and
            valid_items and objects_range[0] <= len(skeleton.key_items) <= objects_range[1] and
            valid_characters and npcs_range[0] <= len(skeleton.key_characters) <= npcs_range[1]
        )
        json_ok = verify_pydantic_model(skeleton, WorldSkeleton)
        if size_ok and json_ok:
            break
        else:
            print(f"[WARNING] Skeleton verification failed on attempt {attempt}. Retrying...")
            if progress_callback:
                progress_callback(f"[WARNING] Skeleton verification failed on attempt {attempt}. Retrying...")
            skeleton = None
    if skeleton is None:
        raise ValueError("Failed to generate a valid skeleton after multiple attempts.")
    completion_msg = f"✅ Esqueleto creado con {len(skeleton.key_locations)} ubicaciones, {len(skeleton.key_items)} objetos y {len(skeleton.key_characters)} personajes"
    print(completion_msg)
    if progress_callback:
        progress_callback(completion_msg)
    
    # Paso 3: Desarrollar detalles y conexiones (with verification)
    step_msg = "🌍 Paso 3: Desarrollando detalles y conexiones..."
    print(step_msg)
    if progress_callback:
        progress_callback(step_msg)
    world_basic = None
    for attempt in range(1, max_attempts + 1):
        world_basic = run_step_3_details(concept, skeleton, language)
        json_ok = verify_pydantic_model(world_basic, GeneratedWorld)
        if json_ok:
            break
        else:
            print(f"[WARNING] Details verification failed on attempt {attempt}. Retrying...")
            if progress_callback:
                progress_callback(f"[WARNING] Details verification failed on attempt {attempt}. Retrying...")
            world_basic = None
    if world_basic is None:
        raise ValueError("Failed to generate valid world details after multiple attempts.")
    completion_msg = f"✅ Mundo base creado con {len(world_basic.locations)} ubicaciones y {len(world_basic.items)} objetos"
    print(completion_msg)
    if progress_callback:
        progress_callback(completion_msg)

    # Paso 4: Añadir puzzles y obstáculos (with verification)
    step_msg = "🧩 Paso 4: Añadiendo puzzles y obstáculos..."
    print(step_msg)
    if progress_callback:
        progress_callback(step_msg)
    world_with_puzzles = None
    for attempt in range(1, max_attempts + 1):
        world_with_puzzles = run_step_4_puzzles(world_basic, language)
        json_ok = verify_pydantic_model(world_with_puzzles, GeneratedWorld)
        if json_ok:
            break
        else:
            print(f"[WARNING] Puzzles verification failed on attempt {attempt}. Retrying...")
            if progress_callback:
                progress_callback(f"[WARNING] Puzzles verification failed on attempt {attempt}. Retrying...")
            world_with_puzzles = None
    if world_with_puzzles is None:
        raise ValueError("Failed to generate valid puzzles after multiple attempts.")
    completion_msg = f"✅ Puzzles añadidos: {len(world_with_puzzles.puzzles)} puzzles en total"
    print(completion_msg)
    if progress_callback:
        progress_callback(completion_msg)

    # Paso 5: Expandir con contenido opcional (with verification)
    step_msg = "🎨 Paso 5: Expandiendo con contenido adicional..."
    print(step_msg)
    if progress_callback:
        progress_callback(step_msg)
    final_world = None
    for attempt in range(1, max_attempts + 1):
        final_world = run_step_5_expansion(world_with_puzzles, language)
        json_ok = verify_pydantic_model(final_world, GeneratedWorld)
        if json_ok:
            break
        else:
            print(f"[WARNING] Expansion verification failed on attempt {attempt}. Retrying...")
            if progress_callback:
                progress_callback(f"[WARNING] Expansion verification failed on attempt {attempt}. Retrying...")
            final_world = None
    if final_world is None:
        raise ValueError("Failed to generate valid expansion after multiple attempts.")
    completion_msg = f"✅ Expansión completada: mundo final con {len(final_world.locations)} ubicaciones"
    print(completion_msg)
    if progress_callback:
        progress_callback(completion_msg)
    
    final_msg = "🌱 ¡Generación incremental completada exitosamente!"
    print(final_msg)
    if not validate_world_size(final_world):
        print("The generated world does not meet the size requirements.")
    if progress_callback:
        progress_callback(final_msg)
    return final_world

def create_world_incrementally_generate(language: str, progress_callback=None) -> GeneratedWorld:
    """
    Orchestrator for incremental generation pipeline in 'generate' mode.
    Uses run_step_1_generate_concept instead of run_step_1_concept.
    Args:
        language: Language for generation
        progress_callback: Optional function to call with progress updates
    Returns:
        GeneratedWorld: Fully generated and validated world
    """
    print(f"⚙️ Iniciando generación incremental del mundo en modo 'generate'")

    # Paso 1: Generar el concepto general
    step_msg = "📝 Paso 1: Generando concepto del mundo..."
    print(step_msg)
    if progress_callback:
        progress_callback(step_msg)
    concept = run_step_1_generate_concept(language)
    completion_msg = f"✅ Concepto creado: '{concept.title}'"
    print(completion_msg)
    if progress_callback:
        progress_callback(completion_msg)

    # Paso 2: Crear el esqueleto con entidades clave
    step_msg = "🦴 Paso 2: Creando esqueleto del mundo..."
    print(step_msg)
    if progress_callback:
        progress_callback(step_msg)
    max_attempts = 3
    skeleton = None
    for attempt in range(1, max_attempts + 1):
        skeleton = run_step_2_skeleton(concept, language)
        # Verify skeleton sizes
        valid_locations = hasattr(skeleton, 'key_locations') and skeleton.key_locations and isinstance(skeleton.key_locations, list)
        valid_items = hasattr(skeleton, 'key_items') and skeleton.key_items and isinstance(skeleton.key_items, list)
        valid_characters = hasattr(skeleton, 'key_characters') and skeleton.key_characters and isinstance(skeleton.key_characters, list)
        config = configparser.ConfigParser()
        config.read('config.ini')
        def parse_range(value):
            if '-' in value:
                return tuple(map(int, value.split('-')))
            return int(value), int(value)
        locations_range = parse_range(config['Size_World']['Locations'])
        objects_range = parse_range(config['Size_World']['Objects'])
        npcs_range = parse_range(config['Size_World']['NPCs'])
        size_ok = (
            valid_locations and locations_range[0] <= len(skeleton.key_locations) <= locations_range[1] and
            valid_items and objects_range[0] <= len(skeleton.key_items) <= objects_range[1] and
            valid_characters and npcs_range[0] <= len(skeleton.key_characters) <= npcs_range[1]
        )
        json_ok = verify_pydantic_model(skeleton, WorldSkeleton)
        if size_ok and json_ok:
            break
        else:
            print(f"[WARNING] Skeleton verification failed on attempt {attempt}. Retrying...")
            if progress_callback:
                progress_callback(f"[WARNING] Skeleton verification failed on attempt {attempt}. Retrying...")
            skeleton = None
    if skeleton is None:
        raise ValueError("Failed to generate a valid skeleton after multiple attempts.")
    completion_msg = f"✅ Esqueleto creado con {len(skeleton.key_locations)} ubicaciones, {len(skeleton.key_items)} objetos y {len(skeleton.key_characters)} personajes"
    print(completion_msg)
    if progress_callback:
        progress_callback(completion_msg)

    # Paso 3: Desarrollar detalles y conexiones
    step_msg = "🌍 Paso 3: Desarrollando detalles y conexiones..."
    print(step_msg)
    if progress_callback:
        progress_callback(step_msg)
    world_basic = run_step_3_details(concept, skeleton, language)
    completion_msg = f"✅ Mundo base creado con {len(world_basic.locations)} ubicaciones y {len(world_basic.items)} objetos"
    print(completion_msg)
    if progress_callback:
        progress_callback(completion_msg)

    # Paso 4: Añadir puzzles y obstáculos
    step_msg = "🧩 Paso 4: Añadiendo puzzles y obstáculos..."
    print(step_msg)
    if progress_callback:
        progress_callback(step_msg)
    final_world = run_step_4_puzzles(world_basic, language)
    completion_msg = f"✅ Puzzles añadidos: {len(final_world.puzzles)} puzzles en total"
    print(completion_msg)
    if progress_callback:
        progress_callback(completion_msg)

    # Paso 5: Expandir con contenido opcional
    # step_msg = "🎨 Paso 5: Expandiendo con contenido adicional..."
    # print(step_msg)
    # if progress_callback:
    #     progress_callback(step_msg)
    # final_world = run_step_5_expansion(world_with_puzzles, language)
    # completion_msg = f"✅ Expansión completada: mundo final con {len(final_world.locations)} ubicaciones"
    # print(completion_msg)
    # if progress_callback:
    #     progress_callback(completion_msg)

    final_msg = "🌱 ¡Generación incremental completada exitosamente!"
    print(final_msg)
    if not validate_world_size(final_world):
        print("The generated world does not meet the size requirements.")
    if progress_callback:
        progress_callback(final_msg)
    return final_world

def validate_world_size(generated_world: GeneratedWorld) -> bool:
    """Validate if the generated world adheres to the size parameters in config.ini."""
    # Load configuration
    config = configparser.ConfigParser()
    config.read('config.ini')

    # Parse size parameters
    def parse_range(value):
        if '-' in value:
            return tuple(map(int, value.split('-')))
        return int(value), int(value)

    locations_range = parse_range(config['Size_World']['Locations'])
    objects_range = parse_range(config['Size_World']['Objects'])
    npcs_range = parse_range(config['Size_World']['NPCs'])
    puzzles_range = parse_range(config['Size_World']['Puzzles'])

    # Validate the generated world
    is_valid = (
        locations_range[0] <= len(generated_world.locations) <= locations_range[1] and
        objects_range[0] <= len(generated_world.items) <= objects_range[1] and
        npcs_range[0] <= len(generated_world.characters) <= npcs_range[1] and
        puzzles_range[0] <= len(generated_world.puzzles) <= puzzles_range[1]
    )

    if not is_valid:
        print("[ERROR] Generated world does not adhere to size parameters:")
        print(f"  Locations: {len(generated_world.locations)} (Expected: {locations_range})")
        print(f"  Objects: {len(generated_world.items)} (Expected: {objects_range})")
        print(f"  NPCs: {len(generated_world.characters)} (Expected: {npcs_range})")
        print(f"  Puzzles: {len(generated_world.puzzles)} (Expected: {puzzles_range})")

    return is_valid

def verify_pydantic_model(obj, model_class):
    """Verify that obj is a valid instance of model_class and can be parsed from dict/json."""
    try:
        if isinstance(obj, model_class):
            return True
        if isinstance(obj, dict):
            model_class.model_validate(obj)
            return True
        if hasattr(obj, 'model_dump'):  # Pydantic v2
            model_class.model_validate(obj.model_dump())
            return True
    except Exception as e:
        print(f"[ERROR] Model verification failed: {e}")
        return False
    return False

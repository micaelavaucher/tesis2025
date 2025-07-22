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

#---- Pipeline Functions -----------------------------------------------------

def run_step_1_concept(theme: str) -> WorldConcept:
    """
    Generation of the general concept of the world.
    
    Args:
        theme: Base theme or concept for the world 
        
    Returns:
        WorldConcept: Validated object with the concept of the world
    """
    model = get_llm()
    prompt_text = prompts.PROMPT_STEP_1_CONCEPT.format(theme=theme)
    
    # Llamar al modelo con el esquema WorldConcept
    concept_response = model.prompt_model_structured(prompt_text, WorldConcept)
    
    if isinstance(concept_response, dict):
        return WorldConcept(**concept_response)
    else:
        return concept_response

def run_step_2_skeleton(concept: WorldConcept) -> WorldSkeleton:
    """
    Generation of the skeleton with key entities.
    
    Args:
        concept: World's concept from step from the previous step
        
    Returns:
        WorldSkeleton: Validated object with the key entities
    """
    model = get_llm()
    prompt_text = prompts.PROMPT_STEP_2_SKELETON.format(
        title=concept.title,
        backstory=concept.backstory,
        player_concept=concept.player_concept,
        main_objective=concept.main_objective
    )
    
    skeleton_response = model.prompt_model_structured(prompt_text, WorldSkeleton)
    
    if isinstance(skeleton_response, dict):
        return WorldSkeleton(**skeleton_response)
    else:
        return skeleton_response

def run_step_3_details(concept: WorldConcept, skeleton: WorldSkeleton) -> GeneratedWorld:
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
    
    prompt_text = prompts.PROMPT_STEP_3_DETAILS.format(
        title=concept.title,
        backstory=concept.backstory,
        player_concept=concept.player_concept,
        main_objective=concept.main_objective,
        skeleton_data=skeleton_data
    )
    
    world_response = model.prompt_model_structured(prompt_text, GeneratedWorld)
    
    if isinstance(world_response, dict):
        return GeneratedWorld(**world_response)
    else:
        return world_response

def run_step_4_puzzles(world_data: GeneratedWorld) -> GeneratedWorld:
    """
    Generation of dependency chains with integrated puzzles.
    
    Args:
        world_data: World from the previous step
        
    Returns:
        GeneratedWorld: Modified object with complex dependency chains
    """
    model = get_llm()
    
    world_json = world_data.model_dump_json(indent=2)
    
    prompt_text = prompts.PROMPT_STEP_4_PUZZLES.format(
        world_data=world_json
    )
    
    enhanced_world_response = model.prompt_model_structured(prompt_text, GeneratedWorld)
    
    if isinstance(enhanced_world_response, dict):
        return GeneratedWorld(**enhanced_world_response)
    else:
        return enhanced_world_response

def run_step_5_expansion(world_data: GeneratedWorld) -> GeneratedWorld:
    """
    Paso 5: Expansion with optional content.
    
    Args:
        world_data: World from the previous step
        
    Returns:
        GeneratedWorld: Final and complete object
    """
    model = get_llm()
    
    world_json = world_data.model_dump_json(indent=2)
    
    prompt_text = prompts.PROMPT_STEP_5_EXPANSION.format(
        world_data=world_json
    )
    
    final_world_response = model.prompt_model_structured(prompt_text, GeneratedWorld)
    
    if isinstance(final_world_response, dict):
        return GeneratedWorld(**final_world_response)
    else:
        return final_world_response

def create_world_incrementally(theme: str, progress_callback=None) -> GeneratedWorld:
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
    concept = run_step_1_concept(theme)
    completion_msg = f"✅ Concepto creado: '{concept.title}'"
    print(completion_msg)
    if progress_callback:
        progress_callback(completion_msg)
    
    # Paso 2: Crear el esqueleto con entidades clave
    step_msg = "🦴 Paso 2: Creando esqueleto del mundo..."
    print(step_msg)
    if progress_callback:
        progress_callback(step_msg)
    skeleton = run_step_2_skeleton(concept)
    completion_msg = f"✅ Esqueleto creado con {len(skeleton.key_locations)} ubicaciones, {len(skeleton.key_items)} objetos y {len(skeleton.key_characters)} personajes"
    print(completion_msg)
    if progress_callback:
        progress_callback(completion_msg)
    
    # Paso 3: Desarrollar detalles y conexiones
    step_msg = "🌍 Paso 3: Desarrollando detalles y conexiones..."
    print(step_msg)
    if progress_callback:
        progress_callback(step_msg)
    world_basic = run_step_3_details(concept, skeleton)
    completion_msg = f"✅ Mundo base creado con {len(world_basic.locations)} ubicaciones y {len(world_basic.items)} objetos"
    print(completion_msg)
    if progress_callback:
        progress_callback(completion_msg)
    
    # Paso 4: Crear cadenas de dependencias complejas
    step_msg = "🔗 Paso 4: Creando cadenas de dependencias..."
    print(step_msg)
    if progress_callback:
        progress_callback(step_msg)
    world_with_puzzles = run_step_4_puzzles(world_basic)
    completion_msg = f"✅ Cadenas de dependencias creadas: {len(world_with_puzzles.puzzles)} puzzles interconectados"
    print(completion_msg)
    if progress_callback:
        progress_callback(completion_msg)
    
    # Paso 5: Expandir con contenido opcional
    step_msg = "🎨 Paso 5: Expandiendo con contenido adicional..."
    print(step_msg)
    if progress_callback:
        progress_callback(step_msg)
    final_world = run_step_5_expansion(world_with_puzzles)
    completion_msg = f"✅ Expansión completada: mundo final con {len(final_world.locations)} ubicaciones"
    print(completion_msg)
    if progress_callback:
        progress_callback(completion_msg)
    
    final_msg = "🌱 ¡Generación incremental completada exitosamente!"
    print(final_msg)
    if progress_callback:
        progress_callback(final_msg)
    return final_world

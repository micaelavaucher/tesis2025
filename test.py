"""Test script to validate the structured data models with the turtle world example."""

# ----------------------------------------- #
# Imports and Configs                       #
# ----------------------------------------- #
import traceback
from pydantic import ValidationError
import configparser

# Import our modules
from structured_data_models import (
    GeneratedWorld, 
    ObjectiveType,
    ComponentType,
    RequirementType,
)
from world_builder import create_world_from_llm_response, inspect_generated_world
from models import get_llm

# ----------------------------------------- #
# Custom exceptions for validation          #
# ----------------------------------------- #
class SemanticError(Exception):
    """Exception raised when semantic connections are invalid."""
    pass

class PlayabilityError(Exception):
    """Exception raised when the world is not playable."""
    pass

# ----------------------------------------- #
# Validation functions                      #
# ----------------------------------------- #
def validate_semantic_connections(generated_world: GeneratedWorld) -> None:
    """Validate that all world elements are semantically connected to the objective."""
    print("🔍 Validando conexiones semánticas...")
    
    errors = []
    
    # Check that all items have relevance or are decorative
    for item in generated_world.items:
        if item.relevance_to_objective is None and item.required_for == []:
            # It's okay if it's clearly decorative, but should be specified
            print(f"⚠️  Item '{item.name}' no tiene relevancia ni es requerido - ¿es decorativo?")
    
    # Check that all locations have relevance or are just connectors
    for location in generated_world.locations:
        if location.relevance_to_objective is None:
            print(f"⚠️  Location '{location.name}' no tiene relevancia al objetivo")
    
    # Check that puzzles have meaningful rewards
    for puzzle in generated_world.puzzles:
        if not puzzle.rewards:
            errors.append(f"Puzzle '{puzzle.name}' no tiene recompensas definidas")
        
        if not puzzle.relevance_to_objective:
            errors.append(f"Puzzle '{puzzle.name}' no tiene relevancia al objetivo")
    
    # Check that characters with interactions have clear purpose
    for character in generated_world.characters:
        if character.interaction:
            if not character.interaction.relevance_to_objective:
                errors.append(f"Character '{character.name}' tiene interacción pero sin relevancia al objetivo")
            
            # Check that they give something or provide information
            if not character.interaction.gives_item and not character.interaction.gives_information:
                errors.append(f"Character '{character.name}' tiene interacción pero no da nada útil")
    
    # Check that blocked passages have clear reasons
    for location in generated_world.locations:
        for blocked in location.blocked_passages:
            if not blocked.relevance_to_objective:
                errors.append(f"Blocked passage to '{blocked.location}' from '{location.name}' sin relevancia al objetivo")
    
    # Check dependency chains make sense
    if not generated_world.dependency_chains:
        errors.append("No hay cadenas de dependencias definidas")
    else:
        for chain in generated_world.dependency_chains:
            if len(chain.steps) < 2:
                errors.append(f"Dependency chain '{chain.chain_description}' tiene muy pocos pasos")
    
    if errors:
        raise SemanticError(f"Errores semánticos encontrados:\n" + "\n".join(f"- {error}" for error in errors))
    
    print("✅ Conexiones semánticas válidas!")

def validate_playability(generated_world: GeneratedWorld) -> None:
    """Validate that the world is actually playable - objective can be reached."""
    print("🎮 Validando jugabilidad...")
    
    errors = []
    
    # Check that objective components exist
    objective = generated_world.objective
    if not objective:
        errors.append("No hay objetivo definido")
        raise PlayabilityError("No hay objetivo definido")
    
    # Create dictionaries for easier lookup
    items_dict = {item.name: item for item in generated_world.items}
    locations_dict = {loc.name: loc for loc in generated_world.locations}
    characters_dict = {char.name: char for char in generated_world.characters}
    puzzles_dict = {puzzle.name: puzzle for puzzle in generated_world.puzzles}
    
    # Check objective components exist
    for component in objective.components:
        if component.component_type == ComponentType.ITEM:
            if component.name not in items_dict:
                errors.append(f"Objetivo requiere item '{component.name}' que no existe")
        elif component.component_type == ComponentType.LOCATION:
            if component.name not in locations_dict:
                errors.append(f"Objetivo requiere location '{component.name}' que no existe")
        elif component.component_type == ComponentType.CHARACTER:
            if component.name not in characters_dict:
                errors.append(f"Objetivo requiere character '{component.name}' que no existe")
    
    # Check that player can reach objective location (if applicable)
    if objective.type in [ObjectiveType.GET_ITEM, ObjectiveType.REACH_LOCATION]:
        # Find where the objective item/location is
        target_location = None
        
        if objective.type == ObjectiveType.GET_ITEM:
            # Find which location has the target item
            target_item_name = None
            for component in objective.components:
                if component.component_type == ComponentType.ITEM:
                    target_item_name = component.name
                    break
            
            if target_item_name:
                for location in generated_world.locations:
                    if target_item_name in location.items:
                        target_location = location.name
                        break
        
        elif objective.type == ObjectiveType.REACH_LOCATION:
            for component in objective.components:
                if component.component_type == ComponentType.LOCATION:
                    target_location = component.name
                    break
        
        # Check if target location is reachable
        if target_location:
            reachable = check_location_reachability(
                start_location=generated_world.player.location,
                target_location=target_location,
                generated_world=generated_world
            )
            
            if not reachable:
                errors.append(f"Location '{target_location}' no es alcanzable desde '{generated_world.player.location}'")
    
    # Check that required items for blocked passages can be obtained
    for location in generated_world.locations:
        for blocked in location.blocked_passages:
            req = blocked.required_to_unblock
            
            if req.requirement_type == RequirementType.ITEM:
                # Check if item exists and is gettable
                if req.item_name not in items_dict:
                    errors.append(f"Blocked passage requiere item '{req.item_name}' que no existe")
                elif not items_dict[req.item_name].gettable:
                    errors.append(f"Blocked passage requiere item '{req.item_name}' que no es obtenible")
            
            elif req.requirement_type == RequirementType.PUZZLE:
                # Check if puzzle exists
                if req.puzzle_name not in puzzles_dict:
                    errors.append(f"Blocked passage requiere puzzle '{req.puzzle_name}' que no existe")
    
    if errors:
        raise PlayabilityError(f"Errores de jugabilidad encontrados:\n" + "\n".join(f"- {error}" for error in errors))
    
    print("✅ Mundo jugable!")

def check_location_reachability(start_location: str, target_location: str, generated_world: GeneratedWorld) -> bool:
    """Check if target location is reachable from start location."""
    if start_location == target_location:
        return True
    
    # Build location graph
    locations_dict = {loc.name: loc for loc in generated_world.locations}
    
    # BFS to find path
    visited = set()
    queue = [start_location]
    
    while queue:
        current = queue.pop(0)
        if current == target_location:
            return True
        
        if current in visited:
            continue
        
        visited.add(current)
        
        if current in locations_dict:
            location = locations_dict[current]
            
            # Add connected locations
            for connected in location.connecting_locations:
                if connected not in visited:
                    queue.append(connected)
            
            # Add blocked locations (assuming they can be unblocked)
            for blocked in location.blocked_passages:
                if blocked.location not in visited:
                    queue.append(blocked.location)
    
    return False

# ----------------------------------------- #
# Test prompt function                      #
# ----------------------------------------- #
def prompt_generate_turtle_world_validation(language: str = 'es') -> str:
    """Generate a prompt for creating the turtle world to validate structured data models."""
    return """Crea un mundo estructurado basado en esta historia específica:

**HISTORIA: "El Rescate de Hojita"**

Emma es una adolescente que busca a su mascota tortuga llamada "Hojita" que está perdida en el jardín de su casa. Para llegar al jardín debe pasar por la cocina, pero hay un candado que bloquea la puerta hacia el jardín.

**ESTRUCTURA ESPECÍFICA REQUERIDA:**

**UBICACIONES (3):**
- Taller de pintura: Donde Emma comienza, con su madre Laura
- Cocina: Conecta el taller con el jardín, PERO la puerta al jardín está bloqueada por un candado
- Jardín: Donde está Hojita la tortuga (objetivo final)

**OBJETIVO PRINCIPAL:**
- Tipo: GET_ITEM
- Descripción: "Emma debe rescatar a su tortuga Hojita del jardín"
- Componentes: Tortuga (item) en Jardín (location)

**PERSONAJES (2):**
- Emma (jugador): Adolescente, inventario vacío, ubicación inicial = Taller de pintura
- Laura (madre): Artista, tiene la llave dorada, ubicación = Taller de pintura
- Laura DEBE requerir algo para dar la llave (ej: que Emma complete un puzzle o le traiga algo)

**OBJETOS REQUERIDOS:**
- Tortuga "Hojita": En el jardín (objetivo principal)
- Llave dorada: Con Laura, necesaria para abrir el candado
- Candado: Bloqueando el paso de Cocina → Jardín
- Martillo gris: En el taller, útil para romper el candado (alternativa)
- Martillo verde: En el taller, es solo decorativo (juguete inútil)

**CONEXIONES SEMÁNTICAS OBLIGATORIAS:**
1. Para llegar al jardín → necesitas abrir el candado
2. Para abrir el candado → necesitas la llave dorada O romperlo con el martillo gris
3. Para conseguir la llave → debes cumplir el requisito de Laura
4. Laura debe pedir algo razonable (resolver puzzle, traer objeto, etc.)

**CADENA DE DEPENDENCIAS EJEMPLO:**
1. Emma quiere rescatar a Hojita del jardín
2. El jardín está bloqueado por un candado en la cocina
3. Laura tiene la llave, pero necesita que Emma [DEFINE TÚ QUÉ]
4. Emma cumple el requisito de Laura
5. Laura le da la llave
6. Emma abre el candado y rescata a Hojita

**VALIDACIONES CRÍTICAS:**
- TODOS los elementos deben tener relevance_to_objective explicado
- Los puzzles deben tener rewards específicos y tipos definidos
- Los personajes con interaction deben tener requires claros
- Las dependency_chains deben ser lógicas y completas
- Los blocked_passages deben tener requisitos específicos

**CREATIVIDAD PERMITIDA:**
- Define qué requiere Laura exactamente
- Agrega un puzzle si es necesario
- Mejora las descripciones
- Añade detalles narrativos coherentes

Genera el JSON completo siguiendo el schema de GeneratedWorld. Asegúrate de que TODO esté semánticamente conectado al objetivo de rescatar a Hojita."""

# ----------------------------------------- #
# Main test execution                       #
# ----------------------------------------- #
def run_turtle_world_test():
    """Run the complete turtle world validation test."""
    print("🐢 **INICIANDO TEST DEL MUNDO DE LA TORTUGA** 🐢\n")
    
    # Configurar modelo igual que en app.py
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    reasoning_model_name = config['Models']['ReasoningModel']
    model = get_llm(reasoning_model_name)
    
    # Test completo del sistema
    test_prompt = prompt_generate_turtle_world_validation(language='es')
    
    try:
        print("📝 Generando mundo con LLM...")
        
        # 1. Generar mundo usando structured output
        llm_response = model.prompt_model_structured(test_prompt, GeneratedWorld)
        
        print("✅ Respuesta del LLM recibida!")
        print(f"📏 Tipo de respuesta: {type(llm_response)}\n")
        
        # 2. Validar estructura
        print("🔧 Validando estructura...")
        if isinstance(llm_response, dict):
            generated_world = GeneratedWorld.model_validate(llm_response)
        else:
            generated_world = llm_response  # Ya es un objeto GeneratedWorld
        print("✅ Estructura válida!")
        
        # 3. Validar semántica
        validate_semantic_connections(generated_world)
        
        # 4. Validar jugabilidad  
        validate_playability(generated_world)
        
        # 5. Crear mundo funcional
        print("🌍 Creando mundo funcional...")
        world = create_world_from_llm_response(llm_response)
        print("✅ Mundo creado exitosamente!")
        
        # 6. Inspeccionar mundo
        print("\n" + "="*50)
        print(inspect_generated_world(world, language='es'))
        print("="*50)
        
        print("\n🎉 **TEST COMPLETADO EXITOSAMENTE** 🎉")
        print("✅ El LLM puede generar mundos estructurados válidos")
        print("✅ Las conexiones semánticas funcionan correctamente")
        print("✅ El mundo es jugable")
        
        return world, generated_world
        
    except ValidationError as e:
        print(f"❌ **Error de estructura:** {e}")
        print("\n📋 **Detalles del error:**")
        print(str(e))
        return None, None
        
    except SemanticError as e:
        print(f"❌ **Error semántico:** {e}")
        return None, None
        
    except PlayabilityError as e:
        print(f"❌ **Error de jugabilidad:** {e}")
        return None, None
        
    except Exception as e:
        print(f"❌ **Error inesperado:** {e}")
        print("\n📋 **Stack trace:**")
        traceback.print_exc()
        return None, None

def run_simple_validation_test():
    """Run a simpler test with manual JSON data."""
    print("🧪 **TEST SIMPLE DE VALIDACIÓN** 🧪\n")
    
    # Create a simple test world manually
    test_world_json = {
        "locations": [
            {
                "name": "Taller de pintura",
                "descriptions": ["Un taller lleno de pinceles y pinturas"],
                "items": ["Martillo gris", "Martillo verde"],
                "connecting_locations": ["Cocina"],
                "blocked_passages": [],
                "relevance_to_objective": "Lugar inicial donde Emma comienza su búsqueda"
            },
            {
                "name": "Cocina", 
                "descriptions": ["La cocina de la casa"],
                "items": [],
                "connecting_locations": ["Taller de pintura"],
                "blocked_passages": [
                    {
                        "location": "Jardín",
                        "obstacle_description": "Un candado fuerte bloquea la puerta",
                        "required_to_unblock": {
                            "requirement_type": "ITEM",
                            "item_name": "Llave dorada",
                            "description": "Necesitas la llave dorada para abrir el candado"
                        },
                        "relevance_to_objective": "El jardín contiene a Hojita, la tortuga objetivo"
                    }
                ],
                "relevance_to_objective": "Pasaje necesario para llegar al jardín"
            },
            {
                "name": "Jardín",
                "descriptions": ["El jardín donde está perdida Hojita"],
                "items": ["Hojita"],
                "connecting_locations": ["Cocina"],
                "blocked_passages": [],
                "relevance_to_objective": "Ubicación de Hojita, la tortuga objetivo"
            }
        ],
        "items": [
            {
                "name": "Hojita",
                "descriptions": ["Una tortuga pequeña y adorable", "La mascota perdida de Emma"],
                "gettable": True,
                "relevance_to_objective": "Es el objetivo principal del juego",
                "required_for": []
            },
            {
                "name": "Llave dorada",
                "descriptions": ["Una llave dorada brillante"],
                "gettable": True,
                "relevance_to_objective": "Necesaria para abrir el candado que bloquea el jardín",
                "required_for": ["Candado"]
            },
            {
                "name": "Martillo gris",
                "descriptions": ["Un martillo pesado y resistente"],
                "gettable": True,
                "relevance_to_objective": "Alternativa para romper el candado",
                "required_for": ["Candado"]
            },
            {
                "name": "Martillo verde",
                "descriptions": ["Un martillo de juguete verde"],
                "gettable": True,
                "relevance_to_objective": None,
                "required_for": []
            }
        ],
        "characters": [
            {
                "name": "Laura",
                "descriptions": ["La madre artista de Emma"],
                "location": "Taller de pintura",
                "inventory": ["Llave dorada"],
                "interaction": {
                    "gives_information": None,
                    "gives_item": "Llave dorada",
                    "requires": [
                        {
                            "requirement_type": "ITEM",
                            "item_name": "Martillo verde",
                            "description": "Laura quiere que Emma le traiga el martillo verde como prueba de confianza"
                        }
                    ],
                    "relevance_to_objective": "Tiene la llave necesaria para acceder al jardín donde está Hojita"
                }
            }
        ],
        "puzzles": [],
        "player": {
            "name": "Emma",
            "descriptions": ["Una adolescente preocupada por su mascota"],
            "location": "Taller de pintura",
            "inventory": [],
            "interaction": None
        },
        "objective": {
            "type": "GET_ITEM",
            "components": [
                {
                    "name": "Hojita",
                    "component_type": "ITEM",
                    "role_in_objective": "La tortuga que Emma debe rescatar"
                }
            ],
            "description": "Emma debe rescatar a su tortuga Hojita del jardín",
            "success_conditions": ["Emma debe tener a Hojita en su inventario"]
        },
        "dependency_chains": [
            {
                "chain_description": "Cadena principal para rescatar a Hojita",
                "steps": [
                    "Emma toma el martillo verde del taller",
                    "Emma le da el martillo verde a Laura",
                    "Laura le da la llave dorada a Emma",
                    "Emma va a la cocina y usa la llave para abrir el candado",
                    "Emma entra al jardín y rescata a Hojita"
                ],
                "elements_involved": ["Emma", "Laura", "Martillo verde", "Llave dorada", "Hojita", "Jardín"]
            }
        ],
        "world_theme": "Aventura doméstica de rescate de mascotas",
        "narrative_context": "Emma debe usar su ingenio y la ayuda de su madre para rescatar a su querida tortuga Hojita del jardín de su casa."
    }
    
    try:
        print("🔧 Validando estructura del mundo de prueba...")
        generated_world = GeneratedWorld.model_validate(test_world_json)
        print("✅ Estructura válida!")
        
        print("🔍 Validando conexiones semánticas...")
        validate_semantic_connections(generated_world)
        
        print("🎮 Validando jugabilidad...")
        validate_playability(generated_world)
        
        print("🌍 Creando mundo funcional...")
        world = create_world_from_llm_response(test_world_json)
        print("✅ Mundo creado exitosamente!")
        
        print("\n" + "="*50)
        print(inspect_generated_world(world, language='es'))
        print("="*50)
        
        print("\n🎉 **TEST SIMPLE COMPLETADO EXITOSAMENTE** 🎉")
        
        return world, generated_world
        
    except Exception as e:
        print(f"❌ **Error en test simple:** {e}")
        traceback.print_exc()
        return None, None

# ----------------------------------------- #
# Execute tests                             #
# ----------------------------------------- #
if __name__ == "__main__":
    print("🚀 **INICIANDO TESTS DE VALIDACIÓN** 🚀\n")
    
    # Run simple test first
    print("1️⃣ Ejecutando test simple...")
    simple_world, simple_generated = run_simple_validation_test()
    
    print("\n" + "="*60 + "\n")
    
    # Run full LLM test - ahora habilitado
    print("2️⃣ Ejecutando test completo con LLM...")
    llm_world, llm_generated = run_turtle_world_test()
    
    print("✅ **TESTS COMPLETADOS** ✅")
from structured_data_models import WorldUpdate

def prompt_describe_objective (objective, language:str = 'en'):
    system_msg = ""
    user_msg = ""

    if language == 'es':
        system_msg, user_msg = prompt_describe_objective_spanish(objective)
    else:
        system_msg, user_msg = prompt_describe_objective_english(objective)
    
    return system_msg, user_msg 

def prompt_describe_objective_english (objective):

    system_msg = """You have to provide an alternative way to narrate the objective given to you. You should always use simple language. 
    
    Always put your generated narration between # characters. For example: # You have to get the <key> # or # You have to reach the <castle> #"""

    first_component_class = objective[0].__class__.__name__
    second_component_class = objective[1].__class__.__name__
    user_msg = ""

    if first_component_class == "Character" and second_component_class == "Location":
        user_msg =  f'The objective to narrate in an alterative way is "You have to go to <{objective[1].name}>."'
    elif first_component_class == "Character" and second_component_class == "Item":
        user_msg = f'The objective to narrate in an alterative way is "<{objective[0].name}> has to get the item <{objective[1].name}>."'
    elif first_component_class == "Item" and second_component_class == "Location":
        user_msg = f'The objective to narrate in an alterative way is "You have to leave item <{objective[0].name}> in place <{objective[1].name}>."'
    elif first_component_class == "Character" and second_component_class == "Character":
        user_msg = f'The objective to narrate in an alterative way is "<{objective[0].name}> has to find <{objective[1].name}>."'

    return system_msg, user_msg 

def prompt_describe_objective_spanish (objective):

    system_msg = """Tienes que dar una forma alternativa de narrar el objetivo que se te dará. Siempre usa lenguaje simple. 
    
    Pon siempre tu narración generada entre caracteres #. Por ejemplo: # Tienes que conseguir la <llave> # o # Tienes que llegaral <Castillo> #"""

    first_component_class = objective[0].__class__.__name__
    second_component_class = objective[1].__class__.__name__
    user_msg = ""

    if first_component_class == "Character" and second_component_class == "Location":
        user_msg = f'El objetivo a decir de forma alternativa es "Tienes que ir a <{objective[1].name}>."'
    elif first_component_class == "Character" and second_component_class == "Item":
        user_msg = f'El objetivo a decir de forma alternativa es "<{objective[0].name}> tiene que conseguir el objeto <{objective[1].name}>."'
    elif first_component_class == "Item" and second_component_class == "Location":
        user_msg = f'El objetivo a decir de forma alternativa es "Tienes que dejar el objeto <{objective[0].name}> en el lugar <{objective[1].name}>."'
    elif first_component_class == "Character" and second_component_class == "Character":
        user_msg = f'El objetivo a decir de forma alternativa es "<{objective[0].name}> tiene que encontrar a <{objective[1].name}>."'

    return system_msg, user_msg

def prompt_narrate_current_scene (world_state: str, previous_narrations: 'list[str]', language: str = 'en', starting_scene: bool = False):
    system_msg = ""
    user_msg = ""

    if language == 'es':
        system_msg, user_msg = prompt_narrate_current_scene_spanish(world_state, previous_narrations, starting_scene)
    else:
        system_msg, user_msg = prompt_narrate_current_scene_english(world_state, previous_narrations, starting_scene)


    return system_msg, user_msg

def prompt_narrate_current_scene_english (world_state: str, previous_narrations: 'list[str]', starting_scene: bool = False):

    system_msg = "You are a storyteller. Take the state of the world given to you and narrate it in a few sentences. Be careful not to include details that contradict the current state of the world or that move the story forward. Also, try to use simple sentences and do not overuse poetic language"
    
    if starting_scene:
        system_msg += "\nTake into account that this is the first scene in the story: introduce the main character, creating a small background story and why that character is in that specific location.\n"
    elif len(previous_narrations)==0:
        system_msg += "Take into account that the player already knows what the main character looks like, so do not mention anything about that. However, it is the first time the player visits this place, so make sure to describe it exhaustively."
    else:
        system_msg += "Take into account that the player already knows what the main character looks like, so do not mention anything about that. Additionally, it is not the first time the player visits this place. Next I’ll give you some previous narrations of this same location (from oldest to newest) so you can be sure to not repeat the same details again:\n"
        for narration in previous_narrations:
            system_msg+=f'- {narration}\n'

    system_msg+= "\nRemember: you are talking to the player, describing what his or her character has and what he or she can see or feel."

    user_msg =f"""This is the state of the world at the moment:
    {world_state}
    """

    return system_msg, user_msg

def prompt_narrate_current_scene_spanish (world_state: str, previous_narrations: 'list[str]', starting_scene: bool = False):
    
    system_msg = f"""Eres un narrador. Toma el estado del mundo que se te de y nárralo en unas pocas oraciones. Ten cuidado de no incluir detalles que contradigan el estado del mundo actual, o que hagan avanzar la historia. Además, si el jugador está en la misma ubicación en la que existe un puzzle, debes darle una pista que le haga saber que allí hay un puzzle, o que un personaje tiene un puzzle para él. Intenta usar oraciones simples, sin abusar del lenguaje poético."""
    
    if starting_scene:
        system_msg += "\nTen en cuenta que esta es la primera escena en la historia narrada: presenta al personaje del jugador, creando un pequeño trasfondo y por qué este personaje está en ese lugar específicamente. Puede usar las pequeñas descripciones presentes en el estado del mundo. Es importante que menciones todos los componentes que hay en este lugar. Sin embargo, es mejor si no describes cada componente: basta con que los menciones con una mínima descripción poco específica. Es muy importante que nombres los lugares a los que puede acceder el jugador desde esta posición. \n"
    elif len(previous_narrations)==0:
        system_msg += "Ten en cuenta que el jugador ya conoce a su personaje, y cómo se ve, así que no menciones nada sobre esto. Sin embargo, es la primera vez que el jugador visita este lugar, así que describelo. Es importante que menciones todos los componentes que hay en este lugar. Sin embargo, es mejor si no describes cada componente: basta con que los menciones con una mínima descripción poco específica. Es muy importante que nombres los lugares a los que puede acceder el jugador desde esta posición. \n"
    else:
        system_msg += "Ten en cuenta que el jugador ya conoce a su personaje, y cómo se ve, así que no menciones nada sobre esto. Además, no es la primera vez que el jugador visita este lugar. A continuación te daré algunas narraciones previas de este mismo lugar (de la más antigua a la más nueva), así te puedes asegurar de no repetir los mismos detalles de nuevo:\n"
        for narration in previous_narrations:
            system_msg+=f'- {narration}\n'

    system_msg+= "\nRecuerda: le estás hablando al jugador, describiendo lo que su personaje tiene y lo que puede sentir o ver."

    user_msg = f"""Este es el estado del mundo en este momento:
    {world_state}
    """

    return system_msg, user_msg

def prompt_world_update (world_state: str, input: str, language: str = 'en'):
    system_msg = ""
    user_msg = ""

    if language == 'es':
        system_msg, user_msg = prompt_world_update_spanish(world_state, input)
    else:
        system_msg, user_msg = prompt_world_update_english(world_state, input)


    return system_msg, user_msg

def prompt_world_update_structured(world_state: str, input: str, language: str = 'en'):
    """Create a world update prompt that will return structured data based on Pydantic models."""
    if language == 'es':
        system_msg = """Eres un narrador. Estás manejando un mundo ficticio, y el jugador puede interactuar con él. 
        Tu tarea es determinar los cambios en el mundo a raíz de las acciones del jugador.
        
        Debes considerar:
        - Objetos que cambiaron de lugar
        - Pasajes entre lugares que se desbloquearon
        - Si el jugador se movió de lugar
        - Una breve narración de los cambios"""
    else:
        system_msg = """You are a narrator. You are managing a fictional world, and the player can interact with it.
        Your task is to determine the changes in the world due to the player's actions.
        
        You should consider:
        - Objects that changed location
        - Passages between locations that were unblocked
        - If the player moved to a new location
        - A brief narration of the changes"""
    
    user_msg = f"""Determine the changes in the world based on the player's input "{input}" and the current world state:
    
    {world_state}"""
    
    return system_msg, user_msg, WorldUpdate

def prompt_world_update_spanish (world_state: str, input: str):
    system_msg = f"""Eres un narrador. Estás manejando un mundo ficticio, y el jugador puede interactuar con él. Siguiendo un formato específico, que voy a explicarte más abajo, tu tarea es encontrar los cambios en el mundo a raíz de las acciones del jugador. En específico, tendrás que encontrar qué objetos cambiaron de lugar, qué pasajes entre lugares se desbloquearon y si el jugador se movió de lugar.
    
    Aquí hay algunas aclaraciones:
    (A) Presta atención a a la descripción de los componentes y sus capacidades.
    (B) Si un pasaje está bloqueado, significa que el jugador debe desbloquearlo antes de poder acceder al lugar. Aunque el jugador te diga que va a acceder al lugar bloqueado, tienes que estar seguro de que está cumpliendo con lo pedido para permitirle desbloquear el acceso, por ejemplo usando una llave o resolviendo un puzzle.
    (C) **PERSONAJES CON REQUISITOS**: Si un personaje tiene requisitos específicos (como resolver un puzzle o tener ciertos objetos), NO debe dar objetos o ayudar hasta que esos requisitos se cumplan. Revisa cuidadosamente la sección de "interaction" de cada personaje y sus "requires".
    (D) No asumas que lo que dice el jugador siempre tiene sentido; quizás esas acciones intentan hacer algo que el mundo no lo permite.
    (E) **PUZZLES PROPUESTOS POR PERSONAJES**: Si un personaje propone un puzzle ("proposes_puzzle"), debe mencionarlo ANTES de dar cualquier recompensa. El jugador debe resolver el puzzle primero.
    (F) Sigue siempre el siguiente formato con las tres categorías, usando "None" en cada caso si no hay cambios y repite la categoría por cada caso:
    - Moved object: <object> now is in <new_location>
    - Blocked passages now available: <now_reachable_location>
    - Your location changed: <new_location>
    - Puzzle solved: <puzzle_name> with answer <answer> (solo si el jugador resolvió un puzzle)
    (G) Por último, puedes agregar una narración de los cambios detecados en el estado del mundo (¡sin hacer avanzar la historia y sin crear detalles no incluidos en el estado del mundo!) usando el formato: #tu mensaje final#
    (H) Dentro de la sección de narración que agregues al final, entre símbolos #, también puedes responder preguntas que haga el jugador en su entrada, sobre los objetos o personajes que puede ver, o el lugar en el que se encuentra.

    Aquí hay algunos ejemplos (con la aclaración entre paréntesis sobre qué podría haber intentado hacer el jugador) sobre el formato, descritos en los puntos (F) y (G):
    
    Ejemplo 1 (El jugador guarda el hacha en su inventario)
    - Moved object: <hacha> now is in <Inventory>
    - Blocked passages now available: None
    - Your location changed: None
    - Puzzle solved: None
    # Guardaste el hacha en tu bolso. Sientes la diferencia de peso luego de haberla guardado #

    Ejemplo 2 (El jugador desbloquea el pasaje al Sótano)
    - Moved object: None
    - Blocked passages now available: <Sótano>
    - Your location changed: None
    - Puzzle solved: None
    # El sótano, que estaba bloqueado, ahora está accesible #

    Ejemplo 3 (El jugador ahora está en el Jardín)
    - Moved object: None
    - Blocked passages now available: None
    - Your location changed: <Jardín>
    - Puzzle solved: None
    # Entras al Jardín #

    Ejemplo 4 (El jugador pide algo a un personaje que requiere resolver un puzzle primero)
    - Moved object: None
    - Blocked passages now available: None
    - Your location changed: None
    - Puzzle solved: None
    # Laura te mira con una sonrisa. "Antes de darte lo que necesitas, debes resolver mi puzzle de los pinceles. Si el pincel rojo se usa para detalles finos, el azul para fondos y el amarillo para iluminaciones, ¿en qué orden deberías usarlos para pintar un amanecer?" #

    Ejemplo 5 (El jugador resuelve correctamente un puzzle)
    - Moved object: <Llave dorada> now is in <Inventory>
    - Blocked passages now available: None
    - Your location changed: None
    - Puzzle solved: <Puzzle de los pinceles> with answer <azul, amarillo, rojo>
    # ¡Correcto! Laura sonríe orgullosa. "Exactamente, primero el azul para el fondo del cielo, luego el amarillo para la luz del amanecer, y finalmente el rojo para los detalles finos." Te entrega la llave dorada. #

    Ejemplo 6 (El jugador da una respuesta incorrecta a un puzzle)
    - Moved object: None
    - Blocked passages now available: None
    - Your location changed: None
    - Puzzle solved: None
    # Laura niega con la cabeza. "No, esa no es la respuesta correcta. Piénsalo mejor: ¿cómo pintarías un amanecer? ¿Qué va primero, el fondo o los detalles?" #

    Ejemplo 7 (El jugador intenta conseguir algo sin cumplir requisitos)
    - Moved object: None
    - Blocked passages now available: None
    - Your location changed: None
    - Puzzle solved: None
    # El personaje no puede ayudarte hasta que cumplas con lo que necesita #"""
    
    
    user_msg = f"""Expresa los cambios en el mundo siguiendo el formato pedido, teniendo en cuenta que el jugador ingresó esta entrada "{input}" a partir de este estado del mundo:
    
    {world_state}"""

    return system_msg, user_msg

def prompt_world_update_english (world_state: str, input: str):
    system_msg = f"""You are a storyteller. You are managing a fictional world, and the player can interact with it. Following a specific format, that I will specify below, your task is to find the changes in the world after the actions in the player input. Specifically, you will have to find what objects were moved, which previously blocked passages are now unblocked, and if the player moved to a new place.
       
    Here are some clarifications:
    (A) Pay attention  to the description of the components and their capabilities.
    (B) If a passage is blocked, then the player must unblock it before being able to reach the place. Even if the player tells you that he is going to access the locked location, you have to be sure that he is complying with what you asked to allow him to unlock the access, for example by using a key or solving a puzzle.
    (C) Do not assume that the player input always makes sense; maybe those actions try to do something that the world does not allow.
    (D) Follow always the following format with the three categories, using "None" in each case if there are no changes and repeat the category for each case:
    - Moved object: <object> now is in <new_location>
    - Blocked passages now available: <now_reachable_location>
    - Your location changed: <new_location>
    (E) Finally, you can narrate the changes you've detected in the world state (without moving the story forward and without making up details not included in the world state!) using the format: #your final message#
    (F) In the narration section that you add at the end, between # symbols, you can also answer questions that the player asks in their input, about the objects or characters they can see, or the place they are in.

    Here I give you some examples (in parentheses, a clarification about what the player might have tried to do) for the asked format, as described in items (D) and (E):

    Example 1 (The player took the axe and put it in the inventory)
    - Moved object: <axe> now is in <Inventory>
    - Blocked passages now available: None
    - Your location changed: None
    #You put the axe in your bag#

    Example 2 (The player unblocks the passage to the basement)
    - Moved object: None
    - Blocked passages now available: <Basement>
    - Your location changed: None
    # The basement is now reachable #

    Example 3 (The player now is in the garden)
    - Moved object: None
    - Blocked passages now available: None
    - Your location changed: <Garden>
    # You enter the garden #

    Example 4 (The player puts objects in the bag and leaves the axe on the floor)
    - Moved object: <banana> now is in <Inventory>,  <bottle> now is in <Inventory>,  <axe> now is in <Main Hall>
    - Blocked passages now available: None
    - Your location changed: None
    # You put the banana and the bottle in your bag. The axe lies on the floor of the Main hall #

    Example 5 (The player puts objects in the bag and leaves the axe on the floor and unblocks the passage to the Small room)
    - Moved object: <banana> now is in <Inventory>,  <bottle> now is in <Inventory>,  <axe> now is in <Main Hall>
    - Blocked passages now available: <Small room>
    - Your location changed: None
    # You put the banana and the bottle in your bag. The axe lies on the floor of the Main hall. Now you can reach the Small room. #

    Example 6 (The player puts objects in the bag and leaves the axe on the floor, unblocks the passage and goes to the Small room)
    - Moved object: <banana> now is in <Inventory>,  <bottle> now is in <Inventory>,  <axe> now is in <Main Hall>
    - Blocked passages now available: <Small room>
    - Your location changed:  <Small room>
    # You put the banana and the bottle in your bag. The axe lies on the floor of the Main hall. The Small room is now unblocked, and you moved there. #

    Example 7 (The player puts the pencil in the bag and gives the book to John)
    - Moved object: <book> now is in <John>,  <pencil> now is in <Inventory>
    - Blocked passages now available: None
    - Your location changed:  None
    # John now has the book. You put the pencil in your bag #

    Example 8 (The player gives the computer to Susan)
    - Moved object: <computer> now is in <Susan>
    - Blocked passages now available: None
    - Your location changed:  None
    # Susan put the computer in her bag #

    Example 9 (The player does something that has not the expected outcome)
    - Moved object: None
    - Blocked passages now available: None
    - Your location changed:  None
    # Nothing happened... #

    Example 10 (The player asks a question)
    - Moved object: None
    - Blocked passages now available: None
    - Your location changed:  None
    # Answer to the player's question #"""
    
    
    user_msg = f"""Give the changes in the world following the specified format, after this player input "{input}" on this world state:
    
    {world_state}"""

    return system_msg, user_msg

def prompt_generate_world(language: str = 'es') -> str:
    """Generate a prompt for creating a creative world with full LLM autonomy."""
    if language == 'es':
        prompt = """Eres un arquitecto creativo de mundos para un juego de ficción interactiva. Tu tarea es crear un mundo completamente original y coherente. Tienes total libertad creativa para la historia, personajes, y ambientación, PERO debes seguir estrictas reglas técnicas para garantizar que el mundo sea jugable.

**LIBERTAD CREATIVA TOTAL:**
- Inventa cualquier historia, tema, o ambientación (medieval, sci-fi, moderno, fantástico, etc.)
- Crea personajes únicos con personalidades interesantes
- Diseña un objetivo principal desafiante y atractivo
- Decide el tono (aventura, misterio, drama, comedia, etc.)

**RESTRICCIONES TÉCNICAS OBLIGATORIAS:**

**ESTRUCTURA MÍNIMA REQUERIDA:**
- 3-4 ubicaciones (cada una con nombre único y 2-3 descripciones atmosféricas)
- 4-6 objetos (nombres únicos y 2-3 descripciones cada uno)
- 2-3 personajes no jugadores + 1 personaje jugador
- 1-2 puzzles lógicos y solucionables
- 1 objetivo principal claro y completable

**REGLAS DE CONEXIÓN OBLIGATORIAS:**
1. **Conexiones bidireccionales**: Si A conecta con B, entonces B DEBE conectar con A
2. **Objetivo alcanzable**: El objetivo DEBE ser completable con los elementos que crees
3. **Cadena de dependencias**: Debe existir al menos una ruta lógica desde el estado inicial hasta completar el objetivo

**REGLAS DE PERSONAJES:**
1. **Interacciones funcionales**: Si un personaje tiene `interaction`, DEBE tener `interaction_text`
2. **Puzzles coherentes**: Si un personaje propone un puzzle, el puzzle DEBE existir y tener `proposed_by_character` configurado
3. **Inventarios válidos**: Todo objeto en inventarios de personajes DEBE existir en la lista de objetos del mundo
4. **Ubicaciones válidas**: Todos los personajes DEBEN estar ubicados en lugares que existen

**REGLAS DE OBJETOS:**
1. **Objetivos completables**: Si un objeto es requerido para el objetivo (`is_objective_target: true`), DEBE ser `gettable: true`
2. **Consistencia funcional**: Objetos decorativos pueden ser `gettable: false`, objetos funcionales DEBEN ser `gettable: true`
3. **Relevancia clara**: Cada objeto debe tener una razón de existir (funcional o atmosférica)

**REGLAS DE PUZZLES:**
1. **Soluciones claras**: Cada puzzle DEBE tener una respuesta específica y no ambigua
2. **Recompensas existentes**: Todas las recompensas (objetos, ubicaciones) DEBEN existir en el mundo
3. **Lógica interna**: Los puzzles deben hacer sentido dentro del contexto de tu historia

**REGLAS DE PASAJES BLOQUEADOS:**
1. **Obstáculos separados**: El `obstacle_name` debe ser diferente del `required_to_unblock.item_name`
   - Obstáculo = lo que bloquea físicamente (puerta, candado, barrera)
   - Requirement = lo que remueve el obstáculo (llave, herramienta, conocimiento)
2. **Elementos existentes**: Tanto obstáculos como requirements DEBEN existir como objetos en el mundo
3. **Conectividad previa**: Solo puedes bloquear pasajes entre ubicaciones ya conectadas

**VALIDACIÓN DE COMPLETABILIDAD:**
Antes de finalizar, verifica mentalmente:
1. ¿Puede el jugador completar el objetivo con los elementos disponibles?
2. ¿Existe al menos una ruta de solución desde el estado inicial?
3. ¿Todos los elementos referenciados existen realmente en el mundo?
4. ¿Las interacciones de personajes están completas?
5. ¿Los puzzles tienen sentido y son solucionables?

**INSPIRACIÓN TEMÁTICA (elige uno o combina):**
- **Misterio**: Resolver un crimen, encontrar un tesoro perdido, descubrir un secreto
- **Aventura**: Rescatar a alguien, explorar ruinas, completar una misión
- **Supervivencia**: Escapar de un lugar, conseguir recursos, encontrar la salida
- **Social**: Convencer personajes, reunir información, mediar conflictos
- **Exploración**: Descubrir nuevas áreas, mapear territorio, encontrar artefactos

**EJEMPLO DE CADENA DE DEPENDENCIAS VÁLIDA:**
1. Jugador quiere [objetivo principal]
2. Para [objetivo] necesita [objeto/ubicación X]
3. Para conseguir X necesita [resolver puzzle/conseguir objeto Y]
4. Para Y necesita [interactuar con personaje Z]
5. Personaje Z requiere [completar tarea/tener objeto W]
6. El jugador puede conseguir W directamente o mediante otro paso

**FORMATO DE SALIDA:**
Genera el JSON completo siguiendo el schema de `GeneratedWorld`. Asegúrate de que:
- Todos los nombres sean únicos y consistentes
- Todas las referencias cruzadas sean válidas
- El mundo sea completamente funcional desde el estado inicial
- La historia sea engaging y los personajes memorables

**RECUERDA:** Libertad creativa total para la narrativa, restricciones técnicas estrictas para la funcionalidad. ¡Crea algo único y jugable!"""
    else:
        prompt = """You are a creative world architect for an interactive fiction game. Your task is to create a completely original and coherent world. You have total creative freedom for the story, characters, and setting, BUT you must follow strict technical rules to ensure the world is playable.

**TOTAL CREATIVE FREEDOM:**
- Invent any story, theme, or setting (medieval, sci-fi, modern, fantasy, etc.)
- Create unique characters with interesting personalities
- Design a challenging and engaging main objective
- Decide the tone (adventure, mystery, drama, comedy, etc.)

**MANDATORY TECHNICAL CONSTRAINTS:**

**MINIMUM REQUIRED STRUCTURE:**
- 3-4 locations (each with unique name and 2-3 atmospheric descriptions)
- 4-6 objects (unique names and 2-3 descriptions each)
- 2-3 non-player characters + 1 player character
- 1-2 logical and solvable puzzles
- 1 clear and completable main objective

**MANDATORY CONNECTION RULES:**
1. **Bidirectional connections**: If A connects to B, then B MUST connect to A
2. **Achievable objective**: The objective MUST be completable with the elements you create
3. **Dependency chain**: There must be at least one logical path from initial state to objective completion

**CHARACTER RULES:**
1. **Functional interactions**: If a character has `interaction`, it MUST have `interaction_text`
2. **Coherent puzzles**: If a character proposes a puzzle, the puzzle MUST exist and have `proposed_by_character` configured
3. **Valid inventories**: Every object in character inventories MUST exist in the world's object list
4. **Valid locations**: All characters MUST be located in places that exist

**OBJECT RULES:**
1. **Completable objectives**: If an object is required for the objective (`is_objective_target: true`), it MUST be `gettable: true`
2. **Functional consistency**: Decorative objects can be `gettable: false`, functional objects MUST be `gettable: true`
3. **Clear relevance**: Each object should have a reason to exist (functional or atmospheric)

**PUZZLE RULES:**
1. **Clear solutions**: Each puzzle MUST have a specific and unambiguous answer
2. **Existing rewards**: All rewards (objects, locations) MUST exist in the world
3. **Internal logic**: Puzzles must make sense within your story's context

**BLOCKED PASSAGE RULES:**
1. **Separate obstacles**: `obstacle_name` must be different from `required_to_unblock.item_name`
   - Obstacle = what physically blocks (door, lock, barrier)
   - Requirement = what removes the obstacle (key, tool, knowledge)
2. **Existing elements**: Both obstacles and requirements MUST exist as objects in the world
3. **Prior connectivity**: You can only block passages between already connected locations

**COMPLETABILITY VALIDATION:**
Before finalizing, mentally verify:
1. Can the player complete the objective with available elements?
2. Is there at least one solution path from the initial state?
3. Do all referenced elements actually exist in the world?
4. Are character interactions complete?
5. Do puzzles make sense and are they solvable?

**THEMATIC INSPIRATION (choose one or combine):**
- **Mystery**: Solve a crime, find lost treasure, discover a secret
- **Adventure**: Rescue someone, explore ruins, complete a mission
- **Survival**: Escape a place, gather resources, find the exit
- **Social**: Convince characters, gather information, mediate conflicts
- **Exploration**: Discover new areas, map territory, find artifacts

**EXAMPLE VALID DEPENDENCY CHAIN:**
1. Player wants [main objective]
2. For [objective] needs [object/location X]
3. To get X needs [solve puzzle/get object Y]
4. For Y needs [interact with character Z]
5. Character Z requires [complete task/have object W]
6. Player can get W directly or through another step

**OUTPUT FORMAT:**
Generate the complete JSON following the `GeneratedWorld` schema. Ensure that:
- All names are unique and consistent
- All cross-references are valid
- The world is completely functional from the initial state
- The story is engaging and characters memorable

**REMEMBER:** Total creative freedom for narrative, strict technical constraints for functionality. Create something unique and playable!"""
    return prompt

def prompt_expand_world(world_state: str, player_location: str, language: str = 'en') -> str:
    """Prompt for expanding the world based on the current state."""
    if language == 'es':
        prompt = f"""Eres un arquitecto creativo de mundos para un juego de ficción interactiva. Basándote en el estado actual del mundo, expande el mundo orgánicamente añadiendo:

        1. 1-2 nuevas ubicaciones conectadas a {player_location} (con nombres y 2-3 oraciones descriptivas)
        2. 2-3 nuevos objetos colocados en estas nuevas ubicaciones (con nombres y 2-3 oraciones descriptivas) 
        3. 0-1 nuevos personajes no jugadores en una de las nuevas ubicaciones (con nombre, descripción, y posiblemente inventario)
        4. 0-1 nuevos puzzles simples que encajen con las nuevas áreas

        Haz que tus adiciones sean coherentes con el estado actual del mundo:
        {world_state}

        Considera crear:
        - Áreas ocultas que extienden la ubicación actual
        - Nuevos pasajes que previamente no se habían notado
        - Objetos que encajan con el tema de las nuevas áreas
        - Personajes que tienen relaciones interesantes con elementos existentes
        - Puzzles que utilicen objetos o conocimientos del mundo existente

        La expansión debe sentirse natural, como si estos elementos siempre hubieran estado ahí pero recién ahora se descubrieran.
        """
    else:
        prompt = f"""You are a creative world architect for an interactive fiction game. Based on the current world state, expand the world organically by adding:

        1. 1-2 new locations connected to {player_location} (with names and 2-3 descriptive sentences)
        2. 2-3 new items placed in these new locations (with names and 2-3 descriptive sentences) 
        3. 0-1 new non-player characters in one of the new locations (with a name, description, and possibly inventory)
        4. 0-1 new simple puzzles that fit with the new areas

        Make your additions coherent with the existing world state:
        {world_state}

        Consider creating:
        - Hidden areas that extend the current location
        - New passages that were previously not noticed
        - Items that fit the theme of the new areas
        - Characters that have interesting relationships with existing elements
        - Puzzles that use objects or knowledge from the existing world

        The expansion should feel natural, as if these elements were always there but just now discovered.
        """
    return prompt

def should_expand_world(player_input: str, language: str = 'en') -> bool:
    """Determine if the world should be expanded based on player input.
    
    Expansion triggers:
    - Player explicitly explores or searches
    - Player tries to go somewhere not currently available
    - Player has visited all available locations
    - Player has interacted with most available items
    """
    if language == 'es':
        exploration_keywords = [
            "explorar", "buscar", "mirar alrededor", "investigar", 
            "examinar alrededores", "revisar área", "descubrir",
            "buscar", "encontrar", "ver más", "explorar más"
        ]
    else:
        exploration_keywords = [
            "explore", "search", "look around", "investigate", 
            "examine surroundings", "check area", "discover"
        ]
    
    for keyword in exploration_keywords:
        if keyword in player_input.lower():
            return True
    
    return False

# For testing
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
- Laura (madre): Artista, tiene la llave dorada en su inventario, ubicación = Taller de pintura
- Laura DEBE proponer un puzzle cuando hables con ella
- Laura debe requerir resolver el puzzle para dar la llave

**OBJETOS REQUERIDOS:**
- Tortuga "Hojita": En el jardín (objetivo principal)
- Llave dorada: En el inventario de Laura, necesaria para abrir el candado
- Martillo gris: En el taller, útil para romper el candado (alternativa)
- Martillo verde: En la cocina, es solo decorativo (juguete inútil)

**PUZZLE REQUERIDO:**
- Laura debe proponer un puzzle cuando interactúes con ella
- El puzzle debe ser sencillo pero lógico
- Resolver el puzzle debe ser requisito para obtener la llave
- Una vez resuelto el puzzle, Laura le da la llave dorada a Emma
    - La llave dorada deja de estar en el inventario de Laura y pasa a estar en el de Emma

**CONEXIONES SEMÁNTICAS OBLIGATORIAS:**
1. Para llegar al jardín → necesitas abrir el candado
2. Para abrir el candado → necesitas la llave dorada O romperlo con el martillo gris
3. Para conseguir la llave → debes resolver el puzzle de Laura
4. Para acceder al puzzle → debes hablar con Laura

**INTERACCIÓN CON LAURA:**
- Cuando hables con Laura por primera vez, debe proponer el puzzle
- Laura debe explicar que necesitas resolver el puzzle para obtener la llave
- El puzzle debe estar relacionado con el arte/pintura (tema del taller)

**CADENA DE DEPENDENCIAS EJEMPLO:**
1. Emma quiere rescatar a Hojita del jardín
2. El jardín está bloqueado por un candado en la cocina
3. Emma habla con Laura
4. Laura propone el puzzle de los pinceles
5. Emma resuelve el puzzle
6. Laura le da la llave dorada
7. Emma abre el candado y rescata a Hojita

**VALIDACIONES CRÍTICAS:**
- Laura debe tener `proposes_puzzle` definido
- El puzzle debe tener `rewards` que incluyan dar la llave
- La interacción de Laura debe tener `interaction_text`
- Laura debe requerir resolver el puzzle para dar la llave

Genera el JSON completo siguiendo el schema de `GeneratedWorld`. Asegúrate de que Laura PROPONGA el puzzle automáticamente al interactuar."""

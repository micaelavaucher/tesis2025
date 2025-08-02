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

    # Handle new GeneratedObjective structure - check if it's a tuple with new structure
    if len(objective) == 2 and hasattr(objective[1], 'description') and hasattr(objective[1], 'type'):
        user_msg = f'The objective to narrate in an alternative way is: "{objective[1].description}"'
    else:
        # Legacy fallback for old objective structure
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
    
    Pon siempre tu narración generada entre caracteres #. Por ejemplo: # Tienes que conseguir la <llave> # o # Tienes que llegar al <Castillo> #"""

    # Handle new GeneratedObjective structure - check if it's a tuple with new structure
    if len(objective) == 2 and hasattr(objective[1], 'description') and hasattr(objective[1], 'type'):
        user_msg = f'El objetivo a decir de forma alternativa es: "{objective[1].description}"'
    else:
        # Legacy fallback for old objective structure
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

    system_msg = "You are a storyteller. Take the state of the world given to you and narrate it in a few sentences. Be careful not to include details that contradict the current state of the world, that move the story forward, or invent new puzzles that arent in the world. Also, try to use simple sentences and do not overuse poetic language"
    
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
    
    system_msg = f"""Eres un narrador. Toma el estado del mundo que se te de y nárralo en unas pocas oraciones. Ten cuidado de no incluir detalles que contradigan el estado del mundo actual, o que hagan avanzar la historia, o inventar puzzles o acertijos que no esten ya en el mundo. Además, si el jugador está en la misma ubicación en la que existe un puzzle, debes darle una pista que le haga saber que allí hay un puzzle, o que un personaje tiene un puzzle para él. Intenta usar oraciones simples, sin abusar del lenguaje poético."""
    
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

def prompt_world_update_structured(world_state: str, input: str, language: str = 'en', relevant_memories: str = ""):
    """Create a world update prompt that will return structured data based on Pydantic models."""
    if language == 'es':
        system_msg = """Eres un narrador experto manejando un mundo ficticio interactivo. Tu tarea es analizar las acciones del jugador y determinar los cambios exactos en el estado del mundo.

REGLAS CRÍTICAS PARA PUZZLES:
1. **PROPOSICIÓN DE PUZZLES**: Si un personaje tiene la propiedad "proposes_puzzle", el personaje DEBE proponer el puzzle cuando el jugador interactúe con él, ANTES de dar cualquier recompensa.
2. **RESOLUCIÓN DE PUZZLES**: Si el jugador intenta resolver un puzzle, analiza cuidadosamente si su respuesta es correcta comparándola con la respuesta esperada.
3. **REQUISITOS**: Verifica que se cumplan todos los requisitos antes de permitir acciones (objetos necesarios, puzzles resueltos, etc.).

REGLAS GENERALES:
- Objetos solo cambian de lugar si el jugador realiza acciones específicas (tomar, dar, dejar)
- Pasajes bloqueados solo se desbloquean si se cumplen los requisitos específicos
- El jugador solo se mueve si intenta explícitamente ir a otra ubicación y el movimiento es posible
- Presta atención a las descripciones, capacidades y requisitos de cada componente

INSTRUCCIÓN ESPECIAL SOBRE MEMORIA:
Presta especial atención a la sección 'Recuerdos Relevantes del Pasado' si está presente. Úsalos para informar tu decisión. Por ejemplo, si el jugador le habla a un personaje sobre un objeto, tu respuesta debe reflejar cómo reaccionaría ese personaje basándose en interacciones pasadas.

Tu respuesta debe ser un JSON válido que siga exactamente el modelo WorldUpdate."""
        
        user_msg_base = f"""Estado actual del mundo:
{world_state}

{relevant_memories}El jugador ahora realiza la siguiente acción:
<accion>
{input}
</accion>

Devuelve un objeto JSON con la siguiente estructura:
{{
    "moved_objects": [
        {{"object_name": "nombre", "new_location": "ubicación"}}
    ],
    "blocked_passages_available": [
        {{"location_name": "ubicación", "is_available": true}}
    ],
    "location_changed": {{
        "new_location": "nombre_ubicación_o_null"
    }},
    "puzzles_solved": [
        {{"puzzle_name": "nombre", "answer": "respuesta", "success": true}}
    ],
    "narration": "Descripción narrativa rica de lo que ocurrió"
}}

IMPORTANTE: Siempre incluye el campo narration con una descripción detallada y evocativa de lo que ocurrió en el mundo."""
    else:
        system_msg = """You are an expert narrator managing an interactive fictional world. Your task is to analyze the player's actions and determine the exact changes in the world state.

CRITICAL RULES FOR PUZZLES:
1. **PUZZLE PROPOSITION**: If a character has the "proposes_puzzle" property, the character MUST propose the puzzle when the player interacts with them, BEFORE giving any reward.
2. **PUZZLE RESOLUTION**: If the player attempts to solve a puzzle, carefully analyze if their answer is correct by comparing it with the expected answer.
3. **REQUIREMENTS**: Verify that all requirements are met before allowing actions (necessary objects, solved puzzles, etc.).

GENERAL RULES:
- Objects only change location if the player performs specific actions (take, give, drop)
- Blocked passages only unlock if specific requirements are met
- The player only moves if they explicitly attempt to go to another location and the movement is possible
- Pay attention to the descriptions, capabilities, and requirements of each component

SPECIAL INSTRUCTION ABOUT MEMORY:
Pay special attention to the 'Relevant Past Memories' section if present. Use them to inform your decision. For example, if the player talks to a character about an object, your response should reflect how that character would react based on past interactions.

Your response must be valid JSON that follows exactly the WorldUpdate model."""
    
        user_msg_base = f"""Current world state:
{world_state}

{relevant_memories}The player now performs the following action:
<action>
{input}
</action>

Return a JSON object with the following structure:
{{
    "moved_objects": [
        {{"object_name": "name", "new_location": "location"}}
    ],
    "blocked_passages_available": [
        {{"location_name": "location", "is_available": true}}
    ],
    "location_changed": {{
        "new_location": "location_name_or_null"
    }},
    "puzzles_solved": [
        {{"puzzle_name": "name", "answer": "answer", "success": true}}
    ],
    "narration": "Rich narrative description of what happened"
}}

IMPORTANT: Always include the narration field with a detailed, evocative description of what occurred in the world."""
    
    return system_msg, user_msg_base, WorldUpdate

def prompt_world_update_spanish (world_state: str, input: str):
    system_msg = f"""Eres un narrador experto manejando un mundo ficticio interactivo. Siguiendo un formato específico, tu tarea es encontrar los cambios en el mundo a raíz de las acciones del jugador. En específico, tendrás que encontrar qué objetos cambiaron de lugar, qué pasajes entre lugares se desbloquearon, si el jugador se movió de lugar, y si resolvió puzzles.
    
    **REGLAS CRÍTICAS PARA PUZZLES:**
    (P1) **PROPOSICIÓN DE PUZZLES**: Si un personaje tiene la propiedad "proposes_puzzle", el personaje DEBE proponer el puzzle cuando el jugador interactúe con él, ANTES de dar cualquier recompensa.
    (P2) **RESOLUCIÓN DE PUZZLES**: Si el jugador intenta resolver un puzzle, analiza cuidadosamente si su respuesta es correcta comparándola con la respuesta esperada del puzzle.
    (P3) **REQUISITOS DE PUZZLES**: Verifica que se cumplan todos los requisitos antes de permitir que un puzzle sea resuelto.
    (P4) **RECOMPENSAS CONDICIONADAS**: Las recompensas (objetos, pasajes, información) solo se otorgan DESPUÉS de resolver exitosamente el puzzle.

    **REGLAS CRÍTICAS PARA INTERACCIONES CON PERSONAJES:**
    (I1) **SER DIRECTO Y ÚTIL**: Cuando el jugador interactúa con un personaje, el personaje debe ser DIRECTO sobre lo que necesita o quiere. No debe dar vueltas o ser evasivo innecesariamente.
    (I2) **COMUNICAR REQUISITOS CLARAMENTE**: Si un personaje tiene requisitos específicos (objetos, puzzles resueltos, etc.), debe comunicárselos al jugador de forma CLARA en la primera o segunda interacción. No debe seguir siendo misterioso después de que el jugador muestre interés.
    (I3) **EVITAR REPETICIÓN INÚTIL**: Si el jugador ya interactuó con un personaje y el personaje ya le dijo que necesita algo, no debe repetir la misma información vaga. En su lugar, debe ser más específico o sugerir dónde conseguir lo que necesita.
    (I4) **INFORMACIÓN PROGRESIVA**: En cada interacción, el personaje debe proporcionar información MÁS ESPECÍFICA que en la anterior, hasta que el jugador tenga toda la información necesaria para cumplir con los requisitos.

    Aquí hay otras aclaraciones importantes:
    (A) Presta atención a la descripción de los componentes y sus capacidades.
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
    (I) Tu narración debe ser rica en detalles y evocadora, utilizando detalles sensoriales cuando sea apropiado. Haz que el mundo cobre vida a través de tus descripciones, sin dejar de adherirte a los hechos del estado del mundo.

    Aquí hay algunos ejemplos (con la aclaración entre paréntesis sobre qué podría haber intentado hacer el jugador) sobre el formato, descritos en los puntos (F) y (G):
    
    Ejemplo 1 (El jugador guarda el hacha en su inventario)
    - Moved object: <hacha> now is in <Inventory>
    - Blocked passages now available: None
    - Your location changed: None
    - Puzzle solved: None
    # Tomas el mango de madera desgastada del hacha, sintiendo su peso reconfortante mientras la levantas. La cabeza metálica brilla tenuemente bajo la luz mientras la aseguras cuidadosamente en tu mochila. El peso familiar contra tu espalda te recuerda el consejo de tu padre sobre siempre mantener una buena herramienta a mano. #

    Ejemplo 2 (El jugador desbloquea el pasaje al Sótano)
    - Moved object: None
    - Blocked passages now available: <Sótano>
    - Your location changed: None
    - Puzzle solved: None
    # Con un giro final de la oxidada llave, el viejo candado se abre con un satisfactorio clic. Lo quitas del pestillo y empujas a un lado la pesada barra de madera que aseguraba la puerta del sótano. Una bocanada de aire frío y húmedo surge desde abajo, trayendo consigo el olor a piedra húmeda y recuerdos olvidados. El sótano, previamente prohibido, ahora es accesible, sus secretos esperando ser descubiertos en la oscuridad de abajo. #

    Ejemplo 3 (El jugador ahora está en el Jardín)
    - Moved object: None
    - Blocked passages now available: None
    - Your location changed: <Jardín>
    - Puzzle solved: None
    # Atraviesas la chirriante verja del jardín y entras en un mundo de colores vibrantes y fragancias. La luz del sol se filtra a través de las hojas de un roble antiguo, proyectando sombras moteadas sobre el sendero cubierto de vegetación. Mariposas danzan entre flores de todos los tonos, y en algún lugar cercano, el agua fluye musicalmente. El jardín te abraza con su belleza salvaje, tan diferente de los confines estériles que acabas de dejar atrás. #

    Ejemplo 4 (El jugador guarda objetos en la bolsa y deja el hacha en el suelo)
    - Moved object: <plátano> now is in <Inventory>, <botella> now is in <Inventory>, <hacha> now is in <Salón Principal>
    - Blocked passages now available: None
    - Your location changed: None
    - Puzzle solved: None
    # Colocas cuidadosamente el plátano maduro y la botella de vidrio en tu bolsa, organizándolos para que nada se aplaste. El aroma dulce del plátano se mezcla con el olor a humedad de tu mochila bien viajada. Con deliberado cuidado, dejas el hacha pesada sobre el suelo pulido del Salón Principal. Reposa allí con cierta finalidad, su hoja reflejando la danzante luz de la araña de cristal que cuelga arriba. Quizás alguien más encuentre mejor uso para ella que tú. #

    Ejemplo 5 (El jugador guarda objetos en la bolsa, deja el hacha en el suelo y desbloquea el pasaje a la Habitación Pequeña)
    - Moved object: <plátano> now is in <Inventory>, <botella> now is in <Inventory>, <hacha> now is in <Salón Principal>
    - Blocked passages now available: <Habitación Pequeña>
    - Your location changed: None
    - Puzzle solved: None
    # Tus dedos trabajan rápidamente mientras guardas el plátano y la botella en tu mochila. El vidrio tintinea suavemente contra tus otras posesiones mientras aseguras la solapa. El hacha la colocas cuidadosamente sobre el suelo de mármol del Salón Principal, su mango gastado apuntando hacia la gran escalera. Después de insertar la ornamentada llave en la pequeña cerradura de latón, escuchas una serie de clics y zumbidos mientras los mecanismos ocultos se desenganchan. La puerta previamente sellada hacia la Habitación Pequeña se estremece y luego se abre ligeramente, liberando una bocanada de aire viciado. Un nuevo camino está ahora disponible para ti, llamándote con la promesa del descubrimiento. #

    Ejemplo 6 (El jugador guarda objetos en la bolsa, deja el hacha en el suelo, desbloquea el pasaje y va a la Habitación Pequeña)
    - Moved object: <plátano> now is in <Inventory>, <botella> now is in <Inventory>, <hacha> now is in <Salón Principal>
    - Blocked passages now available: <Habitación Pequeña>
    - Your location changed: <Habitación Pequeña>
    - Puzzle solved: None
    # Con eficiencia practicada, guardas tanto el plátano como la botella en tu bolsa, sintiendo cómo aumenta el peso cómodo contra tu cadera. El hacha la dejas deliberadamente sobre el suelo reluciente del Salón Principal, donde su cabeza metálica atrapa la luz del candelabro de cristal que cuelga arriba. Después de girar la antigua llave en la cerradura, la puerta oculta hacia la Habitación Pequeña se abre con un crujido, revelando un espacio intacto durante lo que deben ser décadas. Motas de polvo bailan en el rayo de luz que ahora se introduce en este santuario olvidado. Llevado por la curiosidad, cruzas el umbral, las tablas del suelo gimiendo bajo tu peso al entrar en la Habitación Pequeña. El aire aquí está cargado de secretos y el dulce olor a humedad de libros antiguos y recuerdos olvidados. #

    Ejemplo 7 (El jugador guarda el lápiz en la bolsa y le da el libro a Juan)
    - Moved object: <libro> now is in <Juan>, <lápiz> now is in <Inventory>
    - Blocked passages now available: None
    - Your location changed: None
    - Puzzle solved: None
    # Deslizas el gastado lápiz de cedro en tu bolsa, su forma familiar anidándose entre tus otras posesiones. El pesado libro encuadernado en cuero lo extiendes hacia Juan con ambas manos, respetando su aparente edad y valor. Sus ojos se ensanchan ligeramente al reconocer el tomo. "Esto es... He estado buscando esto durante años", susurra, su voz espesa de emoción. Sus manos curtidas aceptan el libro con reverencia, acunándolo como quien sostiene una reliquia preciosa. Juan abre cuidadosamente la cubierta, y por un momento, su comportamiento estoico se suaviza mientras contempla las páginas amarillentas en su interior. #

    Ejemplo 8 (El jugador da la computadora a Susana)
    - Moved object: <computadora> now is in <Susana>
    - Blocked passages now available: None
    - Your location changed: None
    - Puzzle solved: None
    # Le entregas la elegante laptop a Susana, cuyos ojos se iluminan con interés profesional. "Por fin", murmura, sus dedos ya bailando sobre el teclado mientras la pantalla ilumina su rostro concentrado. El resplandor azul resalta la determinación en su expresión mientras accede rápidamente a archivos que tú no podrías esperar entender. Guarda la computadora de manera segura en su bolso de mensajero, el movimiento practicado y eficiente. "Esto podría cambiarlo todo", añade críticamente, asintiendo en agradecimiento mientras su mente claramente corre con nuevas posibilidades. #

    Ejemplo 9 (El jugador hace algo que no tiene el resultado esperado)
    - Moved object: None
    - Blocked passages now available: None
    - Your location changed: None
    - Puzzle solved: None
    # Intentas girar la ornamentada manija de latón, pero la puerta permanece obstinadamente cerrada. El mecanismo hace un sonido de clic sordo, pero nada más sucede. Quizás hay otra forma de abrirla, o algo que te estás perdiendo. Las marcas descoloridas sobre el marco de la puerta parecen burlarse de tus esfuerzos, manteniendo sus secretos bien guardados. #

    Ejemplo 10 (El jugador hace una pregunta)
    - Moved object: None
    - Blocked passages now available: None
    - Your location changed: None
    - Puzzle solved: None
    # Al examinar el extraño símbolo grabado en la pared, lo reconoces como un antiguo sigilo que representa protección y conocimiento oculto. La artesanía es notable, con intrincados patrones en espiral que parecen cambiar ligeramente cuando se ven desde diferentes ángulos. Las leyendas hablan de tales marcas utilizadas por los antiguos practicantes para alejar a los espíritus malignos mientras realizaban sus investigaciones arcanas. El hecho de que permanezca intacto después de todos estos siglos habla del poder que se creía que tenía. #"""
    
    
    user_msg = f"""Expresa los cambios en el mundo siguiendo el formato pedido, teniendo en cuenta que el jugador ingresó esta entrada "{input}" a partir de este estado del mundo:
    
    {world_state}"""

    return system_msg, user_msg

def prompt_world_update_english (world_state: str, input: str):
    system_msg = f"""You are an expert storyteller managing an interactive fictional world. Following a specific format, your task is to find the changes in the world after the actions in the player input. Specifically, you will have to find what objects were moved, which previously blocked passages are now unblocked, if the player moved to a new place, and if any puzzles were solved.

    **CRITICAL RULES FOR PUZZLES:**
    (P1) **PUZZLE PROPOSITION**: If a character has the "proposes_puzzle" property, the character MUST propose the puzzle when the player interacts with them, BEFORE giving any reward.
    (P2) **PUZZLE RESOLUTION**: If the player attempts to solve a puzzle, carefully analyze if their answer is correct by comparing it with the expected answer.
    (P3) **PUZZLE REQUIREMENTS**: Verify that all requirements are met before allowing a puzzle to be solved.
    (P4) **CONDITIONAL REWARDS**: Rewards (objects, passages, information) are only granted AFTER successfully solving the puzzle.
       
    Here are other important clarifications:
    (A) Pay attention to the description of the components and their capabilities.
    (B) If a passage is blocked, then the player must unblock it before being able to reach the place. Even if the player tells you that he is going to access the locked location, you have to be sure that he is complying with what you asked to allow him to unlock the access, for example by using a key or solving a puzzle.
    (C) **CHARACTERS WITH REQUIREMENTS**: If a character has specific requirements (like solving a puzzle or having certain objects), they should NOT give objects or help until those requirements are met. Carefully review the "interaction" section of each character and their "requires".
    (D) Do not assume that the player input always makes sense; maybe those actions try to do something that the world does not allow.
    (E) Follow always the following format with the four categories, using "None" in each case if there are no changes and repeat the category for each case:
    - Moved object: <object> now is in <new_location>
    - Blocked passages now available: <now_reachable_location>
    - Your location changed: <new_location>
    - Puzzle solved: <puzzle_name> with answer <answer> (only if the player solved a puzzle)
    (F) Finally, you can narrate the changes you've detected in the world state (without moving the story forward and without making up details not included in the world state!) using the format: #your final message#
    (G) In the narration section that you add at the end, between # symbols, you can also answer questions that the player asks in their input, about the objects or characters they can see, or the place they are in.
    (H) Your narration should be richly detailed and evocative, using sensory details when appropriate. Make the world come alive through your descriptions, while still adhering to the facts of the world state.

    Here I give you some examples (in parentheses, a clarification about what the player might have tried to do) for the asked format, as described in items (E) and (F):

    Example 1 (The player took the axe and put it in the inventory)
    - Moved object: <axe> now is in <Inventory>
    - Blocked passages now available: None
    - Your location changed: None
    - Puzzle solved: None
    #You grasp the weathered wooden handle of the axe, feeling its reassuring weight as you lift it. The metal head gleams dully in the light as you carefully secure it in your pack. The familiar weight against your back reminds you of your father's advice about always keeping a good tool handy.#

    Example 2 (The player unblocks the passage to the basement)
    - Moved object: None
    - Blocked passages now available: <Basement>
    - Your location changed: None
    - Puzzle solved: None
    #With a final turn of the rusty key, the old padlock releases with a satisfying click. You remove it from the latch and push aside the heavy wooden bar that secured the basement door. A waft of cool, musty air rises from below, carrying the scent of damp stone and forgotten memories. The previously forbidden basement is now accessible, its secrets waiting to be discovered in the darkness below.#

    Example 3 (The player now is in the garden)
    - Moved object: None
    - Blocked passages now available: None
    - Your location changed: <Garden>
    - Puzzle solved: None
    #You step through the creaking garden gate and into a world of vibrant color and fragrance. Sunlight filters through the leaves of an ancient oak, casting dappled shadows across the overgrown path. Butterflies dance between blooms of every hue, and somewhere nearby, water trickles musically. The garden embraces you with its wild beauty, so different from the sterile confines you just left behind.#

    Example 4 (The player puts objects in the bag and leaves the axe on the floor)
    - Moved object: <banana> now is in <Inventory>, <bottle> now is in <Inventory>, <axe> now is in <Main Hall>
    - Blocked passages now available: None
    - Your location changed: None
    - Puzzle solved: None
    #You carefully place the ripe banana and glass bottle into your bag, arranging them so nothing gets crushed. The banana's sweet aroma mingles with the musty scent of your well-traveled pack. With deliberate care, you set the heavy axe down on the polished floor of the Main Hall. It rests there with a certain finality, its blade reflecting the dancing light from the chandelier above. Perhaps someone else might find better use for it than you.#

    Example 5 (The player puts objects in the bag and leaves the axe on the floor and unblocks the passage to the Small room)
    - Moved object: <banana> now is in <Inventory>, <bottle> now is in <Inventory>, <axe> now is in <Main Hall>
    - Blocked passages now available: <Small room>
    - Your location changed: None
    - Puzzle solved: None
    #Your fingers work quickly as you tuck the banana and bottle safely into your pack. The glass clinks softly against your other possessions as you secure the flap. The axe you place carefully on the marble floor of the Main Hall, its worn handle pointing toward the grand staircase. After inserting the ornate key into the small brass lock, you hear a series of clicks and whirrs as hidden mechanisms disengage. The previously sealed doorway to the Small Room shudders and then swings open slightly, releasing a puff of stale air. A new path is now available to you, beckoning with the promise of discovery.#

    Example 6 (The player puts objects in the bag and leaves the axe on the floor, unblocks the passage and goes to the Small room)
    - Moved object: <banana> now is in <Inventory>, <bottle> now is in <Inventory>, <axe> now is in <Main Hall>
    - Blocked passages now available: <Small room>
    - Your location changed: <Small room>
    - Puzzle solved: None
    #With practiced efficiency, you stow both the banana and bottle in your bag, feeling the comfortable weight increase against your hip. The axe you deliberately place on the gleaming floor of the Main Hall, where its metal head catches the light from the crystal chandelier above. After turning the ancient key in the lock, the hidden door to the Small Room creaks open, revealing a space untouched for what must be decades. Dust motes dance in the beam of light that now intrudes upon this forgotten sanctuary. Drawn by curiosity, you step across the threshold, the floorboards groaning beneath your weight as you enter the Small Room. The air here is thick with secrets and the sweet musty scent of old books and forgotten memories.#

    Example 7 (The player solves a riddle correctly)
    - Moved object: None
    - Blocked passages now available: <Secret Chamber>
    - Your location changed: None
    - Puzzle solved: <Ancient Riddle> with answer <echo>
    #Your voice echoes in the chamber as you speak the answer with confidence: "Echo." The ancient statue's eyes suddenly blaze with inner light, and a rumbling sound fills the air. Stone grinds against stone as a hidden mechanism activates, revealing a secret passage behind the wall. The Ancient Riddle has been solved, and the way to the Secret Chamber now lies open before you, promising mysteries yet to be discovered.#

    Example 8 (The player puts the pencil in the bag and gives the book to John)
    - Moved object: <book> now is in <John>, <pencil> now is in <Inventory>
    - Blocked passages now available: None
    - Your location changed: None
    - Puzzle solved: None
    #You slip the worn cedar pencil into your bag, its familiar shape nestling among your other possessions. The heavy leather-bound book you extend toward John with both hands, respecting its apparent age and value. His eyes widen slightly as he recognizes the tome. "This is... I've been searching for this for years," he whispers, his voice thick with emotion. His weathered hands accept the book with reverence, cradling it as one might hold a precious relic. John carefully opens the cover, and for a moment, his stoic demeanor softens as he gazes at the yellowed pages within.#

    Example 9 (The player gives the computer to Susan)
    - Moved object: <computer> now is in <Susan>
    - Blocked passages now available: None
    - Your location changed: None
    - Puzzle solved: None
    - Your location changed: None
    #You hand the sleek laptop to Susan, whose eyes light up with professional interest. "Finally," she murmurs, her fingers already dancing across the keyboard as the screen illuminates her focused face. The blue glow highlights the determination in her expression as she quickly accesses files you couldn't hope to understand. She tucks the computer securely into her messenger bag, the movement practiced and efficient. "This could change everything," she adds cryptically, nodding her thanks while her mind clearly races with new possibilities.#

    Example 10 (The player does something that has not the expected outcome)
    - Moved object: None
    - Blocked passages now available: None
    - Your location changed: None
    - Puzzle solved: None
    #You try turning the ornate brass handle, but the door remains stubbornly shut. The mechanism makes a dull clicking sound, but nothing else happens. Perhaps there's another way to open it, or something you're missing. The faded markings above the doorframe seem to mock your efforts, holding their secrets close.#

    Example 11 (The player asks a question)
    - Moved object: None
    - Blocked passages now available: None
    - Your location changed: None
    - Puzzle solved: None
    #As you examine the strange symbol etched into the wall, you recognize it as an ancient sigil representing protection and hidden knowledge. The craftsmanship is remarkable, with intricate swirling patterns that seem to shift slightly when viewed from different angles. Legends speak of such markings being used by the old practitioners to ward off evil spirits while conducting their arcane research. The fact that it remains intact after all these centuries speaks to the power it was believed to hold.#"""
    
    
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
- 1 objetivo principal claro y completable (OBLIGATORIO - tu mundo DEBE definir un objetivo específico)

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
1. **Soluciones descubribles**: Cada puzzle DEBE tener una solución que el jugador pueda DESCUBRIR a través del juego
   - PROHIBIDO: Códigos o soluciones que el jugador no pueda averiguar explorando el mundo
   - OBLIGATORIO: Pistas físicas en el entorno, diálogos con personajes, o documentos que revelen la solución
2. **Soluciones claras**: Cada puzzle DEBE tener una respuesta específica y no ambigua
3. **Recompensas existentes**: Todas las recompensas (objetos, ubicaciones) DEBEN existir en el mundo
4. **Lógica interna**: Los puzzles deben hacer sentido dentro del contexto de tu historia
5. **Proceso de resolución**: Los puzzles deben requerir INTERACCIÓN con el mundo (no solo conocer una respuesta)

**TIPOS DE PUZZLES PERMITIDOS:**
1. **Puzzles de información**: Requieren descubrir información específica (como una nota con la combinación de una caja fuerte)
2. **Puzzles de item**: Requieren usar un objeto específico para resolver un problema (como una llave para abrir una puerta)
3. **Puzzles de secuencia**: Requieren realizar acciones en un orden específico (como pulsar botones en cierto orden)
4. **Puzzles de adivinanza**: El jugador debe resolver un acertijo o enigma basado en pistas del entorno
5. **Puzzles combinados**: Mezclan varios de los anteriores tipos

**EJEMPLO DE BUEN PUZZLE:**
- Puzzle: Abrir una caja fuerte con un código
- Pista descubrible 1: En un cuaderno encontrado en el escritorio hay una fecha: "15/7/89"
- Pista descubrible 2: Un personaje menciona "el cumpleaños de mi hija es muy importante para mí"
- Solución: El código 1589 (derivado de la fecha que el jugador puede encontrar)

**EJEMPLO DE MAL PUZZLE (PROHIBIDO):**
- Puzzle: Abrir una puerta con un código
- No hay pistas en el mundo sobre cuál es el código
- La solución es un número arbitrario que el jugador no puede descubrir

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
5. ¿Los puzzles tienen sentido y son solucionables A TRAVÉS DE LA EXPLORACIÓN?
6. ¿Para cada código o información necesaria, existe un modo de que el jugador lo descubra?

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
- 1 clear and completable main objective (MANDATORY - your world MUST define a specific objective)

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
1. **Discoverable solutions**: Each puzzle MUST have a solution that players can DISCOVER through gameplay
   - FORBIDDEN: Codes or solutions that players cannot figure out by exploring the world
   - MANDATORY: Physical clues in the environment, character dialogues, or documents that reveal the solution
2. **Clear solutions**: Each puzzle MUST have a specific and unambiguous answer
3. **Existing rewards**: All rewards (objects, locations) MUST exist in the world
4. **Internal logic**: Puzzles must make sense within your story's context
5. **Resolution process**: Puzzles must require INTERACTION with the world (not just knowing an answer)

**ALLOWED PUZZLE TYPES:**
1. **Information puzzles**: Require discovering specific information (like a note with a safe combination)
2. **Item puzzles**: Require using a specific item to solve a problem (like a key to open a door)
3. **Sequence puzzles**: Require performing actions in a specific order (like pressing buttons in a certain order)
4. **Riddle puzzles**: Player must solve a riddle or enigma based on environmental clues
5. **Combination puzzles**: Mix several of the above types

**EXAMPLE OF GOOD PUZZLE:**
- Puzzle: Open a safe with a code
- Discoverable clue 1: In a notebook found on the desk there's a date: "15/7/89"
- Discoverable clue 2: A character mentions "my daughter's birthday is very important to me"
- Solution: Code 1589 (derived from the date that player can find)

**EXAMPLE OF BAD PUZZLE (FORBIDDEN):**
- Puzzle: Open a door with a code
- No clues in the world about what the code is
- Solution is an arbitrary number the player cannot discover

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
5. Do puzzles make sense and are they solvable THROUGH EXPLORATION?
6. For each code or necessary information, is there a way for the player to discover it?

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

def prompt_generate_world_from_inspiration(inspo: str, language: str = 'es') -> str:
    """Generate a prompt for creating a creative world based on specific inspiration with full LLM autonomy."""
    if language == 'es':
        prompt = f"""Eres un arquitecto creativo de mundos para un juego de ficción interactiva. Tu tarea es crear un mundo completamente original y coherente BASADO ESPECÍFICAMENTE EN LA SIGUIENTE INSPIRACIÓN:

**INSPIRACIÓN OBLIGATORIA:**
{inspo}

**INSTRUCCIÓN CRÍTICA:** Debes crear tu mundo usando esta inspiración como base fundamental. Todos los elementos del mundo (historia, personajes, ambientación, objetivo principal) deben estar directamente conectados y derivados de esta inspiración. NO ignores ni te desvíes de esta inspiración base.

**LIBERTAD CREATIVA DENTRO DE LA INSPIRACIÓN:**
- Desarrolla la historia, tema, y ambientación basándote en la inspiración proporcionada
- Crea personajes únicos que encajen con el tema inspiracional
- Diseña un objetivo principal que sea coherente con la inspiración
- Adapta el tono para que complemente la inspiración dada

**RESTRICCIONES TÉCNICAS OBLIGATORIAS:**

**ESTRUCTURA MÍNIMA REQUERIDA:**
- 3-4 ubicaciones (cada una con nombre único y 2-3 descripciones atmosféricas)
- 4-6 objetos (nombres únicos y 2-3 descripciones cada uno)
- 2-3 personajes no jugadores + 1 personaje jugador
- 1-2 puzzles lógicos y solucionables
- 1 objetivo principal claro y completable (OBLIGATORIO - tu mundo DEBE definir un objetivo específico)

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
1. **Soluciones descubribles**: Cada puzzle DEBE tener una solución que el jugador pueda DESCUBRIR a través del juego
   - PROHIBIDO: Códigos o soluciones que el jugador no pueda averiguar explorando el mundo
   - OBLIGATORIO: Pistas físicas en el entorno, diálogos con personajes, o documentos que revelen la solución
2. **Soluciones claras**: Cada puzzle DEBE tener una respuesta específica y no ambigua
3. **Recompensas existentes**: Todas las recompensas (objetos, ubicaciones) DEBEN existir en el mundo
4. **Lógica interna**: Los puzzles deben hacer sentido dentro del contexto de tu historia
5. **Proceso de resolución**: Los puzzles deben requerir INTERACCIÓN con el mundo (no solo conocer una respuesta)

**TIPOS DE PUZZLES PERMITIDOS:**
1. **Puzzles de información**: Requieren descubrir información específica (como una nota con la combinación de una caja fuerte)
2. **Puzzles de item**: Requieren usar un objeto específico para resolver un problema (como una llave para abrir una puerta)
3. **Puzzles de secuencia**: Requieren realizar acciones en un orden específico (como pulsar botones en cierto orden)
4. **Puzzles de adivinanza**: El jugador debe resolver un acertijo o enigma basado en pistas del entorno
5. **Puzzles combinados**: Mezclan varios de los anteriores tipos

**EJEMPLO DE BUEN PUZZLE:**
- Puzzle: Abrir una caja fuerte con un código
- Pista descubrible 1: En un cuaderno encontrado en el escritorio hay una fecha: "15/7/89"
- Pista descubrible 2: Un personaje menciona "el cumpleaños de mi hija es muy importante para mí"
- Solución: El código 1589 (derivado de la fecha que el jugador puede encontrar)

**EJEMPLO DE MAL PUZZLE (PROHIBIDO):**
- Puzzle: Abrir una puerta con un código
- No hay pistas en el mundo sobre cuál es el código
- La solución es un número arbitrario que el jugador no puede descubrir

**REGLAS DE PASAJES BLOQUEADOS:**
1. **Obstáculos separados**: El `obstacle_name` debe ser diferente del `required_to_unblock.item_name`
   - Obstáculo = lo que bloquea físicamente (puerta, candado, barrera)
   - Requirement = lo que remueve el obstáculo (llave, herramienta, conocimiento)
2. **Elementos existentes**: Tanto obstáculos como requirements DEBEN existir como objetos en el mundo
3. **Conectividad previa**: Solo puedes bloquear pasajes entre ubicaciones ya conectadas

**VALIDACIÓN DE COMPLETABILIDAD:**
Antes de finalizar, verifica mentalmente:
1. **¿HAS DEFINIDO UN OBJETIVO PRINCIPAL CLARO?** (OBLIGATORIO)
2. ¿Puede el jugador completar el objetivo con los elementos disponibles?
3. ¿Existe al menos una ruta de solución desde el estado inicial?
4. ¿Todos los elementos referenciados existen realmente en el mundo?
5. ¿Las interacciones de personajes están completas?
6. ¿Los puzzles tienen sentido y son solucionables A TRAVÉS DE LA EXPLORACIÓN?
7. ¿Para cada código o información necesaria, existe un modo de que el jugador lo descubra?
8. **¿TODO el mundo está coherentemente basado en la inspiración proporcionada?**

**EJEMPLO DE CADENA DE DEPENDENCIAS VÁLIDA:**
1. Jugador quiere [objetivo principal basado en la inspiración]
2. Para [objetivo] necesita [objeto/ubicación X relacionado con la inspiración]
3. Para conseguir X necesita [resolver puzzle/conseguir objeto Y que encaje con el tema]
4. Para Y necesita [interactuar con personaje Z derivado de la inspiración]
5. Personaje Z requiere [completar tarea/tener objeto W coherente con el tema]
6. El jugador puede conseguir W directamente o mediante otro paso

**FORMATO DE SALIDA:**
Genera el JSON completo siguiendo el schema de `GeneratedWorld`. Asegúrate de que:
- Todos los nombres sean únicos y consistentes
- Todas las referencias cruzadas sean válidas
- El mundo sea completamente funcional desde el estado inicial
- La historia sea engaging y los personajes memorables
- **TODO esté basado en y sea coherente con la inspiración proporcionada**

**RECUERDA:** Debes usar la inspiración proporcionada como base fundamental para TODO el mundo. Libertad creativa total DENTRO de esa inspiración, restricciones técnicas estrictas para la funcionalidad. ¡Crea algo único, jugable y fiel a la inspiración!"""
    else:
        prompt = f"""You are a creative world architect for an interactive fiction game. Your task is to create a completely original and coherent world BASED SPECIFICALLY ON THE FOLLOWING INSPIRATION:

**MANDATORY INSPIRATION:**
{inspo}

**CRITICAL INSTRUCTION:** You must create your world using this inspiration as the fundamental base. All world elements (story, characters, setting, main objective) must be directly connected to and derived from this inspiration. DO NOT ignore or deviate from this base inspiration.

**CREATIVE FREEDOM WITHIN THE INSPIRATION:**
- Develop the story, theme, and setting based on the provided inspiration
- Create unique characters that fit the inspirational theme
- Design a main objective that is coherent with the inspiration
- Adapt the tone to complement the given inspiration

**MANDATORY TECHNICAL CONSTRAINTS:**

**MINIMUM REQUIRED STRUCTURE:**
- 3-4 locations (each with unique name and 2-3 atmospheric descriptions)
- 4-6 objects (unique names and 2-3 descriptions each)
- 2-3 non-player characters + 1 player character
- 1-2 logical and solvable puzzles
- 1 clear and completable main objective (MANDATORY - your world MUST define a specific objective)

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
1. **Discoverable solutions**: Each puzzle MUST have a solution that players can DISCOVER through gameplay
   - FORBIDDEN: Codes or solutions that players cannot figure out by exploring the world
   - MANDATORY: Physical clues in the environment, character dialogues, or documents that reveal the solution
2. **Clear solutions**: Each puzzle MUST have a specific and unambiguous answer
3. **Existing rewards**: All rewards (objects, locations) MUST exist in the world
4. **Internal logic**: Puzzles must make sense within your story's context
5. **Resolution process**: Puzzles must require INTERACTION with the world (not just knowing an answer)

**ALLOWED PUZZLE TYPES:**
1. **Information puzzles**: Require discovering specific information (like a note with a safe combination)
2. **Item puzzles**: Require using a specific item to solve a problem (like a key to open a door)
3. **Sequence puzzles**: Require performing actions in a specific order (like pressing buttons in a certain order)
4. **Riddle puzzles**: Player must solve a riddle or enigma based on environmental clues
5. **Combination puzzles**: Mix several of the above types

**EXAMPLE OF GOOD PUZZLE:**
- Puzzle: Open a safe with a code
- Discoverable clue 1: In a notebook found on the desk there's a date: "15/7/89"
- Discoverable clue 2: A character mentions "my daughter's birthday is very important to me"
- Solution: Code 1589 (derived from the date that player can find)

**EXAMPLE OF BAD PUZZLE (FORBIDDEN):**
- Puzzle: Open a door with a code
- No clues in the world about what the code is
- Solution is an arbitrary number the player cannot discover

**BLOCKED PASSAGE RULES:**
1. **Separate obstacles**: `obstacle_name` must be different from `required_to_unblock.item_name`
   - Obstacle = what physically blocks (door, lock, barrier)
   - Requirement = what removes the obstacle (key, tool, knowledge)
2. **Existing elements**: Both obstacles and requirements MUST exist as objects in the world
3. **Prior connectivity**: You can only block passages between already connected locations

**COMPLETABILITY VALIDATION:**
Before finalizing, mentally verify:
1. **HAVE YOU DEFINED A CLEAR MAIN OBJECTIVE?** (MANDATORY)
2. Can the player complete the objective with available elements?
3. Is there at least one solution path from the initial state?
4. Do all referenced elements actually exist in the world?
5. Are character interactions complete?
6. Do puzzles make sense and are they solvable THROUGH EXPLORATION?
7. For each code or necessary information, is there a way for the player to discover it?
8. **Is the ENTIRE world coherently based on the provided inspiration?**

**EXAMPLE VALID DEPENDENCY CHAIN:**
1. Player wants [main objective based on inspiration]
2. For [objective] needs [object/location X related to inspiration]
3. To get X needs [solve puzzle/get object Y that fits the theme]
4. For Y needs [interact with character Z derived from inspiration]
5. Character Z requires [complete task/have object W coherent with theme]
6. Player can get W directly or through another step

**OUTPUT FORMAT:**
Generate the complete JSON following the `GeneratedWorld` schema. Ensure that:
- All names are unique and consistent
- All cross-references are valid
- The world is completely functional from the initial state
- The story is engaging and characters memorable
- **EVERYTHING is based on and coherent with the provided inspiration**

**REMEMBER:** You must use the provided inspiration as the fundamental base for the ENTIRE world. Total creative freedom WITHIN that inspiration, strict technical constraints for functionality. Create something unique, playable, and faithful to the inspiration!"""
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

#---- Incremental Generation Prompts -----------------------------------------

PROMPT_STEP_1_CONCEPT = """Eres un diseñador experto de mundos de ficción interactiva. Tu tarea es crear el concepto general de un mundo de aventura basado en el tema proporcionado.

**LIBERTAD CREATIVA TOTAL:**
- Inventa cualquier historia, tema, o ambientación (medieval, sci-fi, moderno, fantástico, etc.)
- Crea personajes únicos con personalidades interesantes
- Diseña un objetivo principal desafiante y atractivo
- Decide el tono (aventura, misterio, drama, comedia, etc.)

**INSPIRACIÓN TEMÁTICA (elige uno o combina):**
- **Misterio**: Resolver un crimen, encontrar un tesoro perdido, descubrir un secreto
- **Aventura**: Rescatar a alguien, explorar ruinas, completar una misión
- **Supervivencia**: Escapar de un lugar, conseguir recursos, encontrar la salida
- **Social**: Convencer personajes, reunir información, mediar conflictos
- **Exploración**: Descubrir nuevas áreas, mapear territorio, encontrar artefactos

**ELEMENTOS OBLIGATORIOS A DEFINIR:**
- Un título atractivo para la aventura
- Una historia de fondo que establezca el contexto y la atmósfera (coherente con el tema)
- Una descripción del personaje jugador y su rol en la historia
- Un objetivo principal claro, motivador y ESPECÍFICO que el jugador debe lograr

**REQUISITOS DEL OBJETIVO:**
- Debe ser CLARO y ESPECÍFICO (no vago como "explorar el mundo")
- Debe ser MOTIVADOR para el jugador
- Debe ser COMPLETABLE con elementos físicos del mundo
- Debe tener una razón narrativa sólida

**EJEMPLOS DE BUENOS OBJETIVOS:**
- "Encontrar la Espada Legendaria para derrotar al dragón"
- "Rescatar a la princesa del castillo encantado"
- "Descubrir el tesoro del pirata perdido"
- "Reunir los tres cristales para abrir el portal"

**EJEMPLOS DE MALOS OBJETIVOS:**
- "Explorar el mundo" (muy vago)
- "Ser feliz" (no específico)
- "Caminar por ahí" (no motivador)

El concepto debe ser cohesivo, interesante y proporcionar una base sólida para construir un mundo de aventura completo.

Tema: {theme}

**INSTRUCCIÓN DE IDIOMA CRÍTICA: La respuesta DEBE estar íntegramente en español. Todos los valores de texto (nombres, descripciones, etc.) deben ser generados en español. Las claves del JSON (como 'title', 'backstory', 'name') deben permanecer en inglés para coincidir con el esquema solicitado.**
"""

PROMPT_STEP_2_SKELETON = """Eres un arquitecto de mundos de ficción interactiva. Basándote en el concepto de mundo proporcionado, tu tarea es definir las entidades clave que formarán la estructura del mundo.

Concepto del mundo:
- Título: {title}
- Historia de fondo: {backstory}
- Concepto del jugador: {player_concept}
- Objetivo principal: {main_objective}

**ESTRUCTURA MÍNIMA REQUERIDA:**
- 2-3 ubicaciones: Los lugares más importantes para la historia y el objetivo
- 3-5 objetos: Los elementos físicos esenciales para completar el objetivo
- 2-3 personajes no jugadores: Los NPCs importantes que ayudarán o desafiarán al jugador

**REGLAS PARA EL ESQUELETO:**
1. **Enfoque en objetivo**: Cada entidad debe tener una conexión clara con el objetivo principal
2. **Ruta lógica**: Debe existir una secuencia lógica de ubicaciones y elementos para alcanzar el objetivo
3. **Dependencias claras**: Los objetos y personajes deben formar una cadena de dependencias hacia el objetivo

Para cada entidad, especifica su nombre y su propósito/rol en el mundo. Piensa en términos de la ruta principal hacia el objetivo y cómo cada elemento contribuye a esa ruta.

**EJEMPLO DE BUENA ESTRUCTURA:**
- Ubicación inicial → Ubicación con personaje clave → Ubicación con objeto importante → Ubicación objetivo
- Objeto inicial → Objeto para intercambio → Objeto final requerido
- Personaje informativo → Personaje que otorga objeto/acceso → Personaje objetivo (si aplica)

**INSTRUCCIÓN DE IDIOMA CRÍTICA: La respuesta DEBE estar íntegramente en español. Todos los valores de texto (nombres, descripciones, etc.) deben ser generados en español. Las claves del JSON deben permanecer en inglés para coincidir con el esquema solicitado.**
"""

PROMPT_STEP_3_DETAILS = """Eres un constructor de mundos de ficción interactiva. Tu tarea es tomar las entidades clave del esqueleto y desarrollarlas en un mundo detallado y jugable, enfocándote en la ruta principal hacia el objetivo.

Concepto del mundo:
- Título: {title}
- Historia de fondo: {backstory}
- Concepto del jugador: {player_concept}
- Objetivo principal: {main_objective}

Entidades clave a desarrollar:
{skeleton_data}

**RESTRICCIONES TÉCNICAS OBLIGATORIAS:**

**REGLAS DE CONEXIÓN OBLIGATORIAS:**
1. **Conexiones bidireccionales**: Si A conecta con B, entonces B DEBE conectar con A
2. **Conectividad global**: TODAS las ubicaciones deben ser accesibles desde cualquier punto del mundo - NO puede haber ubicaciones aisladas o grupos separados
3. **Objetivo alcanzable**: El objetivo DEBE ser completable con los elementos que crees
4. **Cadena de dependencias**: Debe existir al menos una ruta lógica desde el estado inicial hasta completar el objetivo

**REGLAS DE PERSONAJES:**
1. **Interacciones funcionales**: Si un personaje tiene `interaction`, DEBE tener `interaction_text`
2. **Inventarios válidos**: Todo objeto en inventarios de personajes DEBE existir en la lista de objetos del mundo
3. **Ubicaciones válidas**: Todos los personajes DEBEN estar ubicados en lugares que existen

**REGLAS DE OBJETOS:**
1. **Objetivos completables**: Si un objeto es requerido para el objetivo (`is_objective_target: true`), DEBE ser `gettable: true`
2. **Consistencia funcional**: Objetos decorativos pueden ser `gettable: false`, objetos funcionales DEBEN ser `gettable: true`
3. **Relevancia clara**: Cada objeto debe tener una razón de existir (funcional o atmosférica)

**VALIDACIÓN DE COMPLETABILIDAD:**
Antes de finalizar, verifica mentalmente:
1. **¿HAS DEFINIDO UN OBJETIVO PRINCIPAL CLARO?** (OBLIGATORIO)
2. **¿TODAS las ubicaciones son accesibles desde la ubicación inicial?** (OBLIGATORIO - no debe haber ubicaciones aisladas)
3. ¿Puede el jugador completar el objetivo con los elementos disponibles?
4. ¿Existe al menos una ruta de solución desde el estado inicial?
5. ¿Todos los elementos referenciados existen realmente en el mundo?
6. ¿Las interacciones de personajes están completas?

**EJEMPLO DE CADENA DE DEPENDENCIAS VÁLIDA:**
1. Jugador quiere [objetivo principal]
2. Para [objetivo] necesita [objeto/ubicación X]
3. Para conseguir X necesita [interactuar con personaje Y]
4. Personaje Y requiere [completar tarea/tener objeto Z]
5. El jugador puede conseguir Z directamente o mediante otro paso

Debes crear:
- Ubicaciones completas con descripciones atmosféricas y conexiones lógicas bidireccionales
- Objetos detallados con descripciones y propiedades apropiadas
- Personajes con personalidades, ubicaciones e interacciones básicas completas
- Un objetivo claro y específico con componentes definidos y alcanzables
- El personaje jugador en una ubicación inicial apropiada
- Cadenas de dependencias que muestren cómo completar el objetivo

IMPORTANTE: Enfócate solo en la ruta principal. No añadas puzzles complejos todavía - eso vendrá en el siguiente paso. Las interacciones de personajes deben ser directas y simples pero COMPLETAS.

**INSTRUCCIÓN DE IDIOMA CRÍTICA: La respuesta DEBE estar íntegramente en español. Todos los valores de texto (nombres, descripciones, etc.) deben ser generados en español. Las claves del JSON deben permanecer en inglés para coincidir con el esquema solicitado.**
"""

PROMPT_STEP_4_PUZZLES = """Eres un diseñador de cadenas de dependencias para ficción interactiva. Tu objetivo principal es tomar el mundo básico existente y transformarlo en una aventura compleja con múltiples pasos interconectados que el jugador debe completar para alcanzar su objetivo.

Mundo actual:
{world_data}

**OBJETIVO CRÍTICO:** En lugar de simplemente añadir puzzles aislados, debes crear CADENAS DE DEPENDENCIAS que hagan la progresión hacia el objetivo mucho más interesante y desafiante.

**EJEMPLO DE CADENA DE DEPENDENCIAS COMPLEJA:**
Objetivo: Conseguir el Amuleto Mágico
1. El Amuleto está en la Habitación Secreta, pero la puerta está bloqueada por un Candado Mágico
2. Para abrir el Candado Mágico necesitas la Palabra Clave que solo conoce el Mago
3. El Mago te dará la Palabra Clave, pero primero quiere que le traigas su Bastón Perdido
4. El Bastón está en poder del Comerciante, quien lo intercambiará por 3 Gemas
5. Para conseguir las 3 Gemas debes resolver el Acertijo del Guardián en la Cueva
6. Pero para entrar a la Cueva necesitas la Llave de Hierro que tiene la Anciana
7. La Anciana te dará la Llave si le traes una Poción Curativa del Herbolario
8. El Herbolario te dará la Poción a cambio de encontrar su Libro de Recetas...

**ESTRUCTURA DE CADENAS OBLIGATORIA:**
1. **Cadena principal**: La ruta principal hacia el objetivo debe tener AL MENOS de 3 a 6 pasos interdependientes
2. **Subcadenas**: Cada paso principal puede tener sus propias subcadenas de 1-3 pasos
3. **Múltiples rutas opcionales**: Donde sea posible, proporciona rutas alternativas para algunos pasos
4. **Puzzles integrados**: Los puzzles deben estar integrados orgánicamente en las cadenas

**REGLAS DE CADENAS DE DEPENDENCIAS:**
1. **Progresión lógica**: Cada paso debe ser una consecuencia lógica del anterior
2. **Motivación clara**: Cada personaje debe tener una razón convincente para sus peticiones
3. **Diversidad de tareas**: Combina diferentes tipos de desafíos (puzzles, intercambios, exploración, interacciones sociales)
4. **Escalado de dificultad**: Los desafíos deben volverse progresivamente más complejos
5. **Conectividad temática**: Todas las tareas deben estar conectadas con la historia principal

**TIPOS DE DEPENDENCIAS A CREAR:**
1. **Intercambios en cadena**: A quiere B de C, quien quiere D de E, etc.
2. **Información en cascada**: Para conseguir X necesitas saber Y, que se obtiene resolviendo Z
3. **Acceso progresivo**: Para llegar a A necesitas la llave B, que obtienes en C, accesible con objeto D
4. **Puzzles conectados**: Resolver puzzle A revela la pista para puzzle B, que desbloquea acceso a C
5. **Relaciones sociales**: Personaje A confía en ti solo si ayudas a personaje B primero

**REGLAS TÉCNICAS OBLIGATORIAS:**
1. **Conectividad global**: TODAS las ubicaciones deben seguir siendo accesibles - NO crear grupos aislados
2. **Elementos existentes**: Todas las referencias DEBEN apuntar a objetos/personajes/ubicaciones que existen
3. **Soluciones descubribles**: Cada puzzle DEBE tener pistas que el jugador pueda encontrar explorando
4. **Interacciones completas**: Todo personaje con interacción DEBE tener `interaction_text`
5. **Obstáculos lógicos**: Los obstáculos deben estar separados de sus soluciones

**ESTRATEGIAS PARA CREAR COMPLEJIDAD:**
1. **Bloquear acceso directo**: El objetivo no debe ser directamente accesible - añade obstáculos
2. **Requerir múltiples elementos**: Para el paso final se necesitan varios objetos/información
3. **Crear cuellos de botella**: Ciertos personajes clave que controlan múltiples recursos
4. **Esconder elementos críticos**: Objetos importantes en ubicaciones que requieren esfuerzo alcanzar
5. **Información fragmentada**: Dividir pistas importantes entre múltiples personajes/ubicaciones

**MODIFICACIONES REQUERIDAS AL MUNDO:**
1. **Expandir interacciones de personajes**: Añade peticiones, intercambios, información
2. **Añadir puzzles estratégicos**: Que bloqueen puntos críticos de la progresión
3. **Crear pasajes bloqueados**: Con obstáculos que requieren elementos de las cadenas
4. **Redistribuir objetos**: Mueve objetos importantes a ubicaciones menos accesibles
5. **Añadir nuevos elementos**: Si es necesario para crear las cadenas complejas

**VALIDACIÓN DE CADENAS:**
Antes de finalizar, verifica mentalmente:
1. **¿El camino al objetivo tiene AL MENOS 3-6 pasos principales?** (OBLIGATORIO)
2. **¿Cada paso tiene una motivación lógica y clara?**
3. **¿Hay variedad en los tipos de desafíos?**
4. **¿Todas las ubicaciones siguen siendo accesibles?**
5. **¿Todos los elementos referenciados existen?**
6. **¿Las cadenas son interesantes pero no frustrantes?**

Tu misión es convertir un mundo simple y directo en una aventura rica en la que cada logro se sienta ganado a través de exploración, ingenio e interacción social. ¡Haz que el jugador trabaje por su victoria!

**INSTRUCCIÓN DE IDIOMA CRÍTICA: La respuesta DEBE estar íntegramente en español. Todos los valores de texto (nombres, descripciones, etc.) deben ser generados en español. Las claves del JSON deben permanecer en inglés para coincidir con el esquema solicitado.**
"""

PROMPT_STEP_5_EXPANSION = """Eres un enriquecedor de mundos de ficción interactiva. Tu tarea es expandir el mundo existente con contenido adicional opcional que añada profundidad y exploration sin complicar excesivamente la ruta principal.

Mundo actual:
{world_data}

**REGLAS DE EXPANSIÓN OBLIGATORIAS:**
1. **Conexiones bidireccionales**: Si añades nuevas conexiones, A conecta con B entonces B DEBE conectar con A
2. **Conectividad global**: TODAS las ubicaciones (incluyendo las nuevas) deben ser accesibles desde cualquier punto - NO crear grupos aislados
3. **Elementos existentes**: Todas las referencias a objetos, ubicaciones o personajes DEBEN existir
4. **Coherencia temática**: Todo contenido nuevo debe ser coherente con el mundo existente
5. **No interferencia**: El contenido adicional NO debe alterar la ruta principal al objetivo
6. **Inventarios válidos**: Si añades objetos a inventarios de personajes, DEBEN existir en la lista de objetos

**REGLAS DE NUEVOS PUZZLES OPCIONALES:**
Si añades puzzles opcionales, deben seguir las mismas reglas que los puzzles principales:
- **Soluciones descubribles**: Pistas físicas, diálogos o documentos que revelen la solución
- **Lógica interna**: Deben hacer sentido dentro del contexto
- **Recompensas existentes**: Las recompensas DEBEN existir en el mundo

**TIPOS DE EXPANSIÓN RECOMENDADOS:**
1. **Ubicaciones atmosféricas**: Lugares que enriquezcan la ambientación sin ser necesarios
2. **Objetos decorativos**: Elementos que añadan inmersión (`gettable: false` está bien)
3. **Personajes secundarios**: NPCs con historias paralelas o información adicional
4. **Detalles descriptivos**: Enriquecimiento de descripciones existentes

Debes añadir:
- **Ubicaciones secundarias opcionales** que enriquezcan la exploración pero mantengan conexiones lógicas
- **Objetos decorativos o de ambiente** que añadan inmersión sin alterar la jugabilidad principal
- **Personajes secundarios** que proporcionen contexto o historias paralelas (con interacciones completas)
- **Puzzles opcionales** con recompensas menores (siguiendo las reglas de puzzles descubribles)
- **Detalles adicionales** que enriquezcan las descripciones existentes

El contenido adicional debe:
- Ser opcional para completar el objetivo principal
- Enriquecer la experiencia sin confundir al jugador
- Mantener la coherencia temática ABSOLUTA
- Proporcionar recompensas menores pero satisfactorias
- Seguir todas las reglas técnicas del mundo principal

**VALIDACIÓN DE EXPANSIÓN:**
Antes de finalizar, verifica mentalmente:
1. **¿TODAS las ubicaciones (originales y nuevas) son accesibles desde cualquier punto?** (OBLIGATORIO)
2. ¿Todas las nuevas conexiones son bidireccionales?
3. ¿Todos los elementos referenciados existen en el mundo?
4. ¿El contenido adicional mantiene la coherencia temática?
5. ¿La ruta principal sigue siendo clara y no se ve interferida?
6. ¿Los nuevos personajes tienen interacciones completas?

**INSTRUCCIÓN DE IDIOMA CRÍTICA: La respuesta DEBE estar íntegramente en español. Todos los valores de texto (nombres, descripciones, etc.) deben ser generados en español. Las claves del JSON deben permanecer en inglés para coincidir con el esquema solicitado.**
"""

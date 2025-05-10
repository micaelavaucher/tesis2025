def prompt_narrate_current_scene (world_state: str) -> str:
    prompt = f"""You are a storyteller. Take the following state of the world and narrate it in a few sentences. Be careful not to include details that contradict the current state of the world or that move the story forward. Also, try to use simple sentences, being concise and exhaustive.
    
    This is the state of the world at the moment:
    {world_state}
    """

    return prompt

def prompt_world_update (world_state: str, input: str) -> str:
    prompt = f"""You are a storyteller. You are managing a fictional world, and the player can interact with it. This is the state of the world at the moment:
    {world_state}\n\n
    Explain the changes in the world after the player actions in this input "{input}". 
    
    Here are some clarifications. If a passage is blocked, then the player must unblock it before being able to reach the place. Pay atenttion to the description of the components and their capabilities.
    Do not assume that the given input always make sense; maybe those actions try to do something that the world does not allow.
    Follow always the following format with the three categories, using "None" in each case if there are no changes and repeat the category for each case (there may be more than 3 items in the list):
    - Moved object: <object> now is in <new_location>
    - Blocked passages now available: <now_reachable_location>
    - Your location changed: <new_location>
    
    Here you have some examples. 
    Example 1
    - Moved object: <axe> now is in <Inventory>
    - Blocked passages now available: None
    - Your location changed: None

    Example 2
    - Moved object: None
    - Blocked passages now available: None
    - Your location changed: <Garden>

    Example 3
    - Moved object: <banana> now is in <Inventory>,  <bottle> now is in <Inventory>,  <axe> now is in <Main Hall>
    - Blocked passages now available: None
    - Your location changed: None

    Example 4
    - Moved object: <banana> now is in <Inventory>,  <bottle> now is in <Inventory>,  <axe> now is in <Main Hall>
    - Blocked passages now available: <Small room>
    - Your location changed: None

    Example 5
    - Moved object: <banana> now is in <Inventory>,  <bottle> now is in <Inventory>,  <axe> now is in <Main Hall>
    - Blocked passages now available: <Small room>
    - Your location changed:  <Small room>

    Example 6
    - Moved object: <book> now is in <John>,  <pencil> now is in <Inventory>
    - Blocked passages now available: None
    - Your location changed:  None

    Example 7
    - Moved object: <computer> now is in <Susan>
    - Blocked passages now available: None
    - Your location changed:  None
    

    Finally, you can add a final short sentence narrating the detected changes in the state of the world (without moving the story forward and creating details not included in the state of the world!) or answering a question of the player, using the format: #<your final sentence>#
    """

    return prompt

def prompt_generate_world() -> str:
    """Prompt for generating a new world from scratch."""
    prompt = """You are a creative world architect for an interactive fiction game. Generate a small, coherent world with:

    1. 3-4 locations (each with a name and 2-3 descriptive sentences)
    2. 5-7 unique items (with names and 2-3 descriptive sentences)
    3. 2-3 non-player characters (with names, descriptions, and placed in specific locations)
    4. One player character (with a name, description, starting inventory, and starting location)

    Make everything interconnected and logical. Locations should connect to at least one other location. Some locations can have blocked passages requiring specific items to unblock.

    Ensure the world has an interesting theme or premise with potential for exploration and simple puzzles.
    """
    return prompt

def prompt_expand_world(world_state: str, player_location: str) -> str:
    """Prompt for expanding the world based on the current state."""
    prompt = f"""You are a creative world architect for an interactive fiction game. Based on the current world state, expand the world organically by adding:

    1. 1-2 new locations connected to {player_location} (with names and 2-3 descriptive sentences)
    2. 2-3 new items placed in these new locations (with names and 2-3 descriptive sentences) 
    3. 0-1 new non-player characters in one of the new locations (with a name, description, and possibly inventory)

    Make your additions coherent with the existing world state:
    {world_state}

    Consider creating:
    - Hidden areas that extend the current location
    - New passages that were previously not noticed
    - Items that fit the theme of the new areas
    - Characters that have interesting relationships with existing elements

    The expansion should feel natural, as if these elements were always there but just now discovered.
    """
    return prompt

def should_expand_world(player_input: str) -> bool:
    """Determine if the world should be expanded based on player input.
    
    Expansion triggers:
    - Player explicitly explores or searches
    - Player tries to go somewhere not currently available
    - Player has visited all available locations
    - Player has interacted with most available items
    """
    exploration_keywords = [
        "explore", "search", "look around", "investigate", 
        "examine surroundings", "check area", "discover"
    ]
    
    for keyword in exploration_keywords:
        if keyword in player_input.lower():
            return True
    
    return False
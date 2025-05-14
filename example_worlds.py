"""Includes two example worlds to experiment with different scenarios."""

import json
from models import GeminiModel
from world import Character, Item, Location, World


def generate_initial_world(inspiration: str, model: GeminiModel) -> World:
    """Generate the initial world based on the selected theme using the Gemini model."""
    prompt = f"""
    You are tasked with creating a fictional world for an interactive storytelling game. 
    The user has provided the following as inspiration for the world:
    "{inspiration}"
    The world must have:
    - A minimum of 4 locations and a maximum of 10 locations.
    - Each location must have at least 1 item.
    - All locations must be connected, meaning every location must be reachable from at least one other location.
    - If any location is blocked, there must be a way to unblock it.
    - Each location should have a short, unique name and 1-3 natural language descriptions.
    - Each item should have a short, unique name, 1-3 natural language descriptions, and a boolean indicating if it is gettable (default is True).
    - At least two notable characters (NPCs) should be present in the world, each with a unique name and 1-3 natural language descriptions.

    Respond ONLY with a JSON object containing:
    - player: An object with the player's name, descriptions, inventory (list of items).
    - locations: A list of locations, where each location has:
        - name: The name of the location.
        - descriptions: A list of descriptions for the location.
        - items: A list of items, where each item has:
            - name: The name of the item.
            - descriptions: A list of descriptions for the item.
            - gettable: A boolean indicating if the item is gettable. 
        - npcs: A list of NPCs present in this location, where each NPC has:
            - name: The name of the NPC.
            - descriptions: A list of descriptions for the NPC.
        - blocked_locations: A dictionary where the key is the name of a blocked location, and the value is an object with:
            - obstacle: The name of the obstacle blocking the location, it's name must be unique from the others.
            - symmetric: A boolean indicating if the block is symmetric.
        - connected_locations: A list of names of locations that are directly connected to this location. Including blocked ones.

    Respond ONLY with the JSON object.
    """
    try:
        # Get the response from Gemini
        response = model.prompt_model(prompt)
        if response.startswith("```json"):
            response = response.replace("```json", "", 1)
        if response.endswith("```"):
            response = response.replace("```", "", 1)
        response = response.strip()

        # Parse the response as JSON
        world_data = json.loads(response)

        # Create the world
        # Create the world
        # First create all items to reference them later
        all_items = {}
        for location_data in world_data["locations"]:
            for item_data in location_data["items"]:
                item = Item(
                    name=item_data["name"],
                    descriptions=item_data["descriptions"],
                    gettable=item_data.get("gettable", True)
                )
                all_items[item.name] = item
        
        # Create player inventory items first
        player_inventory = []
        for item_name in world_data["player"].get("inventory", []):
            if isinstance(item_name, dict):
                # Handle case where inventory contains full item objects instead of just names
                item = Item(
                    name=item_name["name"],
                    descriptions=item_name["descriptions"],
                    gettable=item_name.get("gettable", True)
                )
                all_items[item.name] = item
                player_inventory.append(item)
            else:
                # Handle case where inventory contains just item names
                # We'll need to create these items later if they don't exist yet
                if item_name not in all_items:
                    # Create a default item if not found
                    item = Item(name=item_name, descriptions=[f"A {item_name}"])
                    all_items[item_name] = item
                player_inventory.append(all_items[item_name])
        
        # Create all locations (without connections yet)
        locations = {}
        for location_data in world_data["locations"]:
            location_items = []
            for item_data in location_data["items"]:
                if item_data["name"] in all_items:
                    location_items.append(all_items[item_data["name"]])
                else:
                    item = Item(
                        name=item_data["name"],
                        descriptions=item_data["descriptions"],
                        gettable=item_data.get("gettable", True)
                    )
                    all_items[item.name] = item
                    location_items.append(item)
            
            location = Location(
                name=location_data["name"],
                descriptions=location_data["descriptions"],
                items=location_items
            )
            locations[location.name] = location
        
        # Set the starting location for the player (first location if not specified)
        player_location = locations[world_data["locations"][0]["name"]]
        
        # Create the player and the world
        player = Character(
            name=world_data["player"]["name"],
            descriptions=world_data["player"]["descriptions"],
            inventory=player_inventory,
            location=player_location
        )
        
        the_world = World(player)
        
        # Add all locations to the world first
        for location in locations.values():
            the_world.add_location(location)
        
        # Add all items to the world
        for item in all_items.values():
            the_world.add_item(item)
        
        # Create NPCs and add them to their locations
        for location_data in world_data["locations"]:
            if "npcs" in location_data:
                for npc_data in location_data["npcs"]:
                    npc_inventory = []
                    if "inventory" in npc_data:
                        for item_name in npc_data["inventory"]:
                            if isinstance(item_name, dict):
                                item = Item(
                                    name=item_name["name"],
                                    descriptions=item_name["descriptions"],
                                    gettable=item_name.get("gettable", True)
                                )
                                all_items[item.name] = item
                                npc_inventory.append(item)
                            else:
                                if item_name in all_items:
                                    npc_inventory.append(all_items[item_name])
                    
                    npc = Character(
                        name=npc_data["name"],
                        descriptions=npc_data["descriptions"],
                        inventory=npc_inventory,
                        location=locations[location_data["name"]]
                    )
                    the_world.add_character(npc)
        
        # Connect locations
        for location_data in world_data["locations"]:
            location = locations[location_data["name"]]
            
            # Handle regular connections
            for connected_name in location_data.get("connected_locations", []):
                if connected_name in locations:
                    location.connecting_locations.append(locations[connected_name])
            
            # Handle blocked passages
            for blocked_name, block_data in location_data.get("blocked_locations", {}).items():
                if blocked_name in locations:
                    obstacle_name = block_data["obstacle"]
                    symmetric = block_data.get("symmetric", True)
                    
                    # Create the obstacle item if it doesn't exist
                    if obstacle_name not in all_items:
                        obstacle = Item(
                            name=obstacle_name,
                            descriptions=[f"An obstacle blocking the way to {blocked_name}"],
                            gettable=False
                        )
                        all_items[obstacle_name] = obstacle
                        the_world.add_item(obstacle)
                    else:
                        obstacle = all_items[obstacle_name]
                    
                    # Add the blocked location to connecting_locations first
                    location.connecting_locations.append(locations[blocked_name])
                    # Then block it
                    location.block_passage(locations[blocked_name], obstacle, symmetric)
        
        return the_world
    
    except Exception as e:
        print(f"Error generating world: {e}")
        return None
        

def get_world(arg: str) -> World:
    if arg=='2':
        return get_world_2()
    return get_world_1()

def get_world_1() -> World:
    """A simple fictional world, used as an example in Figure 3 of the paper."""
    item_1 = Item("Apple",
                  ["A fruit that can be eaten", "It is round-shaped and green"])
    item_2 = Item("Toy car",
                  ["A tiny toy purple car", "It looks brand new"])
    item_3 = Item("Mate",
                  ["A classical mate, ready to drink!", "It contains some yerba", "You can drink this to boost your energy!"])

    place_1 = Location("Garden",
                       ["A beautiful garden", "There is a statue in the center"],
                       items = [item_2])
    place_2 = Location("Cabin",
                       ["A small cabin", "It looks like no one has lived here for a while"])
    place_3 = Location("Mansion hall",
                       ["A big hall", "There is a big staircase"])

    place_1.connecting_locations+=[place_2,place_3]
    place_2.connecting_locations+=[place_1]
    place_3.connecting_locations+=[place_1]

    player = Character("Alicia",
                       ["She is wearing a long skirt","She likes to sing"],
                       inventory=[item_1],
                       location=place_1)
    npc = Character("Javier",
                    ["He has a long beard", "He loves to restore furtniture"],
                    inventory=[item_3],
                    location=place_3)

    the_world = World(player)
    the_world.add_locations([place_1, place_2, place_3])
    the_world.add_items([item_1, item_2, item_3])
    the_world.add_character(npc)

    return the_world

def get_world_2() -> World:
    """Use this world to test more complex cases, like blocked passages between locations."""
    item_1 = Item("Apple",
                  ["A fruit that can be eaten", "It is round-shaped and red"])
    item_2 = Item("Key",
                  ["A key to open a lock", "It is golden", "It is engraved with a strange coat of arms"])
    item_3 = Item("A grey Hammer",
                  ["A great grey hammer that can be used to break things", "It is so heavy..."])
    item_4 = Item("Lock",
                  ["A strong lock engraved with a coat of arms", "It seems that you cannot open it with your hands"])
    item_5 = Item("Note",
                  ["A paper with a note", "You can read 'Go to the kitchen to know the truth'"])
    item_6 = Item("Flashlight",
                  ["A flashlight without batteries"])
    item_7 = Item("A green Hammer",
                  ["A small green hammer", "It is just a toy and you cannot break anything with it."])
    item_8 = Item("A wall of flames",
                  ["The heat is really intense but it is a small fire anyway"])
    item_9 = Item("A metal flower",
                  ["A strange flower"])
    item_10 = Item("A fire extinguisher",
                   ["You can control small fires with this."])

    place_3 = Location ("Garden",
                        ["A small garden below the kitchen"],
                        items = [item_9])
    place_2 = Location("Kitchen",
                       ["A beautiful well-lit kitchen"],
                       items = [item_6,item_10])
    place_2.connecting_locations = [place_3]
    place_2.block_passage(place_3, item_8, symmetric=False)

    place_1 = Location("Cellar",
                       ["There is a metal door locked by a lock", "You can see damp patches on the walls"],
                       items = [item_2, item_3, item_5, item_7])
    place_1.connecting_locations = [place_2]
    place_1.block_passage(place_2, item_4)

    player = Character("Cid",
                       ["A tall soldier"],
                       inventory = [item_1],
                       location = place_1)
    npc = Character("Elvira",
                            ["A little girl", "Her favorite food is apple pie, but she enjoys eating any fruit", "She can't read yet"],
                            location= place_1)

    the_world = World(player)
    the_world.add_locations([place_1,place_2,place_3])
    the_world.add_items([item_1,item_2,item_3,item_4,item_5,
                         item_6, item_7,item_8, item_9, item_10])
    the_world.add_character(npc)

    return the_world

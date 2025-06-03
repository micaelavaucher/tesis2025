"""Implement the main loop for the PAYADOR approach, described in Fig.3 of the paper.

The main steps in the loop are:
- Describe the ficional world in simple sentences
- Get the player input
- Prompt a model to predict the outcomes in the world, after the actions described by the player.
"""

import re
import sys

import example_worlds
from models import GeminiModel
from prompts import (
    prompt_narrate_current_scene,
    prompt_world_update,
    prompt_generate_world,
    prompt_expand_world,
    should_expand_world)
from structured_data_models import GeneratedWorld, WorldExpansion
from world_builder import (
    create_world_from_llm_response, expand_world_from_llm_response)

# Check if we should use a preset world or generate a new one
use_preset = len(sys.argv) > 1 and sys.argv[1] in ["1", "2"]

# Initialize the model and disable the safety settings
model = GeminiModel("API_key")

# Welcome the user
print ("""
PAYADOR is an approach to tackle the world-update problem in Interactive Storytelling.
This proof of concept is intended to ease research on the aforementioned problem and other related tasks. 

The system will print the current 🌎 World state 🌍 and a possible 📖 narration 📖 for it.
Then you will be asked to enter some action(s), and the system will try to predict the outcomes. 

Enter "q" to quit.
""")

# Generate or load a world
if use_preset:
    world_id = sys.argv[1]
    world = example_worlds.get_world(world_id)
    print("Using preset world...")
else:
    print("Generating a new world...")
    world_prompt = prompt_generate_world()
    world_response = model.prompt_model_structured(world_prompt, GeneratedWorld)

    # For debugging
    print("World generation reponse received, creating world...")

    try:
        world = create_world_from_llm_response(world_response)
        print("New world created successfully!")
    except Exception as e:
        print(f"Error creating world: {e}")
        print("\nFalling back to preset world...")
        world = example_worlds.get_world("1")

# Track player's position and visited locations
last_player_position = None
visited_locations = set()
expansion_cooldown = 0 #-- prevent too frequent exapnsion

while(True):
    # Show the state of the world
    print(f"🌎 World state 🌍\n{world.render_world()}\n")

    # Track visited locations
    visited_locations.add(world.player.location.name)

    # If the player is in a different place, narrate the scene
    if last_player_position is not world.player.location:
        last_player_position = world.player.location
        prompt_scene = prompt_narrate_current_scene(world.render_world())
        response_scene = model.prompt_model(prompt_scene)
        print("\n📖 Narration of the scene 📖")
        try:
            print(f"{response_scene}\n")
        except Exception as e:
            print (f"Error: {e}")

    # Take the input from the user
    user_input = input("\nWhat do you want to do?\n\t\t\t👉 ")
    if user_input == "q":
        break

    # Create the prompt and run the model
    prompt_update = prompt_world_update(world.render_world(), user_input)
    response_update = model.prompt_model(prompt_update)

    # Show the detected changes in the fictional world
    print("\n🛠️ Predicted outcomes of the player input 🛠️")
    try:
        print(f"{re.sub(r'#([^#]*?)#','',response_update)}\n")
    except Exception as e:
        print (f"Error: {e}")

    # Show a narration for those changes
    print("\n📖 Narration of the predicted outcomes 📖")
    try:
        print(f"{re.findall(r'#([^#]*?)#',response_update)[0]}\n")
    except Exception as e:
        print (f"Error: {e}")

    # Parse the response and update the world
    world.parse_updates(response_update)

    # Check if we should expand the world
    expansion_cooldown -= 1

    # Expansion conditions:
    # 1. Player explicitly request exploration
    # 2. Player has visited all available locations
    # 3. Cooldown period has passed
    should_expand = (
        should_expand_world(user_input) or
        (len(visited_locations) >= len(world.locations))
    ) and expansion_cooldown <= 0

    if should_expand:
        print("\n🌱 Expanding the world...🌱")

        expansion_prompt = prompt_expand_world(
            world.render_world(),
            world.player.location.name)
        
        expansion_response = model.prompt_model_structured(expansion_prompt, WorldExpansion)

        try:
            expand_world_from_llm_response(world, expansion_response)
            print("World expanded with new areas to explore!\n")

            # Set cooldown to prevent too frequent expansions
            expansion_cooldown = 5
        except Exception as e:
            print(f"Error expanding world: {e}")

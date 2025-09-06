#!/usr/bin/env python3
"""Simple test for mystery objective functionality."""

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.payador.core.world import Character, Item, Location, World, MysteryObjective, MysteryClue
from src.payador.core.game_logic import get_objective_info

def test_mystery_objective_display():
    """Test that mystery objectives display properly with clue progress."""
    
    print("=== Testing Mystery Objective Display ===")
    
    # Create test world components
    location = Location("Test Room", ["A simple test room"])
    player = Character("Detective", ["A skilled detective"], location)
    
    # Create test items
    evidence1 = Item("Bloody Knife", ["A knife with blood stains"], location)
    evidence2 = Item("Letter", ["A threatening letter"], location)
    
    # Create mystery clues
    clue1 = MysteryClue(
        name="Blood Evidence",
        description="The blood type matches the victim",
        associated_item="Bloody Knife",
        item_location="Test Room",
        relevance_to_mystery="Links the weapon to the crime"
    )
    
    clue2 = MysteryClue(
        name="Threatening Message",
        description="The letter threatens the victim",
        associated_item="Letter", 
        item_location="Test Room",
        relevance_to_mystery="Shows motive for the crime"
    )
    
    # Create mystery objective
    mystery_obj = MysteryObjective(
        name="Murder Investigation",
        description="Solve the murder of John Doe by finding the killer",
        clues=[clue1, clue2],
        mystery_solution="The killer is revealed through the blood evidence and threatening letter"
    )
    
    # Create world and set objective
    world = World(player)
    world.add_location(location)
    world.add_item(evidence1)
    world.add_item(evidence2)
    world.set_objective(player, mystery_obj)
    
    # Test initial objective display (no clues discovered)
    print("\n--- Initial State (No clues discovered) ---")
    objective_info_en = get_objective_info(world, 'en')
    objective_info_es = get_objective_info(world, 'es')
    
    print("English:")
    print(objective_info_en)
    print("\nSpanish:")
    print(objective_info_es)
    
    # Discover first clue by interacting with evidence
    print("\n--- Discovering first clue ---")
    discovery_msg = world._check_mystery_clue_discovery("Bloody Knife")
    print(f"Discovery message: {discovery_msg}")
    
    # Show updated objective display
    print("\n--- After first clue discovery ---")
    objective_info_en = get_objective_info(world, 'en')
    print("English:")
    print(objective_info_en)
    
    # Discover second clue
    print("\n--- Discovering second clue ---")
    discovery_msg = world._check_mystery_clue_discovery("Letter")
    print(f"Discovery message: {discovery_msg}")
    
    # Show final objective display
    print("\n--- After all clues discovered ---")
    objective_info_en = get_objective_info(world, 'en')
    print("English:")
    print(objective_info_en)
    
    # Test completion check
    print("\n--- Testing completion ---")
    is_complete = mystery_obj.is_completed()
    progress = mystery_obj.get_completion_progress()
    print(f"Mystery completed: {is_complete}")
    print(f"Progress: {progress[0]}/{progress[1]} clues discovered")
    
    print("\n=== Test completed successfully! ===")

if __name__ == "__main__":
    test_mystery_objective_display()

#!/usr/bin/env python3
"""Test script to validate mystery objective clue validation."""

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(__file__))

from src.payador.core.world_builder import set_objective_from_generated
from src.payador.core.world import Item, Character, Location, MysteryObjective, MysteryClue
from src.payador.llm.structured_data_models import GeneratedObjective, ObjectiveType, MysteryClue as MysteryClueData, ObjectiveComponent, ComponentType

def test_mystery_clue_validation():
    """Test that mystery clues with non-existent items are properly handled."""
    
    print("🧪 Testing mystery clue validation...")
    
    # Create a simple world with some items
    items_dict = {
        "Diary": Item("Diary", ["An old diary"], gettable=True),
        "Letter": Item("Letter", ["A yellowed letter"], gettable=True),
        "Photo": Item("Photo", ["A faded photograph"], gettable=True)
    }
    
    locations_dict = {
        "Study": Location("Study", ["A cozy study room"])
    }
    
    # Create a player character
    player = Character("Player", ["The protagonist"], location=locations_dict["Study"])
    characters_list = [player]
    
    # Create mystery clues - some valid, some invalid
    clue_data_list = [
        MysteryClueData(
            name="First Clue",
            description="Information about the mystery",
            associated_item="Diary",  # This exists
            relevance_to_mystery="Provides background",
            discovered=False
        ),
        MysteryClueData(
            name="Second Clue", 
            description="More mystery information",
            associated_item="Dinero",  # This DOESN'T exist - should be filtered out
            relevance_to_mystery="Shows motive",
            discovered=False
        ),
        MysteryClueData(
            name="Third Clue",
            description="Final piece of the puzzle",
            associated_item="Letter",  # This exists
            relevance_to_mystery="Reveals the truth",
            discovered=False
        )
    ]
    
    # Create objective data
    objective_data = GeneratedObjective(
        type=ObjectiveType.SOLVE_MYSTERY,
        components=[],  # Not needed for mystery objectives
        description="Solve the mystery of the missing inheritance",
        success_conditions=["Discover all clues"],
        mystery_clues=clue_data_list,
        mystery_solution="The butler did it!"
    )
    
    print("📋 Input clues:")
    for i, clue in enumerate(clue_data_list, 1):
        exists = "✅" if clue.associated_item in items_dict else "❌"
        print(f"   {i}. {clue.name} → {clue.associated_item} {exists}")
    
    print("\n🔧 Running validation...")
    
    # Test the validation
    result = set_objective_from_generated(
        objective_data, 
        items_dict, 
        locations_dict, 
        characters_list, 
        player
    )
    
    if result is None:
        print("❌ No objective created (all clues were invalid)")
        return False
    
    player_obj, mystery_obj = result
    
    print(f"\n✅ Mystery objective created with {len(mystery_obj.clues)} valid clues:")
    for i, clue in enumerate(mystery_obj.clues, 1):
        print(f"   {i}. {clue.name} → {clue.associated_item}")
    
    # Verify that only valid clues were included
    expected_valid_clues = ["Diary", "Letter"]
    actual_clue_items = [clue.associated_item for clue in mystery_obj.clues]
    
    if set(actual_clue_items) == set(expected_valid_clues):
        print("✅ Validation working correctly - invalid clues filtered out!")
        return True
    else:
        print(f"❌ Validation failed - expected {expected_valid_clues}, got {actual_clue_items}")
        return False

if __name__ == "__main__":
    success = test_mystery_clue_validation()
    if success:
        print("\n🎉 Test passed! Mystery clue validation is working correctly.")
    else:
        print("\n💥 Test failed! Mystery clue validation needs work.")
    
    sys.exit(0 if success else 1)

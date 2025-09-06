#!/usr/bin/env python3
"""Test script for the mystery objective system."""

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.payador.core.world import Character, Item, Location, World, MysteryObjective, MysteryClue
from src.payador.core.game_logic import get_objective_info
from src.payador.llm.structured_data_models import StructuredWorldUpdate

def create_test_mystery_world():
    """Create a test world with a mystery objective."""
    
    # Create locations
    study = Location("Study", ["A scholarly room filled with books and papers", "Sunlight streams through tall windows"])
    library = Location("Library", ["An impressive collection of ancient texts", "Dust motes dance in the filtered light"])
    
    # Connect locations
    study.add_connection("north", library)
    library.add_connection("south", study)
    
    # Create items with clues
    diary = Item("Diary", ["An old leather-bound diary", "Contains handwritten entries"], gettable=True)
    photograph = Item("Photograph", ["A faded photograph", "Shows a family portrait from long ago"], gettable=True)
    letter = Item("Letter", ["A yellowed letter", "Written in elegant handwriting"], gettable=True)
    locked_box = Item("Locked Box", ["A wooden box with an intricate lock", "Seems to contain something important"], gettable=False)
    
    # Create mystery clues
    clue1 = MysteryClue(
        name="Family Secret",
        description="The diary reveals a hidden family secret about a missing inheritance",
        associated_item="Diary",
        relevance_to_mystery="Shows motivation for the disappearance"
    )
    
    clue2 = MysteryClue(
        name="Last Seen",
        description="The photograph shows Uncle Henry on the day he vanished",
        associated_item="Photograph", 
        relevance_to_mystery="Establishes timeline of disappearance"
    )
    
    clue3 = MysteryClue(
        name="Hidden Message",
        description="The letter contains a coded message about a secret location",
        associated_item="Letter",
        relevance_to_mystery="Reveals where Uncle Henry might have gone"
    )
    
    # Create mystery objective
    mystery_objective = MysteryObjective(
        name="The Mystery of Uncle Henry",
        description="Discover what happened to Uncle Henry who disappeared 20 years ago",
        clues=[clue1, clue2, clue3],
        mystery_solution="Uncle Henry faked his disappearance to escape debts and started a new life under a false identity"
    )
    
    # Create world
    world = World()
    world.add_location(study)
    world.add_location(library)
    
    # Place items in locations
    study.add_item(diary)
    study.add_item(photograph)
    library.add_item(letter)
    library.add_item(locked_box)
    
    world.add_items([diary, photograph, letter, locked_box])
    
    # Create player and set location
    world.player.location = study
    
    # Set the mystery objective
    world.objective = ("solve_mystery", mystery_objective)
    
    return world

def test_mystery_clue_discovery():
    """Test the mystery clue discovery mechanism."""
    print("🧪 Testing PAYADOR Mystery Objective System\n")
    
    # Create test world
    world = create_test_mystery_world()
    mystery_objective = world.objective[1]
    
    print("✅ Created test world with mystery objective")
    print(f"📍 Player location: {world.player.location.name}")
    print(f"🔍 Mystery: {mystery_objective.description}")
    print(f"💡 Total clues: {len(mystery_objective.clues)}")
    
    # Test initial state
    print("\n" + "="*60)
    print("Testing initial mystery state:")
    print("="*60)
    
    print("\n📊 Initial Progress:")
    print(get_objective_info(world, 'en'))
    
    discovered, total = mystery_objective.get_completion_progress()
    print(f"\n✅ Progress: {discovered}/{total} clues discovered")
    print(f"🎯 Completed: {mystery_objective.is_completed()}")
    
    # Test clue discovery through item interaction
    print("\n" + "="*60)
    print("Testing clue discovery through item interactions:")
    print("="*60)
    
    # Simulate picking up the diary (this should discover the first clue)
    print("\n🔍 Test 1: Interacting with Diary")
    
    # Create a structured update that moves the diary to the player
    world_update = StructuredWorldUpdate(
        moved_objects=[{
            "object_name": "Diary",
            "previous_location": "Study", 
            "new_location": "Player"
        }],
        blocked_passages_now_available=[],
        player_location_changed=None,
        puzzles_solved=[]
    )
    
    # Update the world using the structured update
    response = world.update_from_structured(world_update)
    print(f"💭 World update response: {response}")
    
    # Check if the clue was discovered
    discovered, total = mystery_objective.get_completion_progress()
    print(f"📊 Progress after diary: {discovered}/{total} clues discovered")
    
    if discovered > 0:
        print("✅ Clue discovered successfully!")
        for clue in mystery_objective.get_discovered_clues():
            print(f"   • {clue.name}: {clue.description}")
    else:
        print("❌ No clue discovered - this might indicate a problem")
    
    # Test second clue discovery
    print("\n🔍 Test 2: Interacting with Photograph")
    
    world_update2 = StructuredWorldUpdate(
        moved_objects=[{
            "object_name": "Photograph",
            "previous_location": "Study",
            "new_location": "Player"
        }],
        blocked_passages_now_available=[],
        player_location_changed=None,
        puzzles_solved=[]
    )
    
    response2 = world.update_from_structured(world_update2)
    print(f"💭 World update response: {response2}")
    
    discovered, total = mystery_objective.get_completion_progress()
    print(f"📊 Progress after photograph: {discovered}/{total} clues discovered")
    
    # Move to library and get the letter
    print("\n🔍 Test 3: Moving to Library and interacting with Letter")
    
    world_update3 = StructuredWorldUpdate(
        moved_objects=[{
            "object_name": "Letter",
            "previous_location": "Library",
            "new_location": "Player"
        }],
        blocked_passages_now_available=[],
        player_location_changed="Library",
        puzzles_solved=[]
    )
    
    response3 = world.update_from_structured(world_update3)
    print(f"💭 World update response: {response3}")
    
    discovered, total = mystery_objective.get_completion_progress()
    print(f"📊 Final progress: {discovered}/{total} clues discovered")
    print(f"🎯 Mystery completed: {mystery_objective.is_completed()}")
    
    # Test final objective state
    print("\n" + "="*60)
    print("Testing completed mystery objective:")
    print("="*60)
    
    print("\n📊 Final Mystery State:")
    print(get_objective_info(world, 'en'))
    
    if mystery_objective.is_completed():
        print("\n🎉 SUCCESS: Mystery objective completed successfully!")
        print(f"🎯 Solution: {mystery_objective.mystery_solution}")
    else:
        print(f"\n❌ INCOMPLETE: Mystery not completed. Progress: {discovered}/{total}")
    
    # Test objective checking
    print("\n" + "="*60)
    print("Testing objective completion checking:")
    print("="*60)
    
    objective_completed = world.check_objective()
    print(f"🏆 World.check_objective() result: {objective_completed}")
    
    if objective_completed != mystery_objective.is_completed():
        print("❌ ERROR: Mismatch between world.check_objective() and mystery_objective.is_completed()")
    else:
        print("✅ SUCCESS: Objective checking methods are consistent")
    
    print("\n✅ Mystery objective test completed!")

def test_bilingual_support():
    """Test the bilingual support for mystery objectives."""
    print("\n" + "="*60)
    print("Testing bilingual support:")
    print("="*60)
    
    world = create_test_mystery_world()
    
    # Test in English
    print("\n🇺🇸 English version:")
    print(get_objective_info(world, 'en'))
    
    # Test in Spanish
    print("\n🇪🇸 Spanish version:")
    print(get_objective_info(world, 'es'))

if __name__ == "__main__":
    test_mystery_clue_discovery()
    test_bilingual_support()

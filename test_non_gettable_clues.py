#!/usr/bin/env python3
"""Test script to verify clue discovery for non-gettable items works correctly."""

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.payador.core.world import World, Character, Item, Location, MysteryObjective, MysteryClue
from src.payador.llm.structured_data_models import WorldUpdate, MovedObject, BlockedPassageStatus, LocationChange, PuzzleSolution

def test_non_gettable_clue_discovery():
    """Test that clues are discovered when interacting with non-gettable items."""
    print("🧪 Testing clue discovery for non-gettable items...\n")
    
    # Create test location
    bank = Location("Bank", ["The bank where the robbery occurred"])
    
    # Create player
    player = Character("Detective", ["A skilled detective"], bank)
    
    # Create a heavy safe that can't be picked up (gettable=False)
    safe = Item("Heavy Safe", ["A large safe that's too heavy to move", "Shows signs of being forced open"], bank)
    safe.gettable = False  # This is the key - item can't be taken
    
    # Create a mystery clue associated with the safe
    clue = MysteryClue(
        name="Safe Tampering Evidence",
        description="The safe shows clear signs of being forced open with specialized tools",
        associated_item="Heavy Safe",
        item_location="Bank", 
        relevance_to_mystery="Indicates the robbery was planned and executed with professional tools"
    )
    
    # Create mystery objective
    mystery = MysteryObjective(
        name="Bank Robbery Investigation",
        description="Investigate the bank robbery and find the culprit",
        clues=[clue],
        mystery_solution="The safe was opened by a professional thief"
    )
    
    # Create world
    world = World(player)
    world.add_location(bank)
    world.add_item(safe)
    world.set_objective(player, mystery)
    
    print(f"📍 Player location: {world.player.location.name}")
    print(f"📦 Items in location: {[item.name for item in world.player.location.items]}")
    print(f"🔍 Safe gettable: {safe.gettable}")
    print(f"💡 Initial clues discovered: {len(mystery.get_discovered_clues())}/{len(mystery.clues)}")
    
    # Test 1: Try to simulate player interacting with the safe (but not taking it)
    print("\n" + "="*60)
    print("Test 1: Player examines the safe (interaction without taking)")
    print("="*60)
    
    # Create a world update that includes the safe in narration but doesn't move it
    world_update = WorldUpdate(
        moved_objects=[],  # No objects moved
        blocked_passages_available=[],
        location_changed=LocationChange(new_location=None),
        puzzles_solved=[],
        narration="You examine the Heavy Safe closely. The metal is dented and scarred, showing clear evidence of forced entry."
    )
    
    # Apply the update
    world.update_from_structured(world_update, language='en')
    
    # Check if clue was discovered
    discovered_clues = mystery.get_discovered_clues()
    print(f"✅ Clues discovered after interaction: {len(discovered_clues)}/{len(mystery.clues)}")
    
    if discovered_clues:
        for clue in discovered_clues:
            print(f"   • {clue.name}: {clue.description}")
        print("🎉 SUCCESS: Clue discovered by interacting with non-gettable item!")
    else:
        print("❌ FAILURE: No clue discovered")
    
    # Test 2: Verify that attempting to take the safe fails but still discovers clue
    print("\n" + "="*60)
    print("Test 2: Player tries to take the safe (should fail but discover clue)")
    print("="*60)
    
    # Reset clue discovery state for second test
    clue.discovered = False
    
    # Simulate trying to take the safe but failing (no object movement, but item mentioned)
    world_update2 = WorldUpdate(
        moved_objects=[],  # No movement because item is too heavy
        blocked_passages_available=[],
        location_changed=LocationChange(new_location=None),
        puzzles_solved=[],
        narration="You attempt to lift the Heavy Safe, but it's far too heavy to move. As you struggle with it, you notice detailed scratch marks around the lock mechanism."
    )
    
    # Apply the update
    world.update_from_structured(world_update2, language='en')
    
    # Check if clue was discovered
    discovered_clues = mystery.get_discovered_clues()
    print(f"✅ Clues discovered after failed taking attempt: {len(discovered_clues)}/{len(mystery.clues)}")
    
    if discovered_clues:
        for clue in discovered_clues:
            print(f"   • {clue.name}: {clue.description}")
        print("🎉 SUCCESS: Clue discovered even when item can't be taken!")
    else:
        print("❌ FAILURE: No clue discovered")
    
    # Test 3: Test with Spanish language
    print("\n" + "="*60)
    print("Test 3: Test Spanish language support")
    print("="*60)
    
    # Reset clue discovery state for third test
    clue.discovered = False
    
    world_update3 = WorldUpdate(
        moved_objects=[],
        blocked_passages_available=[],
        location_changed=LocationChange(new_location=None),
        puzzles_solved=[],
        narration="Examinas la Heavy Safe detalladamente. El metal muestra signos claros de haber sido forzada."
    )
    
    # Apply the update with Spanish language
    world.update_from_structured(world_update3, language='es')
    
    # Check if clue was discovered
    discovered_clues = mystery.get_discovered_clues()
    print(f"✅ Pistas descubiertas con idioma español: {len(discovered_clues)}/{len(mystery.clues)}")
    
    if discovered_clues:
        print("🎉 SUCCESS: Spanish language support working!")
    else:
        print("❌ FAILURE: Spanish language test failed")
    
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    
    final_progress = mystery.get_completion_progress()
    print(f"📊 Final mystery progress: {final_progress[0]}/{final_progress[1]} clues discovered")
    print(f"🎯 Mystery completed: {mystery.is_completed()}")
    
    if final_progress[0] > 0:
        print("✅ SUCCESS: Non-gettable item clue discovery is working!")
        return True
    else:
        print("❌ FAILURE: Non-gettable item clue discovery is not working")
        return False

if __name__ == "__main__":
    success = test_non_gettable_clue_discovery()
    if success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)

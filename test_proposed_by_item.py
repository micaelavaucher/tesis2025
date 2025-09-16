#!/usr/bin/env python3
"""
Test script to verify the proposed_by_item functionality works correctly.
"""

import sys
import os
sys.path.append('src')

from payador.core.world import World, Item, Puzzle, Location, Character
from payador.llm.structured_data_models import WorldUpdate, LocationChange, MovedObject, PuzzleSolved

def create_test_world_with_proposed_by_item():
    """Create a test world with an item that should propose a puzzle when investigated."""
    
    # Create a test world
    world = World()
    
    # Create a location
    test_location = Location(
        name="Test Library",
        descriptions=["A small library with ancient books and mysterious artifacts"]
    )
    world.add_location(test_location)
    
    # Create a mysterious item
    mysterious_book = Item(
        name="Mysterious Ancient Book",
        descriptions=["A leather-bound tome with strange symbols on its cover", 
                     "The book feels warm to the touch and seems to pulse with energy"]
    )
    test_location.add_item(mysterious_book)
    world.add_item(mysterious_book)
    
    # Create a puzzle that should be proposed by the book
    book_puzzle = Puzzle(
        name="Ancient Riddle of the Book",
        descriptions=["An ancient riddle appears when you investigate the mysterious book"],
        problem="I speak without voice, I hear without ears. I have no body, but come alive with the wind. What am I?",
        answer="echo",
        puzzle_type="riddle",
        proposed_by_item="Mysterious Ancient Book"  # This is the key!
    )
    world.add_puzzle(book_puzzle)
    
    # Create a player character
    player = Character(
        name="Test Player",
        descriptions=["The player character"],
        location=test_location
    )
    world.set_player(player)
    
    return world

def test_item_investigation_triggers_puzzle():
    """Test that investigating an item triggers the associated puzzle."""
    print("🧪 Testing item investigation triggering puzzle...")
    
    world = create_test_world_with_proposed_by_item()
    
    # First, verify the puzzle is properly set up
    puzzle = world.find_puzzle_proposed_by_item("Mysterious Ancient Book")
    assert puzzle is not None, "Puzzle should be found by item name"
    assert puzzle.name == "Ancient Riddle of the Book", "Puzzle name should match"
    assert puzzle.proposed_by_item == "Mysterious Ancient Book", "Puzzle should be proposed by the book"
    
    print(f"✅ Puzzle setup verified: {puzzle.name} proposed by {puzzle.proposed_by_item}")
    
    # Create a world update simulating item investigation
    investigation_update = WorldUpdate(
        moved_objects=[],
        blocked_passages_available=[],
        location_changed=LocationChange(new_location=None),
        puzzles_solved=[],
        narration="You examine the Mysterious Ancient Book closely. The symbols on its cover seem to shift and change as you look at them. The book feels surprisingly warm to the touch."
    )
    
    # Apply the update
    world.update_from_structured(investigation_update)
    
    # Check if the puzzle proposition was added to the narration
    updated_narration = investigation_update.narration
    print(f"\n📖 Updated narration:\n{updated_narration}")
    
    # Verify the puzzle was triggered
    assert puzzle.name.lower() in updated_narration.lower() or puzzle.problem.lower() in updated_narration.lower(), \
        "Puzzle should be mentioned in the updated narration"
    
    print("✅ Item investigation successfully triggered puzzle!")
    
    return True

def test_case_insensitive_matching():
    """Test that item name matching is case insensitive."""
    print("\n🧪 Testing case insensitive item matching...")
    
    world = create_test_world_with_proposed_by_item()
    
    # Test with different case variations
    test_names = [
        "mysterious ancient book",
        "MYSTERIOUS ANCIENT BOOK", 
        "Mysterious Ancient Book",
        "mYsTeRiOuS aNcIeNt BoOk"
    ]
    
    for name in test_names:
        puzzle = world.find_puzzle_proposed_by_item(name)
        assert puzzle is not None, f"Should find puzzle with case variation: {name}"
        print(f"✅ Found puzzle with case variation: {name}")
    
    print("✅ Case insensitive matching works correctly!")
    
    return True

def test_no_puzzle_when_item_moved():
    """Test that puzzles are not triggered when items are moved (taken), only when investigated."""
    print("\n🧪 Testing that moved items don't trigger puzzles...")
    
    world = create_test_world_with_proposed_by_item()
    
    # Create a world update where the item is moved (taken)
    taking_update = WorldUpdate(
        moved_objects=[MovedObject(object_name="Mysterious Ancient Book", new_location="Player")],
        blocked_passages_available=[],
        location_changed=LocationChange(new_location=None),
        puzzles_solved=[],
        narration="You pick up the Mysterious Ancient Book and add it to your inventory."
    )
    
    original_narration = taking_update.narration
    
    # Apply the update
    world.update_from_structured(taking_update)
    
    # The narration should NOT be modified when taking an item
    assert taking_update.narration == original_narration, \
        "Narration should not be modified when item is moved/taken"
    
    print("✅ Moving items doesn't incorrectly trigger puzzles!")
    
    return True

def test_multiple_investigation_keywords():
    """Test that various investigation keywords trigger the puzzle."""
    print("\n🧪 Testing multiple investigation keywords...")
    
    world = create_test_world_with_proposed_by_item()
    
    keywords = ['investigate', 'examine', 'look at', 'inspect', 'observe', 'check', 'study']
    
    for keyword in keywords:
        # Create a fresh update for each keyword
        test_update = WorldUpdate(
            moved_objects=[],
            blocked_passages_available=[],
            location_changed=LocationChange(new_location=None),
            puzzles_solved=[],
            narration=f"You {keyword} the Mysterious Ancient Book carefully."
        )
        
        world.update_from_structured(test_update)
        
        # Check if puzzle was triggered
        puzzle_triggered = any(word in test_update.narration.lower() 
                             for word in ['riddle', 'puzzle', 'echo', 'voice', 'wind'])
        
        assert puzzle_triggered, f"Keyword '{keyword}' should trigger puzzle"
        print(f"✅ Keyword '{keyword}' successfully triggered puzzle")
    
    print("✅ All investigation keywords work correctly!")
    
    return True

if __name__ == "__main__":
    print("🚀 Starting proposed_by_item functionality tests...\n")
    
    try:
        test_item_investigation_triggers_puzzle()
        test_case_insensitive_matching()
        test_no_puzzle_when_item_moved()
        test_multiple_investigation_keywords()
        
        print("\n🎉 All tests passed! The proposed_by_item functionality is working correctly!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

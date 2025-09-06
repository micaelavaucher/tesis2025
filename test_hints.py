#!/usr/bin/env python3
"""Test script for the puzzle hint system."""

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.payador.core.world import Character, Item, Location, Puzzle, World
from src.payador.core.game_logic import get_hint_puzzle_info, handle_debug_command

def create_test_world_with_hints():
    """Create a simple test world with a puzzle that has hints."""
    
    # Create items
    item_safe = Item("Safe", ["A locked metal safe", "There's a 4-digit combination lock"], gettable=False)
    item_photo = Item("Family Photo", ["A photo showing a family", "Date written on back: 15/8/87"], gettable=True)
    item_diary = Item("Diary", ["An old diary", "Contains personal memories"], gettable=True)
    
    # Create puzzle with hints
    puzzle_safe = Puzzle(
        name="Safe Code",
        descriptions=["A combination lock puzzle", "Need a 4-digit code"],
        problem="What's the 4-digit code to open the safe?",
        answer="1587",
        puzzle_type="code",
        hints=[
            "Look for important dates in personal belongings around the room",
            "The family photo might contain significant information",  
            "Check the back of the photo for any written dates",
            "Use the date format DD/MM/YY as the code: 15/8/87 becomes 1587"
        ]
    )
    
    # Create locations
    study = Location(
        name="Study Room",
        descriptions=["A cozy study with a desk and bookshelf", "There's a safe in the corner"],
        items=[item_safe, item_photo, item_diary]
    )
    
    hallway = Location(
        name="Hallway", 
        descriptions=["A long hallway with doors on both sides"],
        items=[]
    )
    
    # Connect locations
    study.connecting_locations = [hallway]
    hallway.connecting_locations = [study]
    
    # Create player
    player = Character(
        name="Detective",
        descriptions=["A curious detective", "Looking for clues"],
        inventory=[],
        location=study
    )
    
    # Create world
    world = World(player)
    world.add_locations([study, hallway])
    world.add_items([item_safe, item_photo, item_diary])
    world.add_puzzle(puzzle_safe)
    world.set_objective(item_photo, hallway)  # Simple objective for testing
    
    return world

def test_hint_system():
    """Test the hint system functionality."""
    print("🧪 Testing PAYADOR Puzzle Hint System\n")
    
    # Create test world
    world = create_test_world_with_hints()
    language = 'en'
    
    print("✅ Created test world with puzzle that has hints")
    print(f"📍 Player location: {world.player.location.name}")
    print(f"🧩 Available puzzles: {list(world.puzzles.keys())}")
    
    puzzle = world.puzzles["Safe Code"]
    print(f"💡 Puzzle has {len(puzzle.hints)} hints available")
    print(f"🎯 Given hints so far: {len(puzzle.given_hints)}")
    
    print("\n" + "="*50)
    print("Testing hint requests:")
    print("="*50)
    
    # Test hint requests
    hint_commands = ["hint", "pista", "give me a hint", "help"]
    
    for i, command in enumerate(hint_commands, 1):
        print(f"\n🔍 Test {i}: '{command}'")
        result = handle_debug_command(command, world, language)
        if result:
            print(result)
        else:
            print("❌ Command not recognized")
        
        print(f"📊 Hints given so far: {len(puzzle.given_hints)}/{len(puzzle.hints)}")
    
    print("\n" + "="*50)
    print("Testing exhausted hints:")
    print("="*50)
    
    # Test when all hints are exhausted
    print(f"\n🔍 Test: Requesting hint when all are used")
    result = handle_debug_command("hint", world, language)
    if result:
        print(result)
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    test_hint_system()

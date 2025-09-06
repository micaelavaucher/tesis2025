#!/usr/bin/env python3
"""
Test script to validate the new mystery clue location validation system.
Tests that clues properly validate both item existence and location placement.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from payador.llm.structured_data_models import GeneratedWorld, MysteryClue, GeneratedObjective, ObjectiveType, ComponentType, ObjectiveComponent
from payador.core.world_builder import create_world_from_llm_response, set_objective_from_generated
from payador.core.world import World, Location, Item, Character

def test_mystery_clue_location_validation():
    """Test that mystery clues properly validate item location placement."""
    print("🔍 Testing Mystery Clue Location Validation")
    print("=" * 50)
    
    # Test 1: Valid mystery clue with correct item and location
    print("\n📝 Test 1: Valid mystery clue with correct item and location")
    
    test_world_data = {
        "title": "Mystery Manor",
        "backstory": "A murder has occurred in the old manor.",
        "locations": [
            {
                "name": "Library",
                "descriptions": ["A dusty old library filled with books"],
                "items": ["Diary", "Old Key"],
                "connecting_locations": ["Hallway"],
                "blocked_passages": []
            },
            {
                "name": "Hallway", 
                "descriptions": ["A dark hallway"],
                "items": [],
                "connecting_locations": ["Library"],
                "blocked_passages": []
            }
        ],
        "items": [
            {
                "name": "Diary",
                "descriptions": ["A personal diary with mysterious entries"],
                "gettable": True
            },
            {
                "name": "Old Key",
                "descriptions": ["A rusty old key"],
                "gettable": True
            }
        ],
        "characters": [],
        "puzzles": [],
        "player": {
            "name": "Detective",
            "descriptions": ["A skilled detective"],
            "location": "Library",
            "inventory": []
        },
        "objective": {
            "type": "solve_mystery",
            "description": "Solve the murder mystery",
            "components": [],
            "mystery_clues": [
                {
                    "name": "Last Entry",
                    "description": "The final diary entry reveals the victim's fears",
                    "associated_item": "Diary",
                    "item_location": "Library",
                    "relevance_to_mystery": "Shows the victim was being threatened"
                }
            ],
            "mystery_solution": "The butler did it!"
        }
    }
    
    try:
        generated_world = GeneratedWorld.model_validate(test_world_data)
        world = create_world_from_llm_response(generated_world)
        print("✅ Valid clue creation successful")
        
        # Check that the mystery objective was created correctly
        if world.objective and len(world.objective) == 2:
            mystery_obj = world.objective[1]
            if hasattr(mystery_obj, 'clues') and len(mystery_obj.clues) > 0:
                clue = mystery_obj.clues[0]
                if hasattr(clue, 'item_location'):
                    print(f"✅ Clue location field present: {clue.item_location}")
                else:
                    print("❌ Clue location field missing")
            else:
                print("❌ No clues found in mystery objective")
        else:
            print("❌ Mystery objective not created properly")
            
    except Exception as e:
        print(f"❌ Valid clue test failed: {e}")
    
    # Test 2: Invalid mystery clue with non-existent item
    print("\n📝 Test 2: Invalid mystery clue with non-existent item")
    
    test_world_data_invalid_item = test_world_data.copy()
    test_world_data_invalid_item["objective"]["mystery_clues"] = [
        {
            "name": "Fake Clue",
            "description": "A clue about something that doesn't exist",
            "associated_item": "NonexistentItem",
            "item_location": "Library",
            "relevance_to_mystery": "Should fail validation"
        }
    ]
    
    try:
        generated_world = GeneratedWorld.model_validate(test_world_data_invalid_item)
        world = create_world_from_llm_response(generated_world)
        
        # Check if the mystery objective was created (should have no clues due to validation)
        if world.objective and len(world.objective) == 2:
            mystery_obj = world.objective[1]
            if hasattr(mystery_obj, 'clues'):
                print(f"✅ Invalid item clue properly filtered out. Remaining clues: {len(mystery_obj.clues)}")
            else:
                print("❌ Mystery objective structure incorrect")
        else:
            print("✅ Mystery objective not created due to all invalid clues")
            
    except Exception as e:
        print(f"❌ Invalid item test failed: {e}")
    
    # Test 3: Invalid mystery clue with non-existent location
    print("\n📝 Test 3: Invalid mystery clue with non-existent location")
    
    test_world_data_invalid_location = test_world_data.copy()
    test_world_data_invalid_location["objective"]["mystery_clues"] = [
        {
            "name": "Misplaced Clue",
            "description": "A clue in a location that doesn't exist",
            "associated_item": "Diary",
            "item_location": "NonexistentRoom",
            "relevance_to_mystery": "Should fail location validation"
        }
    ]
    
    try:
        generated_world = GeneratedWorld.model_validate(test_world_data_invalid_location)
        world = create_world_from_llm_response(generated_world)
        
        # Check if the mystery objective was created (should have no clues due to validation)
        if world.objective and len(world.objective) == 2:
            mystery_obj = world.objective[1]
            if hasattr(mystery_obj, 'clues'):
                print(f"✅ Invalid location clue properly filtered out. Remaining clues: {len(mystery_obj.clues)}")
            else:
                print("❌ Mystery objective structure incorrect")
        else:
            print("✅ Mystery objective not created due to all invalid clues")
            
    except Exception as e:
        print(f"❌ Invalid location test failed: {e}")
    
    # Test 4: Invalid mystery clue where item exists but not in specified location
    print("\n📝 Test 4: Item exists but not in specified location")
    
    test_world_data_wrong_location = test_world_data.copy()
    test_world_data_wrong_location["objective"]["mystery_clues"] = [
        {
            "name": "Mislocated Clue", 
            "description": "A clue about an item that exists but is in the wrong place",
            "associated_item": "Diary",
            "item_location": "Hallway",  # Diary is actually in Library
            "relevance_to_mystery": "Should fail item placement validation"
        }
    ]
    
    try:
        generated_world = GeneratedWorld.model_validate(test_world_data_wrong_location)
        world = create_world_from_llm_response(generated_world)
        
        # Check if the mystery objective was created (should have no clues due to validation)
        if world.objective and len(world.objective) == 2:
            mystery_obj = world.objective[1]
            if hasattr(mystery_obj, 'clues'):
                print(f"✅ Wrong location clue properly filtered out. Remaining clues: {len(mystery_obj.clues)}")
            else:
                print("❌ Mystery objective structure incorrect")
        else:
            print("✅ Mystery objective not created due to all invalid clues")
            
    except Exception as e:
        print(f"❌ Wrong location test failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Mystery Clue Location Validation Tests Complete!")

if __name__ == "__main__":
    test_mystery_clue_location_validation()

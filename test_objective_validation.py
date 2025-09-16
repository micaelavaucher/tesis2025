#!/usr/bin/env python3
"""
Test script to verify the objective validation fix.
"""

import sys
import os
sys.path.append('src')

from payador.llm.structured_data_models import (
    GeneratedWorld, GeneratedLocation, GeneratedItem, GeneratedCharacter, 
    GeneratedObjective, ObjectiveComponent, ObjectiveType, ComponentType
)
from payador.llm.generation_pipeline import verify_objective_completability

def create_test_world_with_missing_fragments():
    """Create a test world similar to the one that failed validation."""
    
    # Create locations
    locations = [
        GeneratedLocation(
            name='Eldoria Village',
            descriptions=['The heart of Eldoria'],
            items=[],
            connecting_locations=['Whispering Woods'],
            blocked_passages=[],
            relevance_to_objective='Starting location'
        ),
        GeneratedLocation(
            name='Whispering Woods',
            descriptions=['A corrupted forest'],
            items=['Corrupted Roots'],  # Only has corrupted roots, no amulet fragment
            connecting_locations=['Eldoria Village'],
            blocked_passages=[],
            relevance_to_objective='Should contain first fragment'
        )
    ]
    
    # Create items (missing the amulet fragments!)
    items = [
        GeneratedItem(
            name='Corrupted Roots',
            descriptions=['Twisted roots'],
            location='Whispering Woods',
            gettable=True,
            relevance_to_objective='Not relevant'
        ),
        GeneratedItem(
            name='Eldoria Amulet',
            descriptions=['The assembled amulet'],
            location=None,  # Not placed anywhere yet
            gettable=True,
            relevance_to_objective='Final goal'
        )
        # Missing: Amulet Fragment (Woods), Amulet Fragment (Springs), Amulet Fragment (Shrine)
    ]
    
    # Create characters
    characters = [
        GeneratedCharacter(
            name='Elder Rowan',
            descriptions=['A wise elder'],
            location='Eldoria Village',
            inventory=[],
            relevance_to_objective='Provides guidance'
        )
    ]
    
    # Create objective that requires the missing fragments
    objective = GeneratedObjective(
        type=ObjectiveType.GET_ITEM,
        components=[
            ObjectiveComponent(
                name='Eldoria Amulet',
                component_type=ComponentType.ITEM,
                role_in_objective='Final assembled amulet'
            ),
            ObjectiveComponent(
                name='Amulet Fragment (Woods)',
                component_type=ComponentType.ITEM,
                role_in_objective='First fragment'
            ),
            ObjectiveComponent(
                name='Amulet Fragment (Springs)',
                component_type=ComponentType.ITEM,
                role_in_objective='Second fragment'
            ),
            ObjectiveComponent(
                name='Amulet Fragment (Shrine)',
                component_type=ComponentType.ITEM,
                role_in_objective='Third fragment'
            )
        ],
        description='Collect all amulet fragments',
        success_conditions=['Have all fragments']
    )
    
    # Create world
    world = GeneratedWorld(
        locations=locations,
        items=items,
        characters=characters,
        puzzles=[],
        player=GeneratedCharacter(
            name='Player',
            descriptions=['The player character'],
            location='Eldoria Village',
            inventory=[],
            relevance_to_objective='Main character'
        ),
        objective=objective
    )
    
    return world

def test_validation():
    """Test the objective validation with missing fragments."""
    print("🧪 Testing objective validation with missing amulet fragments...")
    
    world = create_test_world_with_missing_fragments()
    
    print(f"\n📊 World Summary:")
    print(f"  Locations: {[loc.name for loc in world.locations]}")
    print(f"  Items: {[item.name for item in world.items]}")
    print(f"  Objective items needed: {[comp.name for comp in world.objective.components if comp.component_type == ComponentType.ITEM]}")
    
    result = verify_objective_completability(world)
    
    print(f"\n🔍 Validation result: {'✅ PASSED' if result else '❌ FAILED'}")
    
    if not result:
        print("✅ Good! The validation correctly detected missing fragments.")
    else:
        print("❌ Error! The validation incorrectly passed despite missing fragments.")
    
    return result

if __name__ == "__main__":
    test_validation()

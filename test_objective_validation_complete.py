#!/usr/bin/env python3
"""
Test script to verify the objective validation works with complete items.
"""

import sys
import os
sys.path.append('src')

from payador.llm.structured_data_models import (
    GeneratedWorld, GeneratedLocation, GeneratedItem, GeneratedCharacter, 
    GeneratedObjective, ObjectiveComponent, ObjectiveType, ComponentType
)
from payador.llm.generation_pipeline import verify_objective_completability

def create_test_world_with_all_fragments():
    """Create a test world with all required amulet fragments present."""
    
    # Create locations
    locations = [
        GeneratedLocation(
            name='Eldoria Village',
            descriptions=['The heart of Eldoria'],
            items=[],
            connecting_locations=['Whispering Woods', 'Silent Springs'],
            blocked_passages=[],
            relevance_to_objective='Starting location'
        ),
        GeneratedLocation(
            name='Whispering Woods',
            descriptions=['A corrupted forest'],
            items=['Amulet Fragment (Woods)', 'Corrupted Roots'],
            connecting_locations=['Eldoria Village'],
            blocked_passages=[],
            relevance_to_objective='Contains first fragment'
        ),
        GeneratedLocation(
            name='Silent Springs',
            descriptions=['Silent springs'],
            items=['Amulet Fragment (Springs)'],
            connecting_locations=['Eldoria Village', 'Shadowed Shrine'],
            blocked_passages=[],
            relevance_to_objective='Contains second fragment'
        ),
        GeneratedLocation(
            name='Shadowed Shrine',
            descriptions=['An abandoned temple'],
            items=['Amulet Fragment (Shrine)'],
            connecting_locations=['Silent Springs'],
            blocked_passages=[],
            relevance_to_objective='Contains third fragment'
        )
    ]
    
    # Create items (all fragments present!)
    items = [
        GeneratedItem(
            name='Corrupted Roots',
            descriptions=['Twisted roots'],
            location='Whispering Woods',
            gettable=True,
            relevance_to_objective='Not relevant'
        ),
        GeneratedItem(
            name='Amulet Fragment (Woods)',
            descriptions=['First amulet fragment'],
            location='Whispering Woods',
            gettable=True,
            relevance_to_objective='First fragment to collect'
        ),
        GeneratedItem(
            name='Amulet Fragment (Springs)',
            descriptions=['Second amulet fragment'],
            location='Silent Springs',
            gettable=True,
            relevance_to_objective='Second fragment to collect'
        ),
        GeneratedItem(
            name='Amulet Fragment (Shrine)',
            descriptions=['Third amulet fragment'],
            location='Shadowed Shrine',
            gettable=True,
            relevance_to_objective='Third fragment to collect'
        ),
        GeneratedItem(
            name='Eldoria Amulet',
            descriptions=['The assembled amulet'],
            location=None,  # Will be assembled by player
            gettable=True,
            relevance_to_objective='Final goal'
        )
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
    
    # Create objective that requires all fragments
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

def test_validation_with_complete_world():
    """Test the objective validation with all fragments present."""
    print("🧪 Testing objective validation with ALL amulet fragments present...")
    
    world = create_test_world_with_all_fragments()
    
    print(f"\n📊 World Summary:")
    print(f"  Locations: {[loc.name for loc in world.locations]}")
    print(f"  Items: {[item.name for item in world.items]}")
    print(f"  Objective items needed: {[comp.name for comp in world.objective.components if comp.component_type == ComponentType.ITEM]}")
    
    result = verify_objective_completability(world)
    
    print(f"\n🔍 Validation result: {'✅ PASSED' if result else '❌ FAILED'}")
    
    if result:
        print("✅ Good! The validation correctly passed with all fragments present.")
    else:
        print("❌ Error! The validation incorrectly failed despite having all fragments.")
    
    return result

if __name__ == "__main__":
    test_validation_with_complete_world()

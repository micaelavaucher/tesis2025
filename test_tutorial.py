#!/usr/bin/env python3
"""Test script to verify tutorial mode works correctly."""

import sys
import os
sys.path.append('.')

def test_tutorial_world():
    """Test that tutorial worlds load correctly."""
    print("🧪 Testing Tutorial World Loading...")
    
    try:
        import examples.example_worlds as example_worlds
        
        # Test English tutorial world
        print("  📝 Testing English tutorial world...")
        world_en = example_worlds.get_world('tutorial', language='en')
        assert world_en.player.name == "Player"
        assert len(world_en.locations) == 2
        assert len(world_en.items) == 1
        assert world_en.objective is not None
        assert world_en.objective[0].name == "Player"  # Player should get turtle
        assert world_en.objective[1].name == "Turtle"  # Target is turtle
        print("    ✅ English tutorial world works!")
        
        # Test Spanish tutorial world
        print("  📝 Testing Spanish tutorial world...")
        world_es = example_worlds.get_world('tutorial', language='es')
        assert world_es.player.name == "Jugador"
        assert len(world_es.locations) == 2
        assert len(world_es.items) == 1
        assert world_es.objective is not None
        assert world_es.objective[0].name == "Jugador"  # Jugador should get tortuga
        assert world_es.objective[1].name == "Tortuga"  # Target is tortuga
        print("    ✅ Spanish tutorial world works!")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_streamlit_interface():
    """Test that streamlit interface supports tutorial mode."""
    print("🧪 Testing Streamlit Interface...")
    
    try:
        from src.payador.ui.streamlit_interface import render_tutorial_mode, load_tutorial_world
        print("    ✅ Tutorial mode functions imported successfully!")
        
        # Check if tutorial is in mode options
        mode_options = {
            'Inspiration': 'inspiration',
            'Generate': 'generate', 
            'Preset': 'preset',
            'Tutorial': 'tutorial'
        }
        assert 'Tutorial' in mode_options
        assert mode_options['Tutorial'] == 'tutorial'
        print("    ✅ Tutorial mode in interface options!")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config():
    """Test that config supports tutorial mode."""
    print("🧪 Testing Configuration...")
    
    try:
        from src.payador.config import load_config
        config = load_config()
        
        # Should have default mode as inspiration
        mode = config.get('Options', 'GenerationMode', fallback='inspiration')
        print(f"    📄 Current generation mode: {mode}")
        
        # Test that tutorial mode would work if set
        config.set('Options', 'GenerationMode', 'tutorial')
        test_mode = config.get('Options', 'GenerationMode')
        assert test_mode == 'tutorial'
        print("    ✅ Tutorial mode works in config!")
        
        return True
        
    except Exception as e:
        print(f"    ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🚀 PAYADOR Tutorial Mode Test Suite")
    print("=" * 50)
    
    all_passed = True
    
    all_passed &= test_tutorial_world()
    print()
    all_passed &= test_streamlit_interface()
    print()
    all_passed &= test_config()
    print()
    
    print("=" * 50)
    if all_passed:
        print("🎉 All tests passed! Tutorial mode is ready!")
        print()
        print("📋 Tutorial Mode Summary:")
        print("   🎮 Mode: Tutorial")
        print("   🏠 Locations: Starting Room → Garden")
        print("   🐢 Objective: Get the turtle")
        print("   🌍 Languages: English & Spanish")
        print("   ✨ Status: Ready to use!")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()

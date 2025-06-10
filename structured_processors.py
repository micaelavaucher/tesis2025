"""Process structured data from language models for PAYADOR."""

#---- Imports -----------------------------------------------------------------
from structured_data_models import WorldUpdate

#---- Structured processors ---------------------------------------------------
def process_structured_world_update(world, update_data: dict) -> None:
    """Process a structured world update and apply changes to the world."""
    try:
        # Parse the update data
        update = WorldUpdate.model_validate(update_data)
        
        # Process moved objects
        for moved_object in update.moved_objects:
            try:
                # Find the item in the world
                item = world.items.get(moved_object.object_name)
                if not item:
                    continue
                    
                # Handle different target locations
                target = moved_object.new_location
                if target in ["Inventory", "Inventario", "Player", "Jugador", world.player.name]:
                    # Find where the item currently is
                    item_location = next((char for char in world.characters.values() 
                                        if item in char.inventory), None)
                    if not item_location:
                        item_location = next((loc for loc in world.locations.values() 
                                            if item in loc.items), None)
                    
                    if item_location:
                        world.player.save_item(item, item_location)
                        
                elif target in world.characters:
                    # Give item to character
                    world.player.give_item(world.characters[target], item)
                    
                else:
                    # Drop item in location
                    world.player.drop_item(item)
                    
            except Exception as e:
                print(f"Error processing moved object {moved_object.object_name}: {e}")
        
        # Process blocked passages
        for passage in update.blocked_passages_available:
            try:
                if passage.is_available:
                    location = world.locations.get(world.player.location.name)
                    target_location = world.locations.get(passage.location_name)
                    if location and target_location:
                        location.unblock_passage(target_location)
            except Exception as e:
                print(f"Error processing blocked passage {passage.location_name}: {e}")
        
        # Process location change
        if update.location_changed.new_location:
            try:
                new_location = world.locations.get(update.location_changed.new_location)
                if new_location:
                    world.player.move(new_location)
            except Exception as e:
                print(f"Error changing location to {update.location_changed.new_location}: {e}")
                
    except Exception as e:
        print(f"Error processing structured world update: {e}")
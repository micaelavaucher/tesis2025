---
applyTo: '**'
---
General Concept of the Project

This project, called **PAYADOR**, is a system to dynamically generate text adventure worlds (interactive fiction) using Large Language Models (LLMs) such as Gemini or Llama 3.

The main goal is not only to use the LLM to narrate a story, but to create the entire structure of the game world from scratch: the locations, the objects, the characters, the puzzles, and the player’s final objective. In addition, the system is capable of expanding the world during gameplay, adding new content dynamically.

---

How Does It Work? (Workflow)

The process is based on an **incremental generation pipeline** divided into 5 key stages:

## **1. Incremental Generation Pipeline (generation_pipeline.py)**

Instead of generating the whole world in a single pass, the system uses an incremental 5-step approach orchestrated by `create_world_incrementally()`:

**STEP 1 - World Concept:**
- Function: `run_step_1_concept()`
- Prompt: `PROMPT_STEP_1_CONCEPT`
- Generates: Title, backstory, player concept, main objective
- Output: `WorldConcept` (title, backstory, player_concept, main_objective)

**STEP 2 - Entity Skeleton:**
- Function: `run_step_2_skeleton()`
- Prompt: `PROMPT_STEP_2_SKELETON`
- Generates: Key entities (3-4 locations, 4-6 items, 2-3 characters)
- Output: `WorldSkeleton` (key_locations, key_items, key_characters)

**STEP 3 - Detailed Development:**
- Function: `run_step_3_details()`
- Prompt: `PROMPT_STEP_3_DETAILS`
- Generates: Playable world with main path toward the objective
- Output: Complete but simple `GeneratedWorld`

**STEP 4 - Complex Dependency Chains:**
- Function: `run_step_4_puzzles()`
- Prompt: `PROMPT_STEP_4_PUZZLES`
- Adds: Interconnected dependency chains, integrated puzzles, complex progression toward the objective
- Output: `GeneratedWorld` with multiple interdependent steps making the adventure more challenging

## **2. Incremental Data Structures (structured_data_models.py)**

The system uses specialized Pydantic models for each stage:

- `WorldConcept`: Initial world concept  
- `KeyEntity`: Key entity in the skeleton  
- `WorldSkeleton`: Structure of main entities  
- `ObjectiveComponent`: Objective component  
- `GeneratedObjective`: Complete objective with components and description  
- `GeneratedWorld`: Final complete world  

## **3. Built-in Quality Rules (prompts.py)**

All pipeline prompts include strict rules derived from successful legacy prompts:

**Connectivity Rules:**
- Mandatory bidirectional connections  
- Global connectivity (all locations accessible)  
- No isolated groups of locations  

**Puzzle Rules:**
- Solutions discoverable through exploration  
- Physical clues in the environment  
- Arbitrary codes prohibited  
- Completion validated  

**Coherence Rules:**
- Valid cross-references  
- Valid character inventories  
- Achievable objectives  
- Logical dependency chains  

## **4. World Building (world_builder.py)**

- `create_world_from_llm_response()` converts `GeneratedWorld` into Python objects  
- Handles both `GeneratedWorld` objects and legacy JSON/dictionaries  
- Validates structure and creates: Location, Item, Character, Puzzle  
- Establishes bidirectional connections and checks consistency  

## **5. Gameplay and Narration (app.py)**

- Integrates the incremental pipeline with `create_world_incrementally()`  
- Handles multiple modes: 'inspiration', 'generate', 'preset'  
- Includes retry system for valid objectives  
- Generates initial narrative and objective description  

## **6. RAG System (Retrieval-Augmented Generation) (memory_system.py)**

The system includes intelligent episodic memory that transforms PAYADOR from a world generator into a storyteller with persistent memory:

**Main Components:**
- `AtomicMemory`: Basic memory unit per game turn  
  - Stores: turn number, player action, narrative result, world context, timestamp  
  - Methods: `to_text()`, `to_dict()`, `from_dict()` for serialization  
- `EmbeddingService`: Generates vector embeddings using Gemini API  
  - Model: `gemini-embedding-001` with 768 dimensions  
  - Config: `task_type="RETRIEVAL_DOCUMENT"` with normalization  
- `MemoryStore`: Vector database with persistent ChromaDB  
  - Storage: embeddings, text documents, structured metadata  
  - Search: cosine similarity for contextual retrieval  
- `IntelligentMemorySystem`: Main RAG system coordinator  
  - Functions: automatic ingestion, intelligent retrieval, prompt formatting  

**Workflow:**
1. **Ingestion**: Each turn becomes an `AtomicMemory` with semantic embedding  
2. **Storage**: ChromaDB persists memories in collection by `world_id`  
3. **Retrieval**: Vector search finds memories relevant to the current action  
4. **Augmentation**: Memories formatted as context for LLM prompts  

**Integration with Game Loop:**
- `game_logic.py`: Automatic ingestion post-turn and retrieval pre-prompt  
- `prompts.py`: "Relevant Past Memories" section in `prompt_world_update_structured`  
- `app_interface.py`: API key passed from environment variables  

## **7. Dynamic Expansion**

- Legacy system preserved for in-game growth  
- `expand_world_from_llm_response()` in `world_builder.py`  
- Allows adding new content while maintaining coherence  

---

**Key Files:**
- `generation_pipeline.py`: Incremental pipeline orchestrator  
- `structured_data_models.py`: Pydantic models for each stage  
- `prompts.py`: Specialized prompts with quality rules  
- `world_builder.py`: Conversion to Python objects  
- `app.py`: Integration and generation modes  
- `memory_system.py`: RAG system with intelligent episodic memory  
- `game_logic.py`: Game loop integration with contextual memory  

**Extra:**
- DO NOT EXECUTE ANY CODE AUTOMATICALLY.  

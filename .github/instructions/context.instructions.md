---
applyTo: '**'
---
Concepto General del Proyecto

Este proyecto, que se llama **PAYADOR**, es un sistema para generar dinámicamente mundos de aventura de texto (ficción interactiva) utilizando Modelos de Lenguaje Grandes (LLMs) como Gemini o Llama 3.

El objetivo principal no es solo usar el LLM para narrar una historia, sino para crear toda la estructura del mundo del juego desde cero: las ubicaciones, los objetos, los personajes, los puzzles y el objetivo final del jugador. Además, el sistema es capaz de expandir el mundo durante el juego, añadiendo nuevo contenido de forma dinámica.

---

¿Cómo Funciona? (El Flujo de Trabajo)

El proceso se basa en un **pipeline de generación incremental** dividido en 5 etapas clave:

## **1. Pipeline de Generación Incremental (generation_pipeline.py)**

En lugar de generar todo el mundo en una sola pasada, el sistema utiliza un enfoque incremental de 5 pasos orquestado por `create_world_incrementally()`:

**PASO 1 - Concepto del Mundo:**
- Función: `run_step_1_concept()`
- Prompt: `PROMPT_STEP_1_CONCEPT`
- Genera: Título, historia de fondo, concepto del jugador, objetivo principal
- Salida: `WorldConcept` (título, backstory, player_concept, main_objective)

**PASO 2 - Esqueleto de Entidades:**
- Función: `run_step_2_skeleton()`
- Prompt: `PROMPT_STEP_2_SKELETON`
- Genera: Entidades clave (3-4 ubicaciones, 4-6 objetos, 2-3 personajes)
- Salida: `WorldSkeleton` (key_locations, key_items, key_characters)

**PASO 3 - Desarrollo Detallado:**
- Función: `run_step_3_details()`
- Prompt: `PROMPT_STEP_3_DETAILS`
- Genera: Mundo jugable con la ruta principal hacia el objetivo
- Salida: `GeneratedWorld` completo pero simple

**PASO 4 - Cadenas de Dependencias Complejas:**
- Función: `run_step_4_puzzles()`
- Prompt: `PROMPT_STEP_4_PUZZLES`
- Añade: Cadenas de dependencias interconectadas, puzzles integrados, progresión compleja hacia el objetivo
- Salida: `GeneratedWorld` con múltiples pasos interdependientes que hacen la aventura más desafiante

**PASO 5 - Expansión Opcional:**
- Función: `run_step_5_expansion()`
- Prompt: `PROMPT_STEP_5_EXPANSION`
- Añade: Contenido secundario, ubicaciones atmosféricas, objetos decorativos
- Salida: `GeneratedWorld` enriquecido

## **2. Estructuras de Datos Incrementales (structured_data_models.py)**

El sistema utiliza modelos Pydantic especializados para cada etapa:

- `WorldConcept`: Concepto inicial del mundo
- `KeyEntity`: Entidad clave en el esqueleto
- `WorldSkeleton`: Estructura de entidades principales
- `ObjectiveComponent`: Componente del objetivo
- `GeneratedObjective`: Objetivo completo con componentes y descripción
- `GeneratedWorld`: Mundo completo final

## **3. Reglas de Calidad Integradas (prompts.py)**

Todos los prompts del pipeline incluyen reglas estrictas derivadas de los prompts legacy exitosos:

**Reglas de Conectividad:**
- Conexiones bidireccionales obligatorias
- Conectividad global (todas las ubicaciones accesibles)
- No grupos aislados de ubicaciones

**Reglas de Puzzles:**
- Soluciones descubribles por exploración
- Pistas físicas en el entorno
- Prohibidos códigos arbitrarios
- Validación de completabilidad

**Reglas de Coherencia:**
- Referencias cruzadas válidas
- Inventarios de personajes válidos
- Objetivos alcanzables
- Cadenas de dependencias lógicas

## **4. Construcción del Mundo (world_builder.py)**

- `create_world_from_llm_response()` convierte `GeneratedWorld` a objetos Python
- Maneja tanto objetos `GeneratedWorld` como JSON/diccionarios legacy
- Valida la estructura y crea: Location, Item, Character, Puzzle
- Establece conexiones bidireccionales y verifica consistencia

## **5. Juego y Narración (app.py)**

- Integra el pipeline incremental con `create_world_incrementally()`
- Maneja múltiples modos: 'inspiration', 'generate', 'preset'
- Incluye sistema de reintentos para objetivos válidos
- Genera narrativa inicial y descripción del objetivo

## **6. Sistema RAG (Retrieval-Augmented Generation) (memory_system.py)**

El sistema incluye memoria episódica inteligente que transforma PAYADOR de un generador de mundos a un narrador con memoria persistente:

**Componentes Principales:**
- `AtomicMemory`: Unidad básica de memoria por turno de juego
  - Almacena: número de turno, acción del jugador, resultado narrativo, contexto del mundo, timestamp
  - Métodos: `to_text()`, `to_dict()`, `from_dict()` para serialización
- `EmbeddingService`: Genera embeddings vectoriales usando Gemini API
  - Modelo: `gemini-embedding-001` con dimensionalidad 768
  - Configuración: `task_type="RETRIEVAL_DOCUMENT"` con normalización
- `MemoryStore`: Base de datos vectorial con ChromaDB persistente
  - Almacenamiento: embeddings, documentos texto, metadatos estructurados
  - Búsqueda: similitud coseno para recuperación contextual
- `IntelligentMemorySystem`: Coordinador principal del sistema RAG
  - Funciones: ingestión automática, recuperación inteligente, formateo para prompts

**Flujo de Funcionamiento:**
1. **Ingestión**: Cada turno se convierte en `AtomicMemory` con embedding semántico
2. **Almacenamiento**: ChromaDB persiste memorias en colección por `world_id`
3. **Recuperación**: Búsqueda vectorial encuentra memorias relevantes a acción actual
4. **Augmentación**: Memorias se formatean como contexto para prompts del LLM

**Integración con Game Loop:**
- `game_logic.py`: Ingestión automática post-turno y recuperación pre-prompt
- `prompts.py`: Sección "Recuerdos Relevantes del Pasado" en `prompt_world_update_structured`
- `app_interface.py`: Paso de API key desde variables de entorno

## **7. Expansión Dinámica**

- Sistema heredado preservado para crecimiento durante el juego
- `expand_world_from_llm_response()` en `world_builder.py`
- Permite añadir contenido nuevo manteniendo coherencia

---

**Archivos Clave:**
- `generation_pipeline.py`: Orquestador del pipeline incremental
- `structured_data_models.py`: Modelos Pydantic para cada etapa
- `prompts.py`: Prompts especializados con reglas de calidad
- `world_builder.py`: Conversión a objetos Python
- `app.py`: Integración y modos de generación
- `memory_system.py`: Sistema RAG con memoria episódica inteligente
- `game_logic.py`: Integración del loop de juego con memoria contextual
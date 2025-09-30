"""Modern Streamlit interface for PAYADOR.

This module provides a beautiful and modern chat interface using Streamlit,
replacing the Gradio interface with enhanced UI and functionality.
"""

import streamlit as st
import os
import time
from ..config import load_config
from ..llm.models import get_llm
from ..core.game_logic import create_game_loop, generate_starting_narration
from ..llm.generation_pipeline import create_world_incrementally_generate
from ..core.world_builder import create_world_from_llm_response
from .ui_components import get_ui_texts, get_progress_messages
import examples.example_worlds as example_worlds

def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if 'language' not in st.session_state:
        st.session_state.language = 'en'  # Default to English
    
    if 'generation_mode' not in st.session_state:
        st.session_state.generation_mode = 'inspiration'  # Default to inspiration mode
    
    if 'debug_mode' not in st.session_state:
        st.session_state.debug_mode = False  # Default debug mode off
    
    if 'world' not in st.session_state:
        st.session_state.world = None
    
    if 'game_loop' not in st.session_state:
        st.session_state.game_loop = None
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'world_generated' not in st.session_state:
        st.session_state.world_generated = False
    
    if 'visited_locations' not in st.session_state:
        st.session_state.visited_locations = set()

def get_inspiration_suggestions(language: str) -> dict:
    """Get inspiration suggestions based on language."""
    if language == 'es':
        return {
            "🕵️ Detectives": "Una historia de misterio y crimen donde eres un detective resolviendo un caso complejo",
            "🌙 Crepúsculo, la Saga": "Un mundo de vampiros y licántropos lleno de romance sobrenatural y decisiones difíciles, basado en la saga de Crepúsculo",
            "🍄 Super Mario": "Una aventura colorida en el Reino Champiñón con plataformas, power-ups y rescates épicos"
        }
    else:
        return {
            "🕵️ Detectives": "A mystery and crime story where you are a detective solving a complex case",
            "🌙 Twilight Saga": "A world of vampires and werewolves full of supernatural romance and difficult choices, based on the Twilight saga", 
            "🍄 Super Mario": "A colorful adventure in the Mushroom Kingdom with platforms, power-ups and epic rescues"
        }

def render_sidebar():
    """Render the sidebar with configuration options."""
    with st.sidebar:
        st.markdown("## ⚙️ Configuration")
        
        # Check if game is active (world is loaded)
        game_active = st.session_state.world_generated and st.session_state.world is not None
        
        # Language selector
        language_options = {'English': 'en', 'Español': 'es'}
        current_lang = st.session_state.language
        selected_lang_name = next(k for k, v in language_options.items() if v == current_lang)
        
        new_lang = st.selectbox(
            "🌐 Language",
            options=list(language_options.keys()),
            index=list(language_options.keys()).index(selected_lang_name),
            disabled=game_active
        )
        
        if not game_active and language_options[new_lang] != st.session_state.language:
            st.session_state.language = language_options[new_lang]
            st.rerun()
        
        # Mode selector
        mode_options = {
            'Inspiration': 'inspiration',
            'Generate': 'generate', 
            'Preset': 'preset',
            'Tutorial': 'tutorial'
        }
        current_mode = st.session_state.generation_mode
        selected_mode_name = next(k for k, v in mode_options.items() if v == current_mode)
        
        new_mode = st.selectbox(
            "🎮 Generation Mode",
            options=list(mode_options.keys()),
            index=list(mode_options.keys()).index(selected_mode_name),
            disabled=game_active
        )
        
        if not game_active and mode_options[new_mode] != st.session_state.generation_mode:
            st.session_state.generation_mode = mode_options[new_mode]
            # Reset world state when mode changes
            st.session_state.world = None
            st.session_state.game_loop = None
            st.session_state.chat_history = []
            st.session_state.world_generated = False
            st.rerun()
        
        # Debug mode toggle
        new_debug = st.checkbox(
            "🛠️ Debug Mode",
            value=st.session_state.debug_mode,
            disabled=game_active,
            help="Enable debug quick actions for world inspection"
        )
        
        if not game_active and new_debug != st.session_state.debug_mode:
            st.session_state.debug_mode = new_debug
        
        if game_active:
            st.info("🔒 Settings locked during active game")
        
        st.markdown("---")
        
        # Reset button
        if st.button("🏠 Home", type="secondary"):
            st.session_state.world = None
            st.session_state.game_loop = None
            st.session_state.chat_history = []
            st.session_state.world_generated = False
            st.session_state.visited_locations = set()
            st.rerun()

def render_inspiration_mode():
    """Render the inspiration mode interface."""
    texts = get_ui_texts(st.session_state.language)
    
    st.markdown("# 🌱 PAYADOR")
    st.markdown("### Dynamic Text Adventure World Generator")
    
    if st.session_state.language == 'es':
        st.markdown("**Modo Inspiración:** Escribe una idea y genera un mundo único")
    else:
        st.markdown("**Inspiration Mode:** Write an idea and generate a unique world")
    
    # Inspiration suggestions
    suggestions = get_inspiration_suggestions(st.session_state.language)
    
    if st.session_state.language == 'es':
        st.markdown("**💡 Sugerencias populares:**")
    else:
        st.markdown("**💡 Popular suggestions:**")
    
    cols = st.columns(3)
    
    for i, (title, description) in enumerate(suggestions.items()):
        with cols[i]:
            if st.button(title, key=f"suggestion_{i}", help=description):
                st.session_state.inspiration_input = description
                st.rerun()
    
    # Text input for inspiration
    inspiration = st.text_area(
        texts['PROMPT_LABEL'],
        value=st.session_state.get('inspiration_input', ''),
        placeholder=texts['TEXTBOX_LABEL'],
        height=100
    )
    
    # Generate button
    if st.button(texts['GENERATE_WORLD'], type="primary", disabled=not inspiration.strip()):
        generate_world_from_inspiration(inspiration.strip())

def generate_world_from_inspiration(inspiration: str):
    """Generate world from inspiration with progress display."""
    progress_container = st.container()
    progress_messages = get_progress_messages(st.session_state.language)
    
    with progress_container:
        st.markdown("### 🔄 Generating World...")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            config = load_config()
            reasoning_model_name = config.get('Models', 'ReasoningModel', fallback='gpt-4o-mini')
            narrative_model_name = config.get('Models', 'NarrativeModel', fallback='gpt-4o-mini')
            log_filename = f"streamlit_session_{int(time.time())}.json"
            
            reasoning_model = get_llm(reasoning_model_name)
            narrative_model = get_llm(narrative_model_name)
            
            # Step-by-step generation with proper progress tracking
            from ..llm.generation_pipeline import run_step_1_concept, run_step_2_skeleton, run_step_3_details, run_step_4_puzzles, run_step_5_expansion
            
            # Step 1: Concept
            status_text.text(progress_messages['STEP_1'])
            progress_bar.progress(0.1)
            time.sleep(0.2)
            print(f"session_state: {st.session_state}")
            concept = run_step_1_concept(inspiration, st.session_state.language)
            status_text.text(progress_messages['STEP_1_COMPLETE'].format(title=concept.title))
            progress_bar.progress(0.2)
            time.sleep(0.3)
            
            # Step 2: Skeleton
            status_text.text(progress_messages['STEP_2'])
            progress_bar.progress(0.3)
            time.sleep(0.2)
            
            skeleton = run_step_2_skeleton(concept, st.session_state.language)
            status_text.text(progress_messages['STEP_2_COMPLETE'].format(
                locations=len(skeleton.key_locations),
                items=len(skeleton.key_items),
                characters=len(skeleton.key_characters)
            ))
            progress_bar.progress(0.5)
            time.sleep(0.3)
            
            # Step 3: Details
            status_text.text(progress_messages['STEP_3'])
            progress_bar.progress(0.6)
            time.sleep(0.2)
            
            world_basic = run_step_3_details(concept, skeleton, st.session_state.language)
            status_text.text(progress_messages['STEP_3_COMPLETE'].format(
                locations=len(world_basic.locations),
                items=len(world_basic.items)
            ))
            progress_bar.progress(0.7)
            time.sleep(0.3)
            
            # Step 4: Puzzles
            status_text.text(progress_messages['STEP_4'])
            progress_bar.progress(0.8)
            time.sleep(0.2)
            
            world_with_puzzles = run_step_4_puzzles(world_basic, st.session_state.language)
            status_text.text(progress_messages['STEP_4_COMPLETE'].format(
                puzzles=len(world_with_puzzles.puzzles)
            ))
            progress_bar.progress(0.9)
            time.sleep(0.3)
            
            # Step 5: Final expansion (optional, simplified)
            generated_world = world_with_puzzles  # Skip expansion for now to be faster
            
            status_text.text(progress_messages['PIPELINE_COMPLETE'])
            progress_bar.progress(0.95)
            time.sleep(0.2)
            
            # Build world objects
            status_text.text(progress_messages['BUILDING_WORLD'])
            world = create_world_from_llm_response(generated_world)
            
            if world is None:
                # Fallback to preset world
                status_text.text("🔄 Using fallback world...")
                world = example_worlds.get_world(2, language=st.session_state.language)
            
            st.session_state.world = world
            st.session_state.world_generated = True
            
            # Generate starting narration
            starting_narration = generate_starting_narration(
                st.session_state.world,
                st.session_state.language,
                narrative_model
            )
            
            # Initialize chat with starting narration
            st.session_state.chat_history = [
                {"role": "assistant", "content": starting_narration}
            ]
            
            progress_bar.progress(1.0)
            status_text.success("✅ World generated successfully!")
            time.sleep(1)
            st.rerun()
                
        except Exception as e:
            st.error(f"❌ Error generating world: {str(e)}")

def render_generate_mode():
    """Render the generate mode interface."""
    st.markdown("# 🌱 PAYADOR")
    st.markdown("### Dynamic Text Adventure World Generator")
    
    if st.session_state.language == 'es':
        st.markdown("**Modo Generar:** Genera un mundo completamente aleatorio")
    else:
        st.markdown("**Generate Mode:** Generate a completely random world")
    
    if not st.session_state.world_generated:
        if st.button("🎲 Generate Random World", type="primary"):
            generate_random_world()
    else:
        render_chat_interface()

def generate_random_world():
    """Generate a completely random world."""
    progress_container = st.container()
    
    with progress_container:
        st.markdown("### 🔄 Generating Random World...")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            config = load_config()
            reasoning_model_name = config.get('Models', 'ReasoningModel', fallback='gpt-4o-mini')
            narrative_model_name = config.get('Models', 'NarrativeModel', fallback='gpt-4o-mini')
            
            narrative_model = get_llm(narrative_model_name)
            
            # Step 1: Generate world
            status_text.text("🌍 Creating world concept...")
            progress_bar.progress(0.2)
            
            generated_world = create_world_incrementally_generate(st.session_state.language)
            
            # Step 2: Build world objects
            status_text.text("🏗️ Building world structure...")
            progress_bar.progress(0.6)
            
            world = create_world_from_llm_response(generated_world)
            
            if world is None:
                # Fallback to preset world
                status_text.text("🔄 Using fallback world...")
                progress_bar.progress(0.8)
                world = example_worlds.get_world(2, language=st.session_state.language)
            
            # Step 3: Initialize game
            status_text.text("🎮 Initializing game...")
            progress_bar.progress(0.9)
            
            st.session_state.world = world
            st.session_state.world_generated = True
            
            # Generate starting narration
            starting_narration = generate_starting_narration(
                world,
                st.session_state.language,
                narrative_model
            )
            
            # Initialize chat with starting narration
            st.session_state.chat_history = [
                {"role": "assistant", "content": starting_narration}
            ]
            
            progress_bar.progress(1.0)
            status_text.success("✅ Random world generated successfully!")
            time.sleep(1)
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error generating random world: {str(e)}")

def render_preset_mode():
    """Render the preset mode interface."""
    st.markdown("# 🌱 PAYADOR")
    st.markdown("### Dynamic Text Adventure World Generator")
    
    if st.session_state.language == 'es':
        st.markdown("**Modo Predefinido:** Usa un mundo preconstruido")
    else:
        st.markdown("**Preset Mode:** Use a pre-built world")
    
    if not st.session_state.world_generated:
        # World selector
        world_options = {
            "Mysterious Library": 1,
            "Desert Oasis": 2, 
            "Haunted Mansion": 3
        }
        
        selected_world = st.selectbox(
            "🏰 Select a world:",
            options=list(world_options.keys())
        )
        
        if st.button("🚀 Load World", type="primary"):
            load_preset_world(world_options[selected_world])
    else:
        render_chat_interface()

def load_preset_world(world_id: int):
    """Load a preset world."""
    try:
        world = example_worlds.get_world(world_id, language=st.session_state.language)
        st.session_state.world = world
        st.session_state.world_generated = True
        
        config = load_config()
        narrative_model_name = config.get('Models', 'NarrativeModel', fallback='gpt-4o-mini')
        narrative_model = get_llm(narrative_model_name)
        
        # Generate starting narration
        starting_narration = generate_starting_narration(
            world,
            st.session_state.language,
            narrative_model
        )
        
        # Initialize chat with starting narration
        st.session_state.chat_history = [
            {"role": "assistant", "content": starting_narration}
        ]
        
        st.success("✅ Preset world loaded successfully!")
        time.sleep(1)
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error loading preset world: {str(e)}")

def render_tutorial_mode():
    """Render the tutorial mode interface."""
    st.markdown("# 🌱 PAYADOR")
    st.markdown("### Dynamic Text Adventure World Generator")
    
    if st.session_state.language == 'es':
        st.markdown("**Modo Tutorial:** Aprende a jugar con un mundo simple")
        st.markdown("""
        **¡Bienvenido al Tutorial de PAYADOR!** 🎮
        
        Este es un mundo simple diseñado para enseñarte cómo jugar:
        
        🏠 **2 ubicaciones:** Habitación Inicial → Jardín  
        🐢 **1 objetivo:** Encuentra y toma la tortuga  
        🎯 **Meta:** Recoger la tortuga del jardín
        
        ### 🤖 Estilo de Juego Chatbot
        PAYADOR funciona como una conversación entre tú y un narrador IA. Cada mensaje que escribas representa **una acción en el juego**.
        
        **📝 Mecánicas por Turnos:**
        - Un mensaje = Un turno de juego
        - Escribe comandos en lenguaje natural o descripciones de acciones
        - El narrador responderá describiendo lo que sucede
        - El mundo reacciona a tus decisiones dinámicamente
        
        **Ejemplos de cosas que puedes intentar:**
        - `mirar alrededor` - observar tu entorno
        - `ir al jardín` - moverte a otra ubicación  
        - `tomar tortuga` - recoger objetos
        - `inventario` - ver qué llevas contigo
        - `objetivo` - recordar tu misión
        (¡También puedes probar con otras acciones!)
        
        **📊 Aviso de Investigación:** Tu gameplay puede ser registrado de forma anónima para investigación sobre generación de narrativas con IA.
        """)
    else:
        st.markdown("**Tutorial Mode:** Learn to play with a simple world")
        st.markdown("""
        **Welcome to the PAYADOR Tutorial!** 🎮
        
        This is a simple world designed to teach you how to play:
        
        🏠 **2 locations:** Starting Room → Garden  
        🐢 **1 objective:** Find and take the turtle  
        🎯 **Goal:** Collect the turtle from the garden
        
        ### 🤖 Chatbot-Style Gameplay
        PAYADOR works like a conversation between you and an AI narrator. Each message you write represents **one action in the game**.
        
        **📝 Turn-Based Mechanics:**
        - One message = One game turn
        - Write commands in natural language or action descriptions
        - The narrator will respond describing what happens
        - The world reacts to your decisions dynamically
        
        **Examples of things you can try:**
        - `look around` - observe your surroundings
        - `go to garden` - move to another location  
        - `take turtle` - pick up objects
        - `inventory` - see what you're carrying
        - `objective` - remember your mission
        (You can experiment with other actions too!)
        
        **📊 Research Notice:** Your gameplay may be recorded anonymously for research on AI narrative generation.
        """)
    
    if not st.session_state.world_generated:
        if st.button("🎓 Start Tutorial", type="primary"):
            load_tutorial_world()
    else:
        render_chat_interface()

def load_tutorial_world():
    """Load the tutorial world."""
    try:
        world = example_worlds.get_world('tutorial', language=st.session_state.language)
        st.session_state.world = world
        st.session_state.world_generated = True
        
        config = load_config()
        narrative_model_name = config.get('Models', 'NarrativeModel', fallback='gpt-4o-mini')
        narrative_model = get_llm(narrative_model_name)
        
        # Generate starting narration
        starting_narration = generate_starting_narration(
            world,
            st.session_state.language,
            narrative_model
        )
        
        # Initialize chat with starting narration
        st.session_state.chat_history = [
            {"role": "assistant", "content": starting_narration}
        ]
        
        st.success("✅ Tutorial world loaded successfully!")
        time.sleep(1)
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error loading tutorial world: {str(e)}")

def render_chat_interface():
    """Render the main chat interface."""
    st.markdown("### 💬 Adventure Chat")
    
    # Initialize game loop if not exists
    if st.session_state.game_loop is None and st.session_state.world:
        config = load_config()
        reasoning_model_name = config.get('Models', 'ReasoningModel', fallback='gpt-4o-mini')
        narrative_model_name = config.get('Models', 'NarrativeModel', fallback='gpt-4o-mini')
        enable_rag = config.getboolean('Options', 'EnableRAG', fallback=True)
        
        reasoning_model = get_llm(reasoning_model_name)
        narrative_model = get_llm(narrative_model_name)
        api_key = os.getenv("GEMINI_API_KEY")
        log_filename = f"streamlit_session_{int(time.time())}.json"
        
        st.session_state.game_loop = create_game_loop(
            st.session_state.world, 
            reasoning_model, 
            narrative_model,
            st.session_state.language, 
            log_filename, 
            st.session_state.visited_locations, 
            api_key, 
            enable_rag
        )
    
    # Handle pending command if exists (process before displaying anything)
    if hasattr(st.session_state, 'pending_command') and st.session_state.pending_command:
        prompt = st.session_state.pending_command
        st.session_state.pending_command = None  # Clear the pending command
        
        # Add user message to chat
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        # Generate response
        if st.session_state.game_loop:
            response = st.session_state.game_loop(prompt, st.session_state.chat_history)
            # Add assistant response to chat
            st.session_state.chat_history.append({"role": "assistant", "content": response})
        else:
            st.session_state.chat_history.append({"role": "assistant", "content": "Game loop not initialized. Please reload the world."})
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Define quick actions based on language and debug mode
    if st.session_state.debug_mode:
        # Debug mode: show all actions
        if st.session_state.language == 'es':
            quick_actions = [
                ("🎯 Objetivo", "objetivo"),
                ("💡 Ayuda", "ayuda"),
                ("📋 Inventario", "inventario"),
                ("🔍 Inspeccionar", "inspeccionar mundo"),
                ("🗺️ Resumen", "resumen mundo"),
                ("📍 Ubicación", "¿dónde estoy?")
            ]
        else:
            quick_actions = [
                ("🎯 Objective", "objective"),
                ("💡 Help", "help"),
                ("📋 Inventory", "inventory"),
                ("🔍 Inspect World", "inspect world"),
                ("🗺️ Overview", "world overview"),
                ("📍 Location", "where am I?")
            ]
    else:
        # Normal mode: only basic actions
        if st.session_state.language == 'es':
            quick_actions = [
                ("🎯 Objetivo", "objetivo"),
                ("💡 Ayuda", "ayuda")
            ]
        else:
            quick_actions = [
                ("🎯 Objective", "objective"),
                ("💡 Help", "help")
            ]
    
    # Quick action buttons - positioned right before chat input
    if st.session_state.debug_mode:
        st.markdown("<div style='text-align: left; margin-left: 4%; padding: 15px;'>🛠️ Debug Quick Actions:</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='text-align: left; margin-left: 4%; padding: 15px;'>🎯 Quick Actions:</div>", unsafe_allow_html=True)
    
    # Create buttons for quick actions with better spacing
    if st.session_state.debug_mode:
        # Debug mode: use 2 centered rows of 3 columns each with left margin
        # First row
        col_margin1, col1, col2, col3 = st.columns([0.20, 0.32, 0.32, 0.32])
        # Second row  
        col_margin2, col4, col5, col6 = st.columns([0.20, 0.32, 0.32, 0.32])
        
        cols = [col1, col2, col3, col4, col5, col6]
        
        for i, (button_text, command_text) in enumerate(quick_actions):
            with cols[i]:
                if st.button(button_text, key=f"quick_action_{i}", help=f"Send: {command_text}"):
                    # Simulate sending the command
                    st.session_state.pending_command = command_text
                    st.rerun()
    else:
        # Normal mode: center the 2 buttons with left margin
        col1, col2, col3 = st.columns([0.32, 0.32, 0.32])
        
        # Place buttons in the middle columns
        with col2:
            if st.button(quick_actions[0][0], key="quick_action_0", help=f"Send: {quick_actions[0][1]}"):
                st.session_state.pending_command = quick_actions[0][1]
                st.rerun()
        
        with col3:
            if st.button(quick_actions[1][0], key="quick_action_1", help=f"Send: {quick_actions[1][1]}"):
                st.session_state.pending_command = quick_actions[1][1]
                st.rerun()
    
    # Chat input
    if prompt := st.chat_input("What do you want to do?"):
        # Add user message to chat
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        # Generate response
        if st.session_state.game_loop:
            response = st.session_state.game_loop(prompt, st.session_state.chat_history)
            # Add assistant response to chat
            st.session_state.chat_history.append({"role": "assistant", "content": response})
        else:
            st.session_state.chat_history.append({"role": "assistant", "content": "Game loop not initialized. Please reload the world."})
        
        st.rerun()

def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="PAYADOR - Text Adventure Generator",
        page_icon="🌱",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better styling
    st.markdown("""
        <style>
        .main > div {
            padding-top: 2rem;
        }
        .stButton > button {
            width: 100%;
            margin-top: 1rem;
        }
        
        /* Quick action buttons styling */
        div[data-testid="column"] .stButton > button {
            font-size: 0.8rem;
            padding: 0.25rem 0.5rem;
            margin: 0.1rem;
            height: 2.5rem;
            width: 100%;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            min-width: 0;
        }
        
        /* Selectbox styling for light mode */
        .stSelectbox > div > div {
            background-color: #f0f2f6;
            color: #262730;
        }
        
        /* Selectbox styling for dark mode */
        [data-theme="dark"] .stSelectbox > div > div,
        .stApp[data-theme="dark"] .stSelectbox > div > div,
        [data-baseweb="select"] > div {
            background-color: #262730 !important;
            color: #fafafa !important;
            border: 1px solid #464646 !important;
        }
        
        /* Selectbox dropdown options for dark mode */
        [data-theme="dark"] .stSelectbox [role="listbox"],
        .stApp[data-theme="dark"] .stSelectbox [role="listbox"] {
            background-color: #262730 !important;
            color: #fafafa !important;
        }
        
        /* Selectbox dropdown option items for dark mode */
        [data-theme="dark"] .stSelectbox [role="option"],
        .stApp[data-theme="dark"] .stSelectbox [role="option"] {
            background-color: #262730 !important;
            color: #fafafa !important;
        }
        
        /* Selectbox dropdown option items hover for dark mode */
        [data-theme="dark"] .stSelectbox [role="option"]:hover,
        .stApp[data-theme="dark"] .stSelectbox [role="option"]:hover {
            background-color: #464646 !important;
            color: #fafafa !important;
        }
        
        /* Force text color for selectbox in dark mode */
        [data-theme="dark"] .stSelectbox div[data-baseweb="select"] > div,
        .stApp[data-theme="dark"] .stSelectbox div[data-baseweb="select"] > div {
            color: #fafafa !important;
        }
        
        /* Fix for the actual selected value display */
        [data-theme="dark"] .stSelectbox div[data-baseweb="select"] span,
        .stApp[data-theme="dark"] .stSelectbox div[data-baseweb="select"] span {
            color: #fafafa !important;
        }
        
        .chat-message {
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 0.5rem 0;
        }
        .user-message {
            background-color: #e3f2fd;
            margin-left: 2rem;
        }
        .assistant-message {
            background-color: #f5f5f5;
            margin-right: 2rem;
        }
        
        /* Chat message styling for dark mode */
        [data-theme="dark"] .user-message,
        .stApp[data-theme="dark"] .user-message {
            background-color: #1e3a8a;
            color: #fafafa;
        }
        [data-theme="dark"] .assistant-message,
        .stApp[data-theme="dark"] .assistant-message {
            background-color: #374151;
            color: #fafafa;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    initialize_session_state()
    
    # Render sidebar
    render_sidebar()
    
    # Main content area
    if st.session_state.generation_mode == 'inspiration':
        if not st.session_state.world_generated:
            render_inspiration_mode()
        else:
            render_chat_interface()
    elif st.session_state.generation_mode == 'generate':
        if not st.session_state.world_generated:
            render_generate_mode()
        else:
            render_chat_interface()
    elif st.session_state.generation_mode == 'preset':
        if not st.session_state.world_generated:
            render_preset_mode()
        else:
            render_chat_interface()
    elif st.session_state.generation_mode == 'tutorial':
        if not st.session_state.world_generated:
            render_tutorial_mode()
        else:
            render_chat_interface()
    elif st.session_state.generation_mode == 'tutorial':
        if not st.session_state.world_generated:
            render_tutorial_mode()
        else:
            render_chat_interface()

if __name__ == "__main__":
    main()

import streamlit as st
import sqlite3
import re
import os
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Initialize the LLm with Groq API key and model

llm = ChatGroq(
    groq_api_key=os.getenv("GROQ_API_KEY"),
    model="deepseek-r1-distill-llama-70b",
    temperature=0.7
    
)
# SQLite setup with context manager for better handling
def get_db_connection():
    conn = sqlite3.connect("language_mistakes.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS mistakes 
                      (id INTEGER PRIMARY KEY, user_input TEXT, mistake TEXT, correction TEXT, timestamp TEXT)''')
    conn.commit()
    return conn, cursor

# Scene options by proficiency level
def get_scene_options(level):
    scenes = {
        "beginner": [
            "You’re at a market buying fruit.",
            "You’re greeting a neighbor in your new town.",
            "You’re asking for directions to a park."
        ],
        "intermediate": [
            "You’re ordering a meal at a restaurant.",
            "You’re shopping for clothes in a store.",
            "You’re booking a hotel room over the phone."
        ],
        "advanced": [
            "You’re negotiating a business deal.",
            "You’re discussing a news article with a friend.",
            "You’re giving a presentation at work."
        ]
    }
    return scenes.get(level.lower(), scenes["beginner"])

# Correct user input and track mistakes
def correct_input(user_input, target_lang, native_lang, conn, cursor):
    prompt = PromptTemplate(
        input_variables=["input", "target", "native"],
        template="The user said: '{input}' in {target}. If there’s a mistake, correct it and explain in {native}. If correct, say 'Correct!'"
    )
    chain = LLMChain(llm=llm, prompt=prompt)
    response = chain.run(input=user_input, target=target_lang, native=native_lang)
    
    if "Correct!" not in response:
        # Robust parsing of response (assuming OpenAI returns something like "Mistake: ... Corrected to: ...")
        mistake = user_input
        correction = "Unknown"
        if "Corrected to:" in response:
            try:
                correction = response.split("Corrected to:")[1].split(".")[0].strip()
            except IndexError:
                correction = "Parsing error - check response format"
        cursor.execute("INSERT INTO mistakes (user_input, mistake, correction, timestamp) VALUES (?, ?, ?, ?)",
                       (user_input, mistake, correction, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
    return response

# Generate bot response in target language
def clean_response(response):
    """Removes any reasoning tags like <think>...</think> from the response."""
    return re.sub(r"<think>.*?</think>", "", response, flags=re.DOTALL).strip()

def generate_response(user_input, target_lang, scene):
    prompt = PromptTemplate(
        input_variables=["scene", "input", "target_lang"],
        template="Respond to '{input}' in {target_lang} based on this scene: {scene}"
    )
    chain = LLMChain(llm=llm, prompt=prompt)
    raw_response = chain.run(scene=scene, input=user_input, target_lang=target_lang)
    
    return clean_response(raw_response)

# Review mistakes
def review_mistakes(cursor):
    cursor.execute("SELECT user_input, mistake, correction FROM mistakes")
    mistakes = cursor.fetchall()
    if not mistakes:
        return "No mistakes recorded. Great job!"
    
    review = "=== Mistake Review ===\n"
    for i, (user_input, mistake, correction) in enumerate(mistakes, 1):
        review += f"{i}. You said: '{user_input}' | Mistake: '{mistake}' | Correction: '{correction}'\n"
    
    focus = "Focus area: Work on verb conjugation and vocabulary." if len(mistakes) > 2 else "Focus area: You’re doing well, keep practicing!"
    return review + focus

# Streamlit UI
def main():
    st.title("Language Learning Chatbot")
    
    # Initialize session state
    if "stage" not in st.session_state:
        st.session_state.stage = "setup"
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "target_lang" not in st.session_state:
        st.session_state.target_lang = None
    if "native_lang" not in st.session_state:
        st.session_state.native_lang = None
    if "level" not in st.session_state:
        st.session_state.level = None
    if "scene" not in st.session_state:
        st.session_state.scene = None

    # Get database connection
    conn, cursor = get_db_connection()

    # Setup stage
    if st.session_state.stage == "setup":
        st.write("Welcome! Let’s get started.")
        
        target_lang = st.text_input("What language do you want to learn? (e.g., Spanish, French)")
        native_lang = st.text_input("What language do you already know? (e.g., English)")
        level = st.selectbox("What’s your current level?", ["Beginner", "Intermediate", "Advanced"])
        
        if st.button("Next"):
            if target_lang and native_lang and level:
                st.session_state.target_lang = target_lang
                st.session_state.native_lang = native_lang
                st.session_state.level = level
                st.session_state.stage = "scene_selection"
            else:
                st.error("Please fill in all fields.")

    # Scene selection stage
    elif st.session_state.stage == "scene_selection":
        st.write(f"Choose a scene to practice your {st.session_state.target_lang}:")
        scene_options = get_scene_options(st.session_state.level)
        scene_choice = st.selectbox("Pick a scene:", scene_options)
        
        if st.button("Start Chatting"):
            st.session_state.scene = scene_choice
            st.session_state.stage = "chat"
            st.session_state.chat_history.append(f"Scene: {scene_choice}")

    # Chat stage
    elif st.session_state.stage == "chat":
        st.write(f"Scene: {st.session_state.scene}")
        st.write(f"Respond in {st.session_state.target_lang}. Type 'exit' to finish.")

        # Display chat history
        for message in st.session_state.chat_history:
            st.write(message)

        # User input
        user_input = st.text_input("You:", key="user_input")
        if st.button("Send"):
            if user_input:
                if user_input.lower() == "exit":
                    st.session_state.stage = "review"
                else:
                    # Bot response and feedback
                    bot_response = generate_response(user_input, st.session_state.target_lang, st.session_state.scene)
                    f = correct_input(user_input, st.session_state.target_lang, st.session_state.native_lang, conn, cursor)
                    feedback = clean_response(f)
                    
                    # Update chat history
                    st.session_state.chat_history.append(f"You: {user_input}")
                    st.session_state.chat_history.append(f"Bot: {bot_response}")
                    st.session_state.chat_history.append(f"Feedback: {feedback}")
                    st.rerun()  # Refresh to show updated chat

    # Review stage
    elif st.session_state.stage == "review":
        st.write("Chat ended. Here’s your review:")
        review = review_mistakes(cursor)
        st.write(review)
        if st.button("Start Over"):
            st.session_state.clear()  # Reset everything
            st.rerun()

    # Close database connection at the end of each run
    conn.close()

# Run the app
if __name__ == "__main__":
    main()
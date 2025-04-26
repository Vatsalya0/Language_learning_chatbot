import streamlit as st
import sqlite3
import re
import os
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize LLM
llm = ChatGroq(
    groq_api_key=os.getenv("GROQ_API_KEY"),
    model="deepseek-r1-distill-llama-70b",
    temperature=0.7,
)

# Database utility
def init_db():
    conn = sqlite3.connect("language_mistakes.db")
    conn.execute('''
        CREATE TABLE IF NOT EXISTS mistakes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_input TEXT,
            mistake TEXT,
            correction TEXT,
            timestamp TEXT
        )
    ''')
    conn.commit()
    return conn

# Scene options
SCENES = {
    "Beginner": [
        "You’re at a market buying fruit.",
        "You’re greeting a neighbor in your new town.",
        "You’re asking for directions to a park."
    ],
    "Intermediate": [
        "You’re ordering a meal at a restaurant.",
        "You’re shopping for clothes in a store.",
        "You’re booking a hotel room over the phone."
    ],
    "Advanced": [
        "You’re negotiating a business deal.",
        "You’re discussing a news article with a friend.",
        "You’re giving a presentation at work."
    ]
}

# Prompt templates
CORRECTION_PROMPT = PromptTemplate(
    input_variables=["input", "target", "native", "scene"],
    template=(
        "The user said: '{input}' in {target}.\n"
        "Correct any mistakes WITHOUT changing the writing system (Latin, Cyrillic, Devanagari, etc).\n"
        "Make corrections based on the context: {scene}.\n"
        "If correct, reply exactly 'Correct!'.\n"
        "Briefly explain corrections in {native}."
    )
)

RESPONSE_PROMPT = PromptTemplate(
    input_variables=["scene", "input", "target_lang"],
    template=(
        "Generate a response to '{input}' in '{target_lang}', staying consistent with the scene: {scene}.\n"
        "Use the same writing system as the input."
    )
)

# Utility functions
def clean_response(text):
    """Remove <think> tags."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

def correct_input(user_input, target_lang, native_lang, scene, conn):
    chain = LLMChain(llm=llm, prompt=CORRECTION_PROMPT)
    response = chain.run(input=user_input, target=target_lang, native=native_lang, scene=scene)
    
    if "Correct!" not in response:
        try:
            correction = response.split("Corrected to:")[1].split(".")[0].strip()
        except (IndexError, AttributeError):
            correction = "Parsing error - check LLM output."
        
        conn.execute(
            "INSERT INTO mistakes (user_input, mistake, correction, timestamp) VALUES (?, ?, ?, ?)",
            (user_input, user_input, correction, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
    
    return clean_response(response)

def generate_response(user_input, target_lang, scene):
    chain = LLMChain(llm=llm, prompt=RESPONSE_PROMPT)
    return clean_response(chain.run(scene=scene, input=user_input, target_lang=target_lang))

def review_mistakes(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT user_input, mistake, correction FROM mistakes")
    rows = cursor.fetchall()
    
    if not rows:
        return "🎉 No mistakes recorded. Excellent work!"
    
    review = "📝 **Mistake Review:**\n\n"
    for idx, (user_input, mistake, correction) in enumerate(rows, 1):
        review += f"{idx}. **You said:** '{user_input}'\n   **Mistake:** '{mistake}' ➔ **Correction:** '{correction}'\n\n"
    
    focus = "**Focus Area:** Verb conjugation and vocabulary improvement." if len(rows) > 2 else "**Focus Area:** Keep practicing!"
    return review + "\n\n" + focus

# Main App
def main():
    st.set_page_config(page_title="Language Learning Buddy", page_icon="🗣️")
    st.title("🗣️ Language Learning Chatbot")

    conn = init_db()

    if "stage" not in st.session_state:
        st.session_state.update({
            "stage": "setup",
            "chat_history": [],
            "target_lang": "",
            "native_lang": "",
            "level": "",
            "scene": "",
        })

    stage = st.session_state.stage

    if stage == "setup":
        with st.form("setup_form"):
            st.subheader("Let's get started!")
            st.session_state.target_lang = st.text_input("Language you want to learn:", value=st.session_state.target_lang)
            st.session_state.native_lang = st.text_input("Language you know:", value=st.session_state.native_lang)
            st.session_state.level = st.selectbox("Your current level:", list(SCENES.keys()), index=list(SCENES.keys()).index(st.session_state.level) if st.session_state.level else 0)
            if st.form_submit_button("Next"):
                if all([st.session_state.target_lang, st.session_state.native_lang, st.session_state.level]):
                    st.session_state.stage = "scene_selection"
                    st.rerun()
                else:
                    st.error("🚨 Please complete all fields.")

    elif stage == "scene_selection":
        with st.form("scene_form"):
            st.subheader(f"Choose a Scene for Practicing {st.session_state.target_lang}")
            scenes = SCENES.get(st.session_state.level, SCENES["Beginner"])
            st.session_state.scene = st.selectbox("Pick a Scene:", scenes)
            if st.form_submit_button("Start Chatting"):
                st.session_state.stage = "chat"
                st.session_state.chat_history.append(f"**Scene:** {st.session_state.scene}")
                st.rerun()

    elif stage == "chat":
        st.subheader(f"🎯 Scene: {st.session_state.scene}")
        st.markdown(f"✍️ Practice speaking in **{st.session_state.target_lang}**. (Type **'exit'** to finish.)")
        
        for msg in st.session_state.chat_history:
            st.markdown(msg)
        
        with st.form("chat_form", clear_on_submit=True):
            user_input = st.text_input("You:")
            if st.form_submit_button("Send") and user_input:
                if user_input.lower() == "exit":
                    st.session_state.stage = "review"
                    st.rerun()
                else:
                    bot_response = generate_response(user_input, st.session_state.target_lang, st.session_state.scene)
                    feedback = correct_input(user_input, st.session_state.target_lang, st.session_state.native_lang, st.session_state.scene, conn)
                    st.session_state.chat_history.extend([
                        f"🧑‍🎓 **You:** {user_input}",
                        f"🤖 **Bot:** {bot_response}",
                        f"📝 **Feedback:** {feedback}"
                    ])
                    st.rerun()

    elif stage == "review":
        st.success("✅ Chat ended. Here's your review:")
        st.markdown(review_mistakes(conn))
        if st.button("🔄 Start Over"):
            st.session_state.clear()
            st.rerun()

    conn.close()

if __name__ == "__main__":
    main()

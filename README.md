
# Language Learning Chatbot

A Streamlit web app for practicing languages through contextual conversations, powered by the Groq API  and SQLite. It offers real-time corrections, mistake tracking, and feedback based on user-selected scenes (e.g., shopping, business negotiations).

## Features

- Contextual conversation practice
- Instant feedback and corrections in your native language
- Mistake tracking with SQLite
- Proficiency levels (Beginner, Intermediate, Advanced) and scenes
- Intuitive Streamlit interface

## Tech Stack

- **Frontend**: Streamlit
- **Backend**: Python, SQLite
- **Language Model**: Groq API (`"deepseek-r1-distill-llama-70b"`)
- **Dependencies**: `streamlit`, `sqlite3`, `langchain_groq`, `python-dotenv`

## Installation

1. **Clone Repository**:
   ```bash
   git clone https://github.com/Vatsalya0/Language_learning_chatbot.git
   cd Language_learning_chatbot
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Environment**:
   Create a `.env` file:
   ```plaintext
   GROQ_API_KEY=your-grok-api-key
   ```

4. **Run App**:
   ```bash
   streamlit run main.py
   ```
   Visit [http://localhost:8501](http://localhost:8501).

## Usage

1. Enter target and native languages, select proficiency level.
2. Choose a scene (e.g., "You’re at a market buying fruit").
3. Chat in the target language, receive responses and corrections.
4. Type `exit` to review mistakes.
5. Click "Start Over" for a new session.

## Database

**mistakes** table:
- `id`: Auto-incrementing key
- `user_input`: User's input
- `mistake`: Mistaken input
- `correction`: Corrected input
- `timestamp`: Time of mistake

## Example

**Setup**: Target: Spanish, Native: English, Level: Beginner, Scene: Market  
**Chat**:  
- **You**: Quiero dos manzana.  
- **Bot**: ¡Claro! Aquí tienes dos manzanas.  
- **Feedback**: Mistake: 'manzana' should be plural. Corrected to: Quiero dos manzanas.

## Limitations

- Requires internet for Grok API
- Text-based only
- Predefined scenes

## Future Improvements

- Voice support
- Custom scenes
- Progress visualizations

## Contributing

1. Fork the repository.
2. Create a branch (`git checkout -b feature/your-feature`).
3. Commit changes (`git commit -m "Add feature"`).
4. Push (`git push origin feature/your-feature`).
5. Open a pull request.

## License

MIT License. See [LICENSE](LICENSE).

## Contact

For support, open a GitHub issue or email [vatsalyatripathi01@gmail.com](mailto:vatsalyatripathi01@gmail.com).

---

Happy learning! 🗣️

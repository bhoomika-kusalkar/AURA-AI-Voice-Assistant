# AURA — AI Voice Assistant 🎙️

AURA is a Python-based AI voice assistant that lets users interact with an AI through voice and text using a custom desktop interface.

## ✨ Features

- **Voice interaction:** Record spoken questions and transcribe them using OpenAI Whisper.
- **AI responses:** Generate answers using OpenAI's GPT-4o-mini model.
- **Text-to-speech:** Convert AI responses into spoken audio using Edge TTS.
- **Desktop interface:** Interactive dark-themed GUI built with CustomTkinter.
- **Continuous voice mode:** Support an ongoing voice interaction experience.
- **Animated voice indicator:** Visual feedback based on microphone input.
- **Conversation controls:** Start a new conversation or stop voice interaction.

## 🛠️ Tech Stack

- Python
- OpenAI API
- OpenAI Whisper
- GPT-4o-mini
- CustomTkinter
- Edge TTS
- SoundDevice
- Pygame
- SciPy

## 📁 Project Structure

```text
AI-Voice-Assistant/
├── main.py
├── frontend.py
├── .gitignore
├── .env.example
└── README.md
```

## ⚙️ Setup and Installation

### 1. Clone the repository

```bash
git clone https://github.com/bhoomika-kusalkar/AURA-AI-Voice-Assistant.git
cd AURA-AI-Voice-Assistant
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
venv\Scripts\activate
```

### 3. Install dependencies

Install the packages required by the project. See the project setup instructions for the exact dependency list.

### 4. Configure your API key

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

Replace the placeholder with your own API key. Never commit your real `.env` file.

### 5. Run AURA

```bash
python frontend.py
```

## 🎯 Project Goal

AURA explores the integration of speech recognition, large language models, text-to-speech, and a desktop user interface to create a more natural way to interact with AI.

## 👩‍💻 Developer

**Bhoomika Kusalkar**

Built as a hands-on AI application project using Python and modern AI tools.

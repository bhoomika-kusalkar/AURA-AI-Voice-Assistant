
import os
import asyncio
import uuid

import sounddevice as sd
from scipy.io.wavfile import write
from openai import OpenAI
from dotenv import load_dotenv
import edge_tts
import pygame


# -------------------- CONFIGURATION --------------------

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key or api_key == "put_your_actual_api_key_here":
    raise ValueError(
        "OpenAI API key missing. Check your .env file."
    )

client = OpenAI(api_key=api_key)

SAMPLE_RATE = 16000
RECORD_SECONDS = 6
VOICE = "en-US-AriaNeural"

pygame.mixer.init()


# -------------------- RECORD YOUR VOICE --------------------

def record_audio():
    """Record your voice for six seconds."""
    print("\n🎙️ Listening now — speak!")

    audio = sd.rec(
        int(RECORD_SECONDS * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16",
    )

    sd.wait()

    filename = "question.wav"
    write(filename, SAMPLE_RATE, audio)

    print("✅ Recording complete!")
    return filename


# -------------------- SPEECH TO TEXT --------------------

def transcribe_audio(filename):
    """Convert recorded speech into text."""
    print("📝 Understanding your words...")

    with open(filename, "rb") as audio_file:
        result = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
        )

    return result.text.strip()


# -------------------- AI RESPONSE --------------------

def ask_ai(question, history):
    """Answer the question and remember the conversation."""

    history.append({
        "role": "user",
        "content": question,
    })

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a friendly laptop voice assistant. "
                    "Answer naturally and clearly. Keep spoken "
                    "answers concise unless asked for details."
                ),
            },
            *history[-10:],
        ],
    )

    answer = response.choices[0].message.content or ""

    history.append({
        "role": "assistant",
        "content": answer,
    })

    return answer


# -------------------- TEXT TO SPEECH --------------------

async def speak(text):
    """Convert the AI answer to speech and play it."""

    filename = f"answer_{uuid.uuid4().hex}.mp3"

    try:
        print("🔊 Preparing voice...")

        communicate = edge_tts.Communicate(text, VOICE)
        await communicate.save(filename)

        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            await asyncio.sleep(0.1)

    finally:
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()

        if os.path.exists(filename):
            try:
                os.remove(filename)
            except PermissionError:
                print("⚠️ Could not remove temporary audio file yet.")


# -------------------- MAIN CONVERSATION LOOP --------------------

def main():
    print("\n🤖 YOUR AI VOICE ASSISTANT IS READY!")
    print("Press ENTER to speak.")
    print("Type Q and press ENTER to quit.\n")

    history = []

    try:
        while True:
            command = input(
                "Your turn — ENTER to talk, Q to quit: "
            ).strip().lower()

            if command == "q":
                print("👋 See you later!")
                break

            try:
                audio_file = record_audio()
                question = transcribe_audio(audio_file)

                if not question:
                    print("I couldn't hear anything. Try again.")
                    continue

                print(f"\n🧑 You: {question}")

                if question.lower() in {
                    "quit",
                    "exit",
                    "stop assistant",
                }:
                    print("👋 Goodbye!")
                    break

                answer = ask_ai(question, history)

                print(f"\n🤖 Assistant: {answer}\n")

                asyncio.run(speak(answer))

            except Exception as error:
                print(f"\n❌ Something went wrong: {error}")
                print("Check the API setup, internet, and audio devices.")

    except (KeyboardInterrupt, EOFError):
        print("\n👋 Assistant stopped.")

    finally:
        pygame.mixer.quit()


if __name__ == "__main__":
    main()

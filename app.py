import streamlit as st
import random
import time
from together import Together
from deepgram import DeepgramClient, SpeakOptions
from preferredsoundplayer import soundplay
import re

PASSWORD = st.secrets["password"]
TOGETHER_API_KEY=st.secrets["together_api_key"]
DEEPGRAM_API_KEY=st.secrets["deepgram_api_key"]
CHATBOT="meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo"
FILENAME="audio.mp3"
AUDIO_MODEL="aura-zeus-en"

deepgram = DeepgramClient(DEEPGRAM_API_KEY)

options = SpeakOptions(
model=AUDIO_MODEL,
)

#clients
client = Together(api_key=TOGETHER_API_KEY)
deepgram = DeepgramClient(DEEPGRAM_API_KEY)

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "reset_clicked" not in st.session_state:
    st.session_state.reset_clicked = False
if "grammar" not in st.session_state:
    st.session_state.grammar = ""
if "words" not in st.session_state:
    st.session_state.words = ""
if "topic" not in st.session_state:
    st.session_state.topic = ""
if "sys_prompt" not in st.session_state:
    st.session_state.sys_prompt = ""

def login():
    if st.session_state.password == PASSWORD:
        st.session_state.authenticated = True
    else:
        st.error("Incorrect password. Please try again.")

def reset_app():
    for key in list(st.session_state.keys()):
        if key not in ['authenticated', 'reset_clicked']:
            del st.session_state[key]
    st.session_state.reset_clicked = True
    st.session_state.grammar = ""
    st.session_state.words = ""
    st.session_state.topic = ""
    st.rerun()

# Authentication check
if not st.session_state.authenticated:
    st.title("Talk With Me!")
    st.write("Enter password below to enter chat...")
    with st.form("login_form"):
        st.text_input("Password", type="password", key="password")
        submit_button = st.form_submit_button("Enter")
        if submit_button:
            login()
else:
    # Chat page
    def split_text(text):
        split_text = re.split(r'(?<!\bMr)(?<!\bMrs)(?<=[.!?;])\s*|\n\n', text)
        return split_text

    def speak(split):
        for t in split:
            if t=="":
                continue
            text_to_speak={"text": t}
            deepgram.speak.rest.v("1").save(FILENAME, text_to_speak, options)
            soundplay(FILENAME)
        
        
    def response_generator(prompt):
        stream = client.chat.completions.create(
        model=CHATBOT,
        messages=st.session_state.messages,
        stream=True,
        )
        for chunk in stream:
            yield chunk.choices[0].delta.content
    
    def start_convo(topic,grammar,words):
        client = Together(api_key=TOGETHER_API_KEY)
        st.session_state.sys_prompt=f"""
                   Come up with a conversational scenario suitable for pre-school kids learning English as a second lan. Make sure that your conversation fulfills the following requirements.
                   Conversation Topic:{topic}
                   Grammars to Include:{grammar}
                   Words to Include:{words}
                   Firstly, start with describing the scenario in which the conversation is taking place.
                   The user will be roleplaying one of the characters in the scenario and you will be roleplaying all the other. Make sure to indicate who is talking. Finally, start off with the first line and only ONE line of the conversation and we will go back and forth.
                   IMPORTANT NOTES
                   ---------------
                   -The first line of the conversation should be that of your character.
                   -Keep the sentences short and easy to understand.
                   -Restrain on using too many compound sentences.
                   -Do not use any complex grammars except when explicitly mentioned to be included.
                   -You will only write dialogues for characters you play.
                   -No need to indicate that the user should speak by saying "Your turn!" or anything similar.
                   -Keep the scenario description short.
                   """
        stream = client.chat.completions.create(
        model=CHATBOT,
        messages=[{"role":"user","content":st.session_state.sys_prompt},],
        stream=True,
        temperature=0.7
        )
        for chunk in stream:
            yield chunk.choices[0].delta.content

    st.title("Talk With Me!")

    st.sidebar.header("Requirements")
    topic = st.sidebar.text_input("Topic", key="topic", value=st.session_state.topic)
    grammar = st.sidebar.text_input("Grammar", key="grammar", value=st.session_state.grammar)
    words = st.sidebar.text_input("Words", key="words", value=st.session_state.words)
    

    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    for i,message in enumerate(st.session_state.messages):
        if i==0:
            continue
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
    if st.sidebar.button("Start Conversation"):
        st.session_state.messages = []
        st.sidebar.success("Conversation has been started.")
        with st.chat_message("assistant"):
            response = st.write_stream(start_convo(topic,grammar,words))
        st.session_state.messages.append({"role": "user", "content": st.session_state.sys_prompt})
        st.session_state.messages.append({"role": "assistant", "content": response})
        split=split_text(response)
        speak(split)
        

    # Reset button
    if st.sidebar.button("Reset"):
        reset_app()

    if st.session_state.reset_clicked:
        st.sidebar.success("App has been reset.")
        st.session_state.reset_clicked = False
        
    if prompt := st.chat_input("Enter your response..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            response = st.write_stream(response_generator(prompt))
        st.session_state.messages.append({"role": "assistant", "content": response})
        split=split_text(response)
        speak(split)
        

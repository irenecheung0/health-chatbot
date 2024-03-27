import streamlit as st
import json
from openai import AzureOpenAI
from PIL import Image
import os
import json
from streamlit_mic_recorder import mic_recorder
from streamlit_mic_recorder import speech_to_text

st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    r"""
    <style>
    .stDeployButton {
            visibility: hidden;
        }
    </style>
    """, unsafe_allow_html=True
)

def load_schedule():
    if os.path.exists("medication_schedule.json"):
        with open("medication_schedule.json", "r") as f:
            return json.load(f)
    return None


icon = Image.open("/Users/sahilagarwal/Desktop/comp4461-chatbot/doc_image.png")
icon2 = Image.open("/Users/sahilagarwal/Desktop/comp4461-chatbot/u.png")

initial_content = {
    "isNextState": False,
    "resp": "Hello! I am Sketch, your chatbot that helps you keep track of your medication. "
            "How are you feeling today?",
    "data": ""
}

initial_content['prompt'] = json.dumps(initial_content)

if 'prescription' not in st.session_state:
    st.session_state.prescription = load_schedule()

if 'current_state' not in st.session_state:
    st.session_state.current_state = 'Greeting'

states = {
    'Greeting': {
        'next': 'AskDayOfWeek',
        'description': "Greet the user and ask how he is feeling today.",
        'collectedDataName': None  
    },
    'AskDayOfWeek': {
        'next': 'ProvideAdvice',
        'description': "Ask the user for the day of the week they want to know their medication for.",
        'collectedDataName': 'day_of_week'  
    },
    'ProvideAdvice': {
        'next': 'AskDayOfWeek',
        'description': "Provide the medication that the user has to take for a certain day.",
        'collectedDataName': None  
    },
    'Unhandled': {
        'next': None,
        'description': "Handle any unrelated or unclear inputs by guiding the user back to the conversation or asking "
                       "for clarification.",
        'collectedDataName': None  
    }
}


def next_state(current_state):
    """
    Determines the next state based on the current state.

    Parameters:
    - current_state: The current state of the conversation.

    Returns:
    - The name of the next state.
    """

    next_state = states[current_state]['next']


    if not next_state:
        return None

    return next_state


def create_model_prompt(user_content):
    current_state = st.session_state['current_state']

    state_description = states[current_state]['description']
    next_state = states[current_state]['next']
    next_state_description = states[next_state]['description'] if next_state else states[current_state]['description']
    possible_values = states[current_state].get('possible','anything')

    collected_data_json = json.dumps(st.session_state.get('user_data', {}))
    
    prompt = f""" Answer with a json object in a string without linebreaks, with a isNextState field as a boolean 
    value, a resp field with text value, a data field as a string value (the value of the current collected data, 
    if applicable, not all the collected data till now). You are a chatbot designed to provide 
    the medication that the user needs for the required day. The current state of your conversation with the user is 
    {current_state}, which means {state_description}. If the goal of the current state is satisfied, 
    the next state is {next_state}, which means {next_state_description}. The new response from the user is: 
    {user_content}. The collected data is: {collected_data_json}.

    Decide whether the goal of the current state is satisfied. If yes, make isNextState as true, otherwise as false. 
    If the isNextState is true, and the current state is about collecting data, put the collected data value (only 
    the value of the current data collection goal) in the data field, otherwise leave it empty. Provide your response 
    to the user in the resp field. If isNextState is true, proceed with the action of the next state (such as asking 
    questions); otherwise, try to reach the goal by giving a response. """

    return prompt


def get_response_from_model(client):
    msgs = [{"role": m['role'], "content": m['content']['prompt']} for m in st.session_state.messages]
    response = client.chat.completions.create(
        model=model_name,
        messages=msgs,
    )


    model_response = response.choices[0].message.content


    print(model_response)


    response_data = json.loads(model_response)

    return response_data

switch = st.session_state
if "themes" not in switch: 
  switch.themes = {"current_theme": "light",
                    "refreshed": True,
                    
                    "light": {"theme.base": "dark",
                              "theme.backgroundColor": "#1c1919",
                              "theme.primaryColor": "#c98bdb",
                              "theme.secondaryBackgroundColor": "#30a1e3",
                              "theme.textColor": "white",
                              "button_face": "🌙"},

                    "dark":  {"theme.base": "light",
                              "theme.backgroundColor": "white",
                              "theme.primaryColor": "#5591f5",
                              "theme.secondaryBackgroundColor": "#02c8de",
                              "theme.textColor": "#0a1464",
                              "button_face": "🔆"},
                    }
  

def Mode():
  previous_theme = switch.themes["current_theme"]
  theme = switch.themes["light"] if switch.themes["current_theme"] == "light" else switch.themes["dark"]
  for key, value in theme.items(): 
    if key.startswith("theme"): st._config.set_option(key, value)

  switch.themes["refreshed"] = False
  if previous_theme == "dark": switch.themes["current_theme"] = "light"
  elif previous_theme == "light": switch.themes["current_theme"] = "dark"

with st.sidebar:
    button = switch.themes["light"]["button_face"] if switch.themes["current_theme"] == "light" else switch.themes["dark"]["button_face"]
    st.button(button, on_click=Mode)
    if switch.themes["refreshed"] == False:
        switch.themes["refreshed"] = True
        st.rerun()
    openai_api_key = st.text_input("Azure OpenAI API Key", key="chatbot_api_key", type="password")
    speech_to_text(key='my_stt', callback=None, just_once=True)


model_name = "gpt-35-turbo"

st.title("Sketch - A smart advisor for post-surgery care")

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": initial_content}]

icons = {'user': icon2, 'assistant': icon}
for msg in st.session_state.messages:
    st.chat_message(msg["role"], avatar=icons[msg["role"]]).write(msg["content"]['resp'])

if not openai_api_key:
    st.info("Please add your Azure OpenAI API key to continue.")
    st.stop()   

voice_resp = None
if ('my_stt_output' in st.session_state and st.session_state.my_stt_output):     
    voice_resp = st.session_state.my_stt_output
    del st.session_state["my_stt_output"]
    st.session_state.messages.append(
        {"role": "user", "content": {'prompt': create_model_prompt(voice_resp), 'resp': voice_resp}}
    ) 
    st.chat_message("user", avatar = icon2).write(voice_resp)

    client = AzureOpenAI(
        api_key=openai_api_key,
        api_version="2023-12-01-preview",
        azure_endpoint="https://hkust.azure-api.net/",
    )
    model_resp = get_response_from_model(client)
    if model_resp['isNextState']:

        if model_resp['isNextState']:
            if 'user_data' not in st.session_state:
                st.session_state['user_data'] = {}
            if states[st.session_state['current_state']]['collectedDataName']:
                st.session_state['user_data'][states[st.session_state['current_state']]['collectedDataName']] = model_resp[
                'data']

        st.session_state['current_state'] = next_state(st.session_state['current_state'])
        if st.session_state['current_state'] == 'ProvideAdvice':
            schedule = st.session_state.prescription
            day_of_week = st.session_state['user_data']['day_of_week']

            if schedule and day_of_week in schedule:
                medication_info = "\n".join([f"{med}: {info}" for med, info in schedule[day_of_week].items()])
                if medication_info:
                    model_resp['resp'] = f"Here is your medication for {day_of_week}:\n{medication_info}"
                else:
                    model_resp['resp'] = f"You have no medication scheduled for {day_of_week}."
            else:
                model_resp['resp'] = f"No medication information found for {day_of_week}."
            st.session_state['current_state'] = next_state(st.session_state['current_state'])
    model_resp['prompt'] = json.dumps(model_resp)

    st.session_state.messages.append({"role": "assistant", "content": model_resp})
    st.chat_message("assistant", avatar=icon).write(model_resp['resp'])
   
user_resp = st.chat_input()
if user_resp:
    st.session_state.messages.append(
        {"role": "user", "content": {'prompt': create_model_prompt(user_resp), 'resp': user_resp}}
    ) 
    st.chat_message("user", avatar = icon2).write(user_resp)

    client = AzureOpenAI(
        api_key=openai_api_key,
        api_version="2023-12-01-preview",
        azure_endpoint="https://hkust.azure-api.net/",
    )
    model_resp = get_response_from_model(client)
    if model_resp['isNextState']:
        print(st.session_state.current_state,"Previous State")
        if model_resp['isNextState']:
            if 'user_data' not in st.session_state:
                st.session_state['user_data'] = {}
            if states[st.session_state['current_state']]['collectedDataName']:
                st.session_state['user_data'][states[st.session_state['current_state']]['collectedDataName']] = model_resp[
                'data']
        st.session_state['current_state'] = next_state(st.session_state['current_state'])
        print(st.session_state['current_state'], "Next State")
        if st.session_state['current_state'] == 'ProvideAdvice':
            schedule = st.session_state.prescription
            day_of_week = st.session_state['user_data']['day_of_week']

            if schedule and day_of_week in schedule:
                medication_info = "\n".join([f"{med}: {info}" for med, info in schedule[day_of_week].items()])
                if medication_info:
                    model_resp['resp'] = f"Here is your medication for {day_of_week}:\n{medication_info}"
                else:
                    model_resp['resp'] = f"You have no medication scheduled for {day_of_week}."
            else:
                model_resp['resp'] = f"No medication information found for {day_of_week}."
            st.session_state['current_state'] = next_state(st.session_state['current_state'])
    model_resp['prompt'] = json.dumps(model_resp)

    st.session_state.messages.append({"role": "assistant", "content": model_resp})
    st.chat_message("assistant", avatar=icon).write(model_resp['resp'])
    user_resp = None
#%%
import streamlit as st
from chat import DBQA,load_json


api_key = load_json('/home/chuang/Dev/Keys/openai_key.json')['ChatGPT']['API_KEY']
# Loading from a directory
Index_Save_Path = '/data/chuang/QA_LangChan/KB_Index/chroma'
QA_agent = DBQA(Index_Save_Path,api_key)
#%%
# Streamlit app UI
st.title("Documented Augumented QA")
st.sidebar.header("Instructions")
st.sidebar.info(
    '''This is a web application that allows you to interact with 2022 April WEO FM and GFSR with 
       the OpenAI API's implementation of the ChatGPT model.
       Enter a **query** in the **text box** and **press enter** to receive 
       a **response** from the ChatGPT
       '''
    )

def main():
    '''
    This function gets the user input, pass it to ChatGPT function and 
    displays the response
    '''
    # Get user input
    user_query = st.text_input("Enter query here, to exit enter :q","")
    if user_query != ":q" or user_query != "":
        # Pass the query to the ChatGPT function
        response = QA_agent.get_response(user_query)
        return st.write(f"\n\n  {response}")
main() 


# %%

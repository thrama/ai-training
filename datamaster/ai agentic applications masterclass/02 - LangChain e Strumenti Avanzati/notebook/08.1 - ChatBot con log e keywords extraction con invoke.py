"""
- Data Masters -
Creazione e gestione di un chatbot interattivo basato su modelli di linguaggio avanzati.

Utilizzando librerie come LangChain e Gradio, viene configurato un modello di chat (ChatOpenAI) con specifiche
personalizzate; viene definito un template di prompt per guidare le risposte del chatbot; è implementata una memoria
per la conversazione in modo da poter mantenere il contesto ed è sfruttata una catena di esecuzione (LangChain) per
gestire l'input e le risposte; durante l'interazione con l'utente vengono loggati alcuni elementi della conversazione.
Infine, il codice utilizza Gradio per creare un'interfaccia utente che permette una gradevole interazione in tempo
reale con il chatbot.
"""

# Iniziamo importando le librerie necessarie i moduli specifici di LangChain per la
# gestione dei modelli di chat e delle memorie e l'interfaccia utente Gradio


import os
from random import randrange
import time

from langchain_openai import ChatOpenAI  # pip install langchain-openai 
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts  import MessagesPlaceholder 
from langchain_core.prompts import ChatPromptTemplate
from langchain.messages import HumanMessage, AIMessage, SystemMessage

import gradio as gr  # pip install gradio



# Inizializzazione del modello di chat, un modello basato su LangChain che utilizza la classe
# "ChatOpenAI", specificando alcune opzioni come la chiave API di OpenAI, la temperatura e il
# numero massimo di token per generazione.
model = ChatOpenAI(openai_api_key=os.getenv("openai_key"), temperature=.75, max_tokens=1024, request_timeout=30)


# Definizione di un template di prompt
# Questo template verrà utilizzato per creare prompt di chat durante le conversazioni.
system_template = ("Act like an useful assistant and answer the user questions")

# -----------------------------------------------
# A regime il nostro prompt sarà strutturato così:
# > System message
# > History Message 1
# > History Message 2
# .
# .
# .
# > History Message N
# > Human Message (in input)
# -----------------------------------------------
prompt = ChatPromptTemplate([
    ("system", system_template),
    MessagesPlaceholder(variable_name="history"),
    ("user", "{input}"),
])

chain = prompt | model

chat_map = {}
def get_chat_history(session_id: str) -> InMemoryChatMessageHistory:
    if session_id not in chat_map:
        chat_map[session_id] = InMemoryChatMessageHistory()
    return chat_map[session_id]

chain_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history=get_chat_history,
    input_messages_key="input",
    history_messages_key="history"
)

def generate_response(session_id, input_text, history):
    """
    Gestione delle risposte del chatbot utilizzando la catena di esecuzione
    definita precedentemente per ottenere le risposte generated dal chatbot
    durante la generazione dell'output.
    :param session_id: identificatore univoco della sessione
    :param input_text: messaggio di input
    :param history: conversazioni passate (lista di tuple). Diverse dalla memoria interna. Viene utilizzato da gradio per gesitre l'interfaccia di chat
    """
    
    # Se l'input è vuoto, non fare nulla
    if not input_text or len(input_text.strip()) == 0:
        return session_id, "", history

    # Aggiungi il messaggio alla history (per mostrare la conversazione aggiornata alla UI di gradio)
    if history is None:
        history = []
    
    # Processo la risposta dell'LLM
    try:
        response = chain_with_history.invoke({"input": input_text}, config={"session_id": str(session_id)})
        print(response)
        response = response.content
        

        history.append({"role": "user", "content": input_text})
        history.append({"role": "assistant", "content": response})


        
        # Generazione di un riassunto della conversazione ed estrazione dei principali tag riscontrati
        try:
            summary_res = model.invoke([
                SystemMessage(
                    content="Extract the main keywords in the text into a comma-separated list, then summarize the text in"
                            " a very short form. Prefix the keywords with 'Keywords:' and the short summary with 'Summary:'"),
                HumanMessage(content=input_text + " " + response)
            ])
            
            print(f'\n--- Session {session_id} Summary --- \n')

            print("USER: ", input_text, "\n")
            print("AI: ", response, "\n")
            print(summary_res.content)
            print('--------------------------------\n')
            
        # Gestione errore della invoke di estrazione keyword    
        except Exception as e:
            print(f"Errore nella generazione del riassunto: {e}")
    
    # Gestione errore della invoke di risposta del LLM all'input dell'utente
    except Exception as e:
        print(f"Errore nell'elaborazione del messaggio: {e}")
        response = "Mi dispiace, si è verificato un errore nell'elaborazione della tua richiesta."
        history.append({"role": "user", "content": input_text})
        history.append({"role": "assistant", "content": response})
    
    return session_id, "", history



with gr.Blocks(css="""footer{display:none !important}""") as demo:
    
    # State per mantenere il session_id unico per ogni utente con lambda function per generare un ID univoco
    # nel formato [random_5cifre]_[timestamp_ms]_[random_5cifre]
    session_id_state = gr.State(value=lambda: f"{randrange(10000, 99999)}_{int(time.time() * 1000)}_{randrange(10000, 99999)}")

    chatbot = gr.Chatbot(type="messages")

    msg = gr.Textbox(placeholder="Scrivi qui il tuo messaggio", label="")
    
    # Gestione dell'invio del messaggio
    msg.submit(
        generate_response, 
        [session_id_state, msg, chatbot], 
        [session_id_state, msg, chatbot]
    )

demo.queue().launch(debug=True, share=True)
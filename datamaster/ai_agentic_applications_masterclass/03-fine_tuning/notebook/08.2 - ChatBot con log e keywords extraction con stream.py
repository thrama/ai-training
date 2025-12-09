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


# Inizializzazione del modello di chat
model = ChatOpenAI(openai_api_key=os.getenv("openai_key"), temperature=.75, max_tokens=1024, request_timeout=30)

# Prompt template
system_template = (
    "Act like a useful assistant and answer the user questions using the information the user gives to you during the conversation."
)

prompt = ChatPromptTemplate([
    ("system", system_template),
    MessagesPlaceholder(variable_name="history"),
    ("user", "{input}"),
])

# LangChain chain con memoria
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


def stream_response(session_id, input_text, history):
    
    if not input_text or len(input_text.strip()) == 0:
        yield session_id, "", history
        return

    if history is None:
        history = []

    partial_response = ""

    try:

        # stream() restituisce un generatore che emette man mano i token generati dal modello
        stream = chain_with_history.stream({"input": input_text}, config={"session_id": str(session_id)})

        # Iteriamo sopra il generatore token-by-token
        for token in stream:
            delta = token.content # Estraggo il token generato
            if delta:
                partial_response += delta  # Accumulo il testo man mano

                # Costruiamo una "history temporanea" per la UI di Gradio:
                # prendiamo l'intera conversazione pregressa (history),
                # aggiungiamo il nuovo input utente e la risposta parziale accumulata finora
                temp_history = history + [
                    {"role": "user", "content": input_text},
                    {"role": "assistant", "content": partial_response}
                ]

                # Facciamo lo yield intermedio per aggiornare l'interfaccia Gradio in tempo reale
                yield session_id, "", temp_history

        # Fine dello stream: abbiamo ricevuto tutta la risposta completa
        # Aggiorniamo ora la history vera (che manterrà la conversazione completa per Gradio e per la prossima richiesta)
        history.append({"role": "user", "content": input_text})
        history.append({"role": "assistant", "content": partial_response})


        try:
            summary_res = model.invoke([
                SystemMessage(
                    content="Extract the main keywords in the text into a comma-separated list, then summarize the text in a very short form. Please prefix the keywords with 'Keywords:' and the short summary with 'Summary:'"
                ),
                HumanMessage(content=input_text + " " + partial_response)
            ])

            print(f'\n--- Session {session_id} Summary --- \n')

            print("USER: ", input_text, "\n")
            print("AI: ", partial_response, "\n")
            print(summary_res.content)
            print('--------------------------------\n')

        except Exception as e:
            print(f"Errore nella generazione del riassunto: {e}")

    except Exception as e:
        print(f"Errore nello streaming: {e}")
        history.append({"role": "user", "content": input_text})
        history.append({"role": "assistant", "content": partial_response})
        yield session_id, "", history


with gr.Blocks(css="""footer{display:none !important}""") as demo:
    
    session_id_state = gr.State(value=lambda: f"{randrange(10000, 99999)}_{int(time.time() * 1000)}_{randrange(10000, 99999)}")
    
    chatbot = gr.Chatbot(type="messages")
    msg = gr.Textbox(placeholder="Scrivi qui il tuo messaggio", label="")

    msg.submit(
        stream_response, 
        [session_id_state, msg, chatbot], 
        [session_id_state, msg, chatbot]
    )

demo.queue().launch(debug=True, share=True)

import os
import json

from openai import OpenAI
from dotenv import load_dotenv

from helpers import *
from selecionar_persona import *
from tools_ecomart import *

load_dotenv()

# Inicializar cliente OpenAI
api_key = os.getenv("OPENAI_API_KEY")

cliente = OpenAI(api_key=api_key)
modelo = "gpt-4o"

# Carregar o contexto do arquivo especificado
contexto_path = "dados/ecomart.txt"
if not os.path.exists(contexto_path):
    raise FileNotFoundError(f"The context file '{contexto_path}' does not exist.")
contexto = carrega(contexto_path)

# def criar_lista_ids():
#         lista_ids_arquivos = []

#         file_dados = cliente.files.create(
#                 file=open("dados/dados_ecomart.txt", "rb"),
#                 purpose="assistants"
#         )
#         lista_ids_arquivos.append(file_dados.id)
        
#         file_politicas = cliente.files.create(
#                 file=open("dados/politicas_ecomart.txt", "rb"),
#                 purpose="assistants"
#         )
#         lista_ids_arquivos.append(file_politicas.id)

#         file_produtos = cliente.files.create(
#                 file=open("dados/produtos_ecomart.txt","rb"),
#                 purpose="assistants"
#         )

#         lista_ids_arquivos.append(file_produtos.id)

#         return lista_ids_arquivos

def criar_thread(vector_store):
    thread = cliente.beta.threads.create(
        tool_resources={
            'file_search': {
                'vector_store_ids': [vector_store.id]
            }
        }
    )
    return {
        'id': thread.id
    }

def create_vector_store():
    vector_store = cliente.beta.vector_stores.create(name='Ecomart Vector Store')

    file_paths = [
        'dados/dados_ecomart.txt',
        'dados/politicas_ecomart.txt',
        'dados/produtos_ecomart.txt'
    ]
    file_streams = [open(path, 'rb') for path in file_paths]

    cliente.beta.vector_stores.file_batches.upload_and_poll(
        vector_store_id=vector_store.id,
        files=file_streams
    )

    return vector_store

def criar_assistente(vector_store):
    assistente = cliente.beta.assistants.create(
        name="Atendente EcoMart",
        instructions = f"""
                        Você é um chatbot de atendimento a clientes de um e-commerce. 
                        Você não deve responder perguntas que não sejam dados do ecommerce informado!
                        Além disso, acesse os arquivos associados a você e a thread para responder as perguntas.
                        """,
        model = modelo,
        tools = minhas_tools,
        tool_resources={
            'file_search': {
                'vector_store_ids': [vector_store.id]
            }
        }
        
    )
    return assistente.id

def pegar_json():
        filename = "assistentes.json"

        if not os.path.exists(filename):
            vector_store = create_vector_store()
            thread = criar_thread(vector_store)
            assistant_id = criar_assistente(vector_store)
            data = {
                    "assistant_id": assistant_id,
                    "thread": thread,
                    'vector_store_id': vector_store.id,
            }
            with open(filename, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
            print("Arquivo 'assistentes.json' criado com sucesso.")

        try:
            with open(filename, "r", encoding="utf-8") as file:
                data = json.load(file)
                return data
        except FileNotFoundError:
            print("Arquivo 'assistentes.json' não encontrado.")
    

# Selecionar a persona
persona = personas.get("neutro")
if not persona:
    raise ValueError("Persona 'neutro' not found in personas.")


import os
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# carrega variáveis de ambiente do arquivo .env
load_dotenv()

# recupera  chave da API do OMDB do arquivo .env
API_KEY = os.getenv("OMDB_API_KEY")
BASE_URL = "http://www.omdbapi.com/"

app = FastAPI()

# Configura o middleware CORS para permitir solicitações do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas as origens -->> ALTERAR PARA FRONTEND ESPECÍFICO EM PRODUÇÃO
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos os métodos HTTP  
    allow_headers=["*"],  # Permite todos os cabeçalhos
)

# busca de um título específico no OMDB pelo ID do IMDB ou pelo título
@app.get("/buscarTitulo")
def search_omdb(titulo: str = None, imdb_id: str = None):
    if not titulo and not imdb_id:
        raise HTTPException(status_code=400, detail="Title or IMDb ID must be provided.")

    parametros = {"apikey": API_KEY}
    if titulo:
        parametros["t"] = titulo
    if imdb_id:
        parametros["i"] = imdb_id

    response = requests.get(BASE_URL, params=parametros)
    
    if response.status_code == 200:
        data = response.json()
        if data.get("Response") == "True":
            return {
                'titulo': data.get("Title"),
                'ano': data.get("Year"),
                'poster': data.get("Poster"),
            }
        else:
            raise HTTPException(status_code=404, detail=data.get("Error", "Movie not found."))
    else:
        raise HTTPException(status_code=response.status_code, detail="Error fetching data from OMDB API.")
    
# busca de múltiplos títulos no OMDB pelo ID do IMDB
@app.get("/buscarShowsAssistindo")
def search_omdb_multiple(imdb_ids: str):
    imdb_id_list = imdb_ids.split(',')
    results = []

    for imdb_id in imdb_id_list:
        parametros = {"apikey": API_KEY, "i": imdb_id}
        response = requests.get(BASE_URL, params=parametros)

        if response.status_code == 200:
            data = response.json()
            if data.get("Response") == "True":
                results.append({
                    'titulo': data.get("Title"),
                    'ano': data.get("Year"),
                    'poster': data.get("Poster"),
                })
            else:
                raise HTTPException(status_code=404, detail=f"Show with IMDb ID {imdb_id} not found.")
        else:
            raise HTTPException(status_code=response.status_code, detail=f"Error fetching data for IMDb ID {imdb_id}.")

    return results
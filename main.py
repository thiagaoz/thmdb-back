import math
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


# busca de múltiplos títulos no OMDB pelo ID do IMDB
@app.get("/busca-atracoes")
def search_omdb_multiple(imdb_ids: str, rating_th: float = None):
    imdb_id_list = imdb_ids.split(',')
    results = []

    for imdb_id in imdb_id_list:
        parametros = {"apikey": API_KEY, "i": imdb_id}
        response = requests.get(BASE_URL, params=parametros)

        if response.status_code == 200:
            data = response.json()
            
            if data.get("Response") == "True":
                if data.get("Type") == "episode":  # Ignora episódios, pois não queremos exibir episódios na lista de atrações
                    continue 

                results.append({
                    'imdb_id': imdb_id,
                    'title': data.get("Title"),
                    'plot': data.get("Plot"),
                    'poster': data.get("Poster"),
                    'genre': data.get("Genre"),
                    'rating_th': math.floor(rating_th + 0.5) if rating_th is not None else None,  # Arredonda a nota para o inteiro mais próximo
                    'type': selecionar_tipo(data.get("Genre"), data.get("Type")),  # Adiciona o tipo (movie, series, etc.)
                    'year': data.get("Year"),
                    'seasons': data.get("totalSeasons") if data.get("totalSeasons") is not None else None  # Adiciona o número de temporadas, se disponível
                })
            else:
                raise HTTPException(status_code=404, detail=f"Error fetching data for IMDb ID {imdb_id}: {data.get('Error', 'Movie not found.')}")
        
        else:
            raise HTTPException(status_code=response.status_code, detail=f"Error fetching data for IMDb ID {imdb_id}.")

    return results

def selecionar_tipo(genre, type: str):
    if genre.lower() == "stand-up":
        return "Stand-up"
    elif type == "movie":
        return "Filme"
    elif type == "series":
        return "Série"
    elif type == "game":
        return "Jogo"
    else:
        return "Outro"
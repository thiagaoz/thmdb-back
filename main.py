import csv
import json
import os
import requests
from dotenv import load_dotenv
from pathlib import Path
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

def selecionar_tipo(type: str):
    if type == "movie":
        return "Filme"
    elif type == "series":
        return "Série"
    elif type == "game":
        return "Jogo"
    else:
        return "Outro"

# busca de múltiplos títulos no OMDB pelo ID do IMDB
@app.get("/busca-atracoes")
def search_omdb_multiple(ids: str):
    id_list = ids.split(',')
    results = []

    for id in id_list:
        parametros = {"apikey": API_KEY, "i": id}
        response = requests.get(BASE_URL, params=parametros)

        if response.status_code == 200:
            data = response.json()
            
            if data.get("Response") == "True":
                if data.get("Type") == "episode":  # Ignora episódios, pois não queremos exibir episódios na lista de atrações
                    continue 

                results.append({
                    'id': id,
                    'title': data.get("Title"),
                    'plot': data.get("Plot"),
                    'poster': data.get("Poster"),
                    'genre': data.get("Genre"),
                    #'rating_th': math.floor(rating_th + 0.5) if rating_th is not None else None,  # Arredonda a nota para o inteiro mais próximo
                    'type': selecionar_tipo(data.get("Type")),  # Adiciona o tipo (movie, series, etc.)
                    'year': data.get("Year"),
                    'seasons': data.get("totalSeasons") if data.get("totalSeasons") is not None else None  # Adiciona o número de temporadas, se disponível
                })
            else:
                raise HTTPException(status_code=404, detail=f"Error fetching data for IMDb ID {id}: {data.get('Error', 'Movie not found.')}")
        
        else:
            raise HTTPException(status_code=response.status_code, detail=f"Error fetching data for IMDb ID {id}.")

    return results

# Mapping CSV column names to JSON keys
novo_nome = {
    "Const": "id",
    "Your Rating": "rating_th",
    "Title": "title",
    "Title Type": "type",
    "Genres": "genre",
    "Directors": "directors",
    "URL": "url",
}

caminho_imdb_csv = "../frontend/src/data/imdb_ratings.csv"
caminho_imdb_json = "../frontend/src/data/imdb.json"
caminho_atracao_json = "../frontend/src/data/atracao.json"

atributos_selecionados = ["Const", "Your Rating", "Title", "Title Type", "Genres", "Directors", "URL"]

@app.get("/imdb_csv_to_json")
def imdb_csv_to_json() -> str:
    """Converts the IMDb CSV file to a JSON file."""
    data = []
    Path(caminho_imdb_json).parent.mkdir(parents=True, exist_ok=True)

    with open(caminho_imdb_csv, mode="r", encoding="utf-8") as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            colunas_filtradas = {
                novo_nome.get(coluna, coluna): row[coluna]
                for coluna in atributos_selecionados
                if coluna in row
            }

            if "rating_th" in colunas_filtradas:
                try:
                    colunas_filtradas["rating_th"] = float(colunas_filtradas["rating_th"])
                except ValueError:
                    colunas_filtradas["rating_th"] = None

            data.append(colunas_filtradas)

    with open(caminho_imdb_json, mode="w", encoding="utf-8") as json_file:
        json.dump(data, json_file, indent=4, ensure_ascii=False)

    response = f"✅ Arquivo JSON gerado com sucesso em: {caminho_imdb_json}"
    print(response)
    return response

@app.get("/imdb_to_atracao")
def imdb_to_atracao() -> str:
    """Complementa os dados do JSON do IMDb com informações do OMDb."""
    if not Path(caminho_imdb_json).exists():
        raise HTTPException(
            status_code=404,
            detail=f"Arquivo de origem não encontrado: {caminho_imdb_json}. Execute /imdb_csv_to_json primeiro.",
        )

    with open(caminho_imdb_json, mode="r", encoding="utf-8") as f:
        imdb_data = json.load(f)

    if not imdb_data:
        raise HTTPException(
            status_code=400,
            detail=f"O arquivo {caminho_imdb_json} está vazio.",
        )

    results = []
    erros = 0

    for atracao in imdb_data:
        atracao_id = atracao.get("id")
        if not atracao_id:
            print("⚠️ Item sem o campo 'id' ignorado.")
            erros += 1
            continue

        try:
            params = {"apikey": API_KEY, "i": atracao_id}
            response = requests.get(BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            omdb_data = response.json()

            if omdb_data.get("Response") == "True":
                results.append({
                    **atracao,
                    "plot": omdb_data.get("Plot"),
                    "poster": omdb_data.get("Poster"),
                    "year": omdb_data.get("Year"),
                    "seasons": omdb_data.get("totalSeasons"),
                })
            else:
                print(f"⚠️ Filme não encontrado no OMDb ID {atracao_id}: {omdb_data.get('Error')}")
                erros += 1
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro de requisição para {atracao_id}: {e}")
            erros += 1
        except KeyError as e:
            print(f"❌ Chave ausente em {atracao_id}: {e}")
            erros += 1

    Path(caminho_atracao_json).parent.mkdir(parents=True, exist_ok=True)
    with open(caminho_atracao_json, mode="w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    msg = f"✅ Processamento concluído: {len(results)} atrações salvas em {caminho_atracao_json} ({erros} falhas)."
    print(msg)
    return msg


if __name__ == "__main__":
    try:
        imdb_csv_to_json()
    except Exception as e:
        print(f"❌ Erro ao converter CSV para JSON: {e}")


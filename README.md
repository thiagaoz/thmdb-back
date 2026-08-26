# THMDB Backend

O backend é a parte responsável por buscar e preparar informações para o
frontend. Ele consulta serviços externos, converte os dados exportados do IMDb
e atualiza os arquivos locais usados pelo site.

## Arquivos principais

- **`main.py`:** inicia a API e concentra os endpoints usados pelo frontend.
  Faz buscas de filmes e séries no TMDB e oferece os comandos de conversão.
- **`tmdb.py`:** reúne funções de apoio para consultar o TMDB e transformar
  resultados em dados de atrações.
- **`watchlist.py`:** transforma a watchlist exportada do IMDb em JSON,
  complementando os títulos com informações do TMDB.
- **`imdb_to_atracao.py`:** lê as avaliações do IMDb e cria ou atualiza os
  dados gerais de filmes e séries.
- **`imdb_to_assitindo.py`:** prepara os dados das séries que estão sendo
  acompanhadas, usando informações do OMDb.
- **`corretor_atracoes.py`:** revisa os dados das atrações e padroniza campos
  como avaliação e quantidade de temporadas.
- **`atualizar_runtime.py`:** atualiza a duração dos títulos a partir dos dados
  exportados do IMDb.
- **`requirements.txt`:** lista os pacotes Python usados pelo projeto.
- **`.env`:** guarda as chaves das APIs. Esse arquivo é privado e não deve ser
  publicado ou compartilhado.

## API disponível

- **`/busca-atracoes-title`:** procura filmes e séries pelo título no TMDB.
- **`/converter`:** dispara a atualização dos dados gerais de atrações.
- **`/converter-watchlist`:** dispara a atualização dos dados da watchlist.
- **`/docs`:** exibe a documentação interativa gerada pelo FastAPI.

## Fluxo geral

O usuário interage com o frontend. Quando precisa pesquisar um título, o
frontend chama o backend. O backend consulta o TMDB, organiza a resposta e
devolve os dados em um formato que os cards conseguem exibir.

Os scripts de conversão têm outra função: eles mantêm os arquivos JSON do
frontend atualizados a partir das exportações do IMDb e das informações das
APIs externas.

## Outros

- Python com FastAPI para criar a API.
- Uvicorn para executar o servidor web.
- Requests para acessar TMDB e OMDb.
- python-dotenv para ler as variáveis do arquivo `.env`.
- Pacotes listados em `requirements.txt`: `brotli`, `certifi`, `charset-normalizer`,
  `idna`, `mutagen`, `pycryptodomex`, `python-dotenv`, `requests`, `urllib3`,
  `websockets`, `yt-dlp`, `yt-dlp-ejs`, `fastapi` e `uvicorn`.
- O servidor local usa a porta `8000`. No Render, o serviço usa a porta
  fornecida pela variável `$PORT`.
- A publicação usa um Web Service Python no Render.
- As chaves `TMDB_API_KEY` e `OMDB_API_KEY` são lidas do ambiente. A chave do

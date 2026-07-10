# busca o arquivo original do imdb.csv e converte para type Atracao em json na mesma pata frontend/src/data

import csv
import json

novo_nome = {
    "Const" : "id",
    "Your Rating": "rating_th"
}

def imdb_para_atracao(caminho_csv:str, caminho_json: str, atributos_selecionados: list[str]) -> None:
    data =[]

    with open(caminho_csv, mode='r', encoding='utf-8') as imbd_file:
        csv_reader = csv.DictReader(imbd_file)
        for row in csv_reader:
            
            colunas_filtradas = {
                novo_nome.get(coluna, coluna) : row[coluna]
                for coluna in atributos_selecionados
                if coluna in row
            }

            if "rating_th" in colunas_filtradas:
                colunas_filtradas["rating_th"] = float(colunas_filtradas["rating_th"])
                
            data.append(colunas_filtradas)

    with open(caminho_json, mode='w', encoding='utf-8') as atracao_json:
        json.dump(data, atracao_json, indent=4, ensure_ascii=False)

    print(f"Arquivo JSON gerado com sucesso em {caminho_json}")

if __name__ == "__main__":
    try:
        caminho_csv = "../frontend/src/data/imdb_ratings.csv"
        caminho_json = "../frontend/src/data/imdb_ids.json"
        atributos_selecionados = ["Const", "Your Rating"]

        imdb_para_atracao(caminho_csv, caminho_json, atributos_selecionados)

    except Exception as e:
        print("Ocorreu um erro:")
        print(e)

    finally:
        input("\nPressione Enter para fechar...")

    


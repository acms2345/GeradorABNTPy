from geradorabnt import citacaoInLine, citacaoRef
import requests
from bs4 import BeautifulSoup


while True:

    url = input("Insira a URL da fonte: ")

    if url == 'sair': break


    headers = {
        "User-Agent": "Mozilla/5.0"
    }


    doc = requests.get(url)

    if doc.status_code == 200:
        soup = BeautifulSoup(doc.content, 'html.parser')

        pastaEscolha = input("Em qual pasta irás salvar?: ")



        print(citacaoInLine(soup, url, pastaEscolha))
        print(citacaoRef(pastaEscolha, url))
    else:
        print(f"Erro ao ler fonte. Código do erro: {doc.status_code}")




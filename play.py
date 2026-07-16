from geradorabnt import citacaoInLine, citacaoRef
import requests
import re
import unicodedata
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

        pasta = unicodedata.normalize('NFKD', pastaEscolha).encode('ASCII', 'ignore').decode('ASCII')

        pasta.replace(" ", "_")

        pasta = re.sub(r'[\\/*?:"<>|]', "", pasta)

        nome_limpo = re.sub(r'[^a-zA-Z0-9_-]', '', pasta)




        print(citacaoInLine(soup, url, pasta))
        print(citacaoRef(pasta, url))
    else:
        print(f"Erro ao ler fonte. Código do erro: {doc.status_code}")




import geradorabnt
import requests
from bs4 import BeautifulSoup


url = input("Insira a URL da fonte: ")


headers = {
    "User-Agent": "Mozilla/5.0"
}


doc = requests.get(url)

if doc.status_code == 200:
    soup = BeautifulSoup(doc.content, 'html.parser')

    print(geradorabnt.obterDadosABNT(soup))
else:
    print(f"Erro ao adicionar fonte. Código do erro: {doc.status_code}")




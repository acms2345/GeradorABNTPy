import requests
from bs4 import BeautifulSoup

import json
from datetime import date



def obterDadosABNT(soup):
    """{
    "autor": ...,
    "tipo_autor": "pessoa" | "instituicao" | "desconhecido",
    "titulo_parte": ...,
    "titulo_todo": ...,   # nome do site, em itálico na hora de montar
    "data_publicacao": ...,  # pode ser None
    "data_acesso": ...,
    "url": ...
    }"""

    #Essa é a estrutura a ser seguida
    autor = None
    tipo_autor = None
    tituloCompleto= None
    dataPublicacao = None
    dataAcesso = None
    urlSite = None

    dadosABNT = None

    if soup.find('script', type='application/ld+json'):
        scriptTag = soup.find('script', type='application/ld+json')
        dadosABNT = json.loads(scriptTag.string)

        autorDados = dadosABNT.get('author', {})
        autor = autorDados.get('name')
        tipo_autor = autorDados.get('@type')
        tituloCompleto = dadosABNT.get('headline')
        dataPublicacao = autorDados.get('datePublished')
        dataAcesso = date.today()
        urlSite = dadosABNT.get('url')
        
        
    elif soup.find('div', class_='citacao-txt'):
        citacao_abnt = (soup.find('div', class_='citacao-txt')).get_text().strip()

    elif soup.find('p', class_='citation'):
        citacao_abnt = (soup.find('p', class_='citation')).get_text().strip()
    
    else:
    
        titulo = soup.find('h1')

    return citacao_abnt



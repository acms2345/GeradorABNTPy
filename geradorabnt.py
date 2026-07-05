import requests
from bs4 import BeautifulSoup

import json
from datetime import date

def carregarJSONLD(jsonldsPuros):
    listaJSONLDs = []
    
    for scriptTag in jsonldsPuros:
        try:
            conversao = json.loads(scriptTag)
            listaJSONLDs.append(conversao.string)
        except (json.JSONDecodeError, TypeError):
            continue
    
    return listaJSONLDs


def obterDadosABNT(soup):
    """
    São coletadas as seguintes informações:
    autor, tipo_autor, tituloCompleto, data_publicacao, data_acesso e url.

    Primeiro, é feita a análise para saber se o site possui um JSON-LD, 
    arquivo de indexação que pode servir como base de obtenção.
    Se tiver, coleta-se as informações com base nele.

    Senão...
    """

    #Essa é a estrutura a ser seguida
    autor = None
    tipo_autor = None
    tituloCompleto= None
    dataPublicacao = None
    dataAcesso = None
    urlSite = None

    dadosSite = None

    JSONLD = soup.find_all('script', type='application/ld+json')

    if JSONLD:
        try:
            for dadosSiteTeste in carregarJSONLD(JSONLD):
                if(dadosSiteTeste.get('@type') in {'Article', 'NewsArticle', 'BlogPosting'} ): 
                    dadosSite = dadosSiteTeste
                    break
            if not dadosSite:
                raise ValueError("Nenhum JSON-LD compatível encontrado.")
            
            autorDados = dadosSite.get('author', {})
            autor = autorDados.get('name')
            autorPartesNome = autor.strip().split()
            autorSobrenome = autorPartesNome[-1].upper()
            autorNomeResto = " ".join(autorPartesNome[:-1])
            
            tipo_autor = autorDados.get('@type')

            tituloCompleto = dadosSite.get('headline')
            dataPublicacao = autorDados.get('datePublished')
            dataAcesso = date.today()
            urlSite = dadosSite.get('url')
            


        except Exception as e:
            dadosSite = None
            

        

        
        
        
    """if not dadosSite and soup.find('div', class_='citacao-txt'):
        citacao_abnt = (soup.find('div', class_='citacao-txt')).get_text().strip()

    elif soup.find('p', class_='citation'):
        citacao_abnt = (soup.find('p', class_='citation')).get_text().strip()
    
    else:
    
        titulo = soup.find('h1')

    return citacao_abnt"""


def citacaoInLine():
    pass

def citacaoRef():
    pass



import requests
from bs4 import BeautifulSoup

import json
from datetime import date, datetime
import re

def carregarJSONLD(jsonldsPuros):
    listaJSONLDs = []
    
    for scriptTag in jsonldsPuros:
        try:
            conversao = json.loads(scriptTag.string)
            listaJSONLDs.append(conversao)
        except (json.JSONDecodeError, TypeError):
            continue
    
    return listaJSONLDs


def obterDadosABNT(soup):
    """
    São coletadas as seguintes informações:
    autor, tipo_autor, tituloCompleto, data_publicacao, data_acesso e url.
    
    Esses são retornados em um dicionário

    Primeiro, é feita a análise para saber se o site possui um JSON-LD, 
    arquivo de indexação que pode servir como base de obtenção.
    Se tiver, coleta-se as informações com base nele.

    Senão...
    """

    #Essa é a estrutura a ser seguida
    autor = []
    tipo_autor = None
    tituloCompleto= None
    anoPublicacao = None
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
            
            
            
            if autorDados:
              if isinstance(autorDados, list):
                for autorIndividual in autorDados:
                  nomeCompleto = autorIndividual.get('name')

                  autorPartesNome = nomeCompleto.strip().split()
                  autorSobrenome = autorPartesNome[-1].upper()
                  autorNomeResto = " ".join(autorPartesNome[:-1])

                  autor.append({
                      'sobrenome' : autorSobrenome,
                      'nomeResto' : autorNomeResto
                  })
              if isinstance(autorDados, dict):
                autor = [autor]
                nomeCompleto = autorDados.get('name')
                autorPartesNome = nomeCompleto.strip().split()
                autorSobrenome = autorPartesNome[-1].upper()
                autorNomeResto = " ".join(autorPartesNome[:-1])

                autor = {
                    'sobrenome' : autorSobrenome,
                    'nomeResto' : autorNomeResto
                }

            
            tipo_autor = autorDados.get('@type')

            tituloCompleto = dadosSite.get('headline')
            dataPublicacao = dadosSite.get('datePublished')
            if dataPublicacao:
                try:
                    if isinstance(dataPublicacao, (int, float)):
                        anoPublicacao = int(dataPublicacao)
                    elif isinstance(dataPublicacao, str):
                        verificacao = re.search(r'\d{4}', dataPublicacao)
                        if verificacao:
                            anoPublicacao = int(verificacao.group(0))
                        else:
                            anoPublicacao = datetime.fromisoformat(dataPublicacao).year
                except Exception:
                    anoPublicacao = None
            
            dataAcesso = date.today()
            urlSite = dadosSite.get('url')
            


        except Exception as e:
            dadosSite = None
        
    
    return {
      "autor" : autor,
      "tipoAutor" : tipo_autor, 
      "tituloCompleto" : tituloCompleto, 
      "anoPublicacao" : anoPublicacao, 
      "dataAcesso" : dataAcesso, 
      "url" : urlSite
    }
    


def citacaoInLine(soup):
    dadosABNT = obterDadosABNT(soup)

    pedacosCitacaoInLine = []

    pedacosCitacaoInLine.append('(')

    anoPublicacao = dadosABNT.get('anoPublicacao')
    autor = dadosABNT.get('autor')
    if isinstance(autor, list):
        if len(autor) > 3:
            texto = f"{autor[1]} et al., "
            pedacosCitacaoInLine.append(texto)
        else:
            for i in range(2):
                texto = f"{autor[i].get('sobrenome')}, "
                pedacosCitacaoInLine.append(texto)

    else:
        sobrenome = autor.get('sobrenome')
        pedacosCitacaoInLine.append(f"{autor[i].get('sobrenome')}, ")

    pedacosCitacaoInLine.append(f"{anoPublicacao})")

    citacaoInLine = "".join(pedacosCitacaoInLine)

    return citacaoInLine

    

    
    

    
    

def citacaoRef(soup):
    dadosABNT = obterDadosABNT(soup)

    if not dadosABNT:
        if soup.find('div', class_='citacao-txt'):
            citacao_abnt = (soup.find('div', class_='citacao-txt')).get_text().strip()

        elif soup.find('p', class_='citation'):
            citacao_abnt = (soup.find('p', class_='citation')).get_text().strip()
    

    return citacao_abnt



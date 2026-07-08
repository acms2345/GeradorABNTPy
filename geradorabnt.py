import requests
from bs4 import BeautifulSoup

import json
from datetime import date, datetime
import re

import colorama


from citeproc import CitationStylesStyle, CitationStylesBibliography
from citeproc import formatter
from citeproc import Citation, CitationItem
from citeproc.source.json import CiteProcJSON

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
    nomeSite = None
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

                  if autorIndividual.get('@type') == 'Organization' or tipo_autor == 'Organization':
                      tipo_autor = 'Organization'

                      nomeCompleto = nomeCompleto.upper()

                      autor.append({'instituicao' : nomeCompleto})
                      continue

                
                
                  
                  autorPartesNome = nomeCompleto.strip().split()
                  autorSobrenome = autorPartesNome[-1].upper()
                  autorNomeResto = " ".join(autorPartesNome[:-1])


                  autor.append({
                      'family' : autorSobrenome,
                      'given' : autorNomeResto
                  })
              if isinstance(autorDados, dict):
                nomeCompleto = autorDados.get('name')
                tipo_autor = autorDados.get('@type')

                if tipo_autor == 'Organization':
                    nomeCompleto = nomeCompleto.upper()
                    autor = {
                        'literal' : nomeCompleto
                    }
                else:
                    autorPartesNome = nomeCompleto.strip().split()
                    autorSobrenome = autorPartesNome[-1].upper()
                    autorNomeResto = " ".join(autorPartesNome[:-1])

                    autor.append({
                        'family' : autorSobrenome,
                        'given' : autorNomeResto
                    })

            
            

            tituloCompleto = dadosSite.get('headline')

            nomeSiteDados = dadosSite.get('publisher', {})
            if nomeSiteDados:
                nomeSite = nomeSiteDados.get('name')
            elif dadosSite.get('name'):
                nomeSite = dadosSite.get('name')
            
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
                
            urlSite = dadosSite.get('url')
            
            
            


        except Exception as e:
            dadosSite = None
        
    dataAcessoPura = date.today()

    meses = ['jan.', 'fev.', 'mar.', 'abr.', 'mai.', 'jun.', 'jul.', 'ago.', 'set.', 'out.', 'nov.', 'dez.']
    dataAcesso = f"{dataAcessoPura.day} {meses[dataAcessoPura.month - 1]} {dataAcessoPura.year}"
        
        
    
    if anoPublicacao == None:
        return {
            "author" : autor,
            ##"tipoAutor" : tipo_autor, 
            "title" : tituloCompleto, 
            "accessed" : {"date-parts": [[dataAcessoPura.year, dataAcessoPura.month, dataAcessoPura.day]]}, 
            "URL" : urlSite,
            "container-title" : nomeSite,
            "type" : "webpage",
            "id" : urlSite
        }
    else:
        return {
            "author" : autor,
            ##"tipoAutor" : tipo_autor, 
            "title" : tituloCompleto, 
            "issued" : {"date-parts" : [[anoPublicacao]]}, 
            "accessed" : {"date-parts": [[dataAcessoPura.year, dataAcessoPura.month, dataAcessoPura.day]]}, 
            "URL" : urlSite,
            "container-title" : nomeSite,
            "type" : "webpage",
            "id" : urlSite
        }
    


def citacaoInLine(soup):
    dadosABNT = obterDadosABNT(soup)

    pedacosCitacaoInLine = []

    pedacosCitacaoInLine.append('(')

    anoPublicacao = dadosABNT.get('anoPublicacao')
    autor = dadosABNT.get('autor')
    
    if isinstance(autor, list):
        if len(autor) > 3:
            texto = f"{autor[0].get('sobrenome')} et al., "
            pedacosCitacaoInLine.append(texto)
        else:
            for i in range(2):
                texto = f"{autor[i].get('sobrenome')}, "
                pedacosCitacaoInLine.append(texto)

    else:
        sobrenome = autor.get('sobrenome')
        pedacosCitacaoInLine.append(f"{autor.get('sobrenome')}, ")

    pedacosCitacaoInLine.append(f"{anoPublicacao})")

    citacaoInLine = "".join(pedacosCitacaoInLine)

    return bibliografia.cite(citacao, lambda x: None)

    

    
    

    
    

def citacaoRef(soup):
    dadosABNT = obterDadosABNT(soup)

    id = dadosABNT.get('id')

    dadosBibliograficos = [dadosABNT]

    print("DEBUG dadosBibliograficos:", json.dumps(dadosBibliograficos, ensure_ascii=False, indent=2))

    fonteCiteprocPY = CiteProcJSON(dadosBibliograficos)
    estilo = CitationStylesStyle('ibict-abnt.csl', validate=False)


    # 3. Criar a bibliografia e registrar citação
    bibliografia = CitationStylesBibliography(estilo, fonteCiteprocPY, formatter.html)
    citacao = Citation([CitationItem(id)])
    bibliografia.register(citacao)

    pedacosCitacaoRef = []

    if (dadosABNT.get('autor') or dadosABNT.get('tituloCompleto') == None):
        if soup.find('div', class_='citacao-txt'):
            citacao_abnt = (soup.find('div', class_='citacao-txt')).get_text().strip()

        elif soup.find('p', class_='citation'):
            citacao_abnt = (soup.find('p', class_='citation')).get_text().strip()

    return bibliografia.cite(citacao, lambda x: None)



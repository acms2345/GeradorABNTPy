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

import unicodedata

def carregarJSONLD(jsonldsPuros):
    listaJSONLDs = []
    
    for scriptTag in jsonldsPuros:
        try:
            conversao = json.loads(scriptTag.string)
            listaJSONLDs.append(conversao)
        except (json.JSONDecodeError, TypeError):
            continue
    
    return listaJSONLDs


def obterTituloABNT(soup, dadosJSONSite):
    if dadosJSONSite:
        if dadosJSONSite.get('headline'):
            return dadosJSONSite.get('headline')
    if soup.find('h1'):
        return (soup.find('h1')).get_text()
    
    #Se tudo falhar...
    return (soup.title).get_text()

def obterAutorABNT(soup, dadosSite):
    """Essa função deve retornar o que o ibict-abnt.csl espera:
    
    - Para autores: family: sobrenome e given : restanteDoNome
    - Para organizações: literal: nome """
    autor = []

    tipo_autor = None
    
    if dadosSite:
    
        autorDados = dadosSite.get('author', {})
        
        if autorDados:
            if isinstance(autorDados, list):
                for autorIndividual in autorDados:
                    
                    nomeCompleto = autorIndividual.get('name')

                    if not nomeCompleto:
                        continue

                    if autorIndividual.get('@type') == 'Organization':
                        tipo_autor = 'Organization'

                        nomeCompleto = nomeCompleto.upper()

                        autor.append({'literal' : nomeCompleto})
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
                    autor.append({
                        'literal' : nomeCompleto
                    })
                else:
                    autorPartesNome = nomeCompleto.strip().split()
                    autorSobrenome = autorPartesNome[-1].upper()
                    autorNomeResto = " ".join(autorPartesNome[:-1])

                    autor.append({
                        'family' : autorSobrenome,
                        'given' : autorNomeResto
                    })
    if autor == []:
        metatagValido = False

        seletores_meta = [
        {'name': 'author'},
        {'property': 'article:author'}]

        for seletor in seletores_meta:
            metadadosAutor = soup.find('meta', attrs=seletor)
            if metadadosAutor and metadadosAutor.get('content'):
                nomeAutorTeste = metadadosAutor.get('content')
                if seletor == {'property': 'article:author'}:
                    if nomeAutorTeste.startswith(('http://', 'https://')):
                        continue
                # Se tem vírgula, pega só a primeira parte
                padrao_limpeza = r",\s*(do jornal|da redação|correspondente|colunista|enviado|especial|o|a)\b.*"
    
                # Substitui o padrão por nada e limpa espaços extras nas pontas
                nomeAutorTesteLimpo = re.sub(padrao_limpeza, "", nomeAutorTeste, flags=re.IGNORECASE).strip()

                nomeAutorTesteVerif = nomeAutorTesteLimpo.lower()
                nomeAutorTesteVerif = ''.join(c for c in unicodedata.normalize('NFD', nomeAutorTesteVerif)
                    if unicodedata.category(c) != 'Mn')
                
                blacklist_exata = {
                    'admin', 'administrator', 'root', 'system', 'sistema', 'webmaster', 'cms', 'wordpress', 'blogger',
                    'none', 'null', 'nil', 'na', 'not applicable', 'unknown', 'desconhecido', 'undefined', 'indefinido',
                    'teste', 'test', 'author', 'autor', 'editor', 'writer', 'staff', 'contributor', 'colaborador',
                    'anonymous', 'anon', 'anonimo', 'user', 'usuario', 'guest', 'visitante', 'convidado', 'profile', 'perfil',
                    'membro', 'member', 'site', 'website', 'homepage', 'web'
                }

                if nomeAutorTesteVerif in blacklist_exata: continue

                if len(nomeAutorTesteVerif) < 3 or not any(c.isalpha() for c in nomeAutorTesteVerif):
                    continue
                termos_parciais = [
                    r'\bequipe\b', r'\bsuporte\b', r'\batendimento\b', r'\bredacao\b', 
                    r'\breporter\b', r'\breportagem\b', r'\bjornalismo\b', r'\bcomunicacao\b', 
                    r'\bconteudo\b', r'\bagencia\b'
                ]
                
                # Compila os termos em uma única expressão regular separada por "OU" (|)
                regex_parcial = re.compile('|'.join(termos_parciais))
                
                if regex_parcial.search(nomeAutorTesteVerif):
                    continue
                
                
                autorPartesNome = nomeAutorTesteLimpo.split()
                autorSobrenome = autorPartesNome[-1].upper()
                autorNomeResto = " ".join(autorPartesNome[:-1])

                autor.append({
                    'family' : autorSobrenome,
                    'given' : autorNomeResto
                })

    return autor

        
def obterNomeSiteABNT(soup, dadosJSONSite):
    if dadosJSONSite:
        nomeSiteDados = dadosJSONSite.get('publisher', {})
        if nomeSiteDados:
            return nomeSiteDados.get('name')
        elif dadosJSONSite.get('name'):
            return dadosJSONSite.get('name')
    
    meta_site = soup.find("meta", property="og:site_name")

    if meta_site:
        nome_site = meta_site.get("content")
        return nome_site
    
def obterAnoPublicacao(dadosJSONSite, soup):
    if dadosJSONSite:
        dataPublicacao = dadosJSONSite.get('datePublished')
        if dataPublicacao:
            if isinstance(dataPublicacao, (int, float)):
                return int(dataPublicacao)
            elif isinstance(dataPublicacao, str):
                verificacao = re.search(r'\d{4}', dataPublicacao)
                if verificacao:
                    return int(verificacao.group(0))
                try:
                    return datetime.fromisoformat(dataPublicacao).year
                except:
                    pass

    #Se a verificação do JSON-LD falhar... Observa-se os metadados.
    meta_site = soup.find("meta", property="article:published_time")

    if meta_site:
        anoPublicacao = meta_site.get("content")
        if isinstance(anoPublicacao, (int, float)):
            return int(anoPublicacao)  
        elif isinstance(anoPublicacao, str):
            verificacao = re.search(r'\d{4}', anoPublicacao)
            if verificacao:
                return int(verificacao.group(0))
            else:
                try:
                    return datetime.fromisoformat(anoPublicacao).year
                except:
                    pass  
        
    #Se tudo falhar...
    return None


def obterDadosABNT(soup, urlSite):
    """
    São coletadas as seguintes informações:
    autor, tipo_autor, tituloCompleto, data_publicacao, data_acesso e url.
    
    Esses são retornados em um dicionário

    Primeiro, é feita a análise para saber se o site possui um JSON-LD, 
    arquivo de indexação que pode servir como base de obtenção.
    Se tiver, coleta-se as informações com base nele.

    Senão, há o fallback individual para cada informação.
    """

    #Essa é a estrutura a ser seguida
    autor = []
    tipo_autor = None
    tituloCompleto= None
    nomeSite = None
    anoPublicacao = None
    

    dadosSite = None

    JSONLD = soup.find_all('script', type='application/ld+json')

    if JSONLD:
        for dadosSiteTeste in carregarJSONLD(JSONLD):
            try:
                if dadosSiteTeste.get('author', {}) or dadosSiteTeste.get('headline'): 
                    dadosSite = dadosSiteTeste
                    break
                

            except AttributeError:
                
                if isinstance(dadosSiteTeste, list):
                    for dadosTesteIndividual in dadosSiteTeste:
                        if dadosTesteIndividual.get('author') or dadosTesteIndividual.get('headline'):
                            dadosSite = dadosTesteIndividual
                            break
            

    tituloCompleto = obterTituloABNT(soup, dadosSite)
    nomeSite = obterNomeSiteABNT(soup, dadosSite)
    anoPublicacao = obterAnoPublicacao(dadosSite, soup)
    autor = obterAutorABNT(soup, dadosSite)
        
    dataAcessoInfo = date.today()        
        
    
    if anoPublicacao == None:
        return {
            "author" : autor,
            "title" : tituloCompleto, 
            "accessed" : {"date-parts": [[dataAcessoInfo.year, dataAcessoInfo.month, dataAcessoInfo.day]]}, 
            "URL" : urlSite,
            "container-title" : nomeSite,
            "type" : "webpage",
            "id" : urlSite
        }
    else:
        return {
            "author" : autor, 
            "title" : tituloCompleto, 
            "issued" : {"date-parts" : [[anoPublicacao]]}, 
            "accessed" : {"date-parts": [[dataAcessoInfo.year, dataAcessoInfo.month, dataAcessoInfo.day]]}, 
            "URL" : urlSite,
            "container-title" : nomeSite,
            "type" : "webpage",
            "id" : urlSite
        }

bibliografiasPorPasta = {}  

def criarBibliografia(dados_json, idBibliografia):
    """Inicializa a fonte de dados e o motor do CSL."""
    fonte = CiteProcJSON(dados_json)
    estilo = CitationStylesStyle('ibict-abnt.csl', locale='pt-BR', validate=False)
    # Usamos plain para texto puro ou html para manter itálicos/negritos
    bibliografia = CitationStylesBibliography(estilo, fonte, formatter.plain)
    bibliografiasPorPasta[idBibliografia] = bibliografia
    return bibliografia


def citacaoInLine(soup, url, pasta):
    dadosABNT = obterDadosABNT(soup, url)

    try:

        id = dadosABNT.get('id')

        dadosBibliograficos = [dadosABNT]

        try:
            bibliografia = bibliografiasPorPasta[pasta]
        except KeyError:
            bibliografia = criarBibliografia(dadosBibliograficos, pasta)

        #print("DEBUG dadosBibliograficos:", json.dumps(dadosBibliograficos, ensure_ascii=False, indent=2))

        
        citacao = Citation([CitationItem(id)])
        bibliografia.register(citacao)

        return bibliografia.cite(citacao, lambda x: None)
    except Exception as excecao:
        return f"Erro ao construir a citação In Line: {excecao}"

        """pedacosCitacaoInLine = []

        pedacosCitacaoInLine.append('(')

        anoPublicacao = dadosABNT.get('issued')
        autor = dadosABNT.get('author')
        
        if isinstance(autor, list):
            if len(autor) > 3:
                texto = f"{autor[0].get('family')} et al., "
                pedacosCitacaoInLine.append(texto)
            else:
                for i in range(2):
                    texto = f"{autor[i].get('family')}, "
                    pedacosCitacaoInLine.append(texto)

        else:
            sobrenome = autor.get('family')
            pedacosCitacaoInLine.append(f"{autor.get('family')}, ")

        pedacosCitacaoInLine.append(f"{anoPublicacao})")

        citacaoInLine = "".join(pedacosCitacaoInLine)

        return citacaoInLine"""


    

    
    

    
    

def citacaoRef(pasta, url):
    try:
        bibliografia = bibliografiasPorPasta[pasta]
        if bibliografia is None:
            return "Erro: Você precisa chamar citacaoInLine antes de gerar a referência."
        

        # 1. Encontra a posição (índice) que a chave ocupa dentro daquela bibliografia
        # O citeproc armazena a ordem em 'keys' dentro do objeto do estilo
        indice_no_estilo = bibliografia.keys.index(url)
        
        
        if indice_no_estilo is not None:
            # 2. Renderiza a lista da bibliografia e extrai exatamente o item daquele índice
            lista_formatada = bibliografia.bibliography()
            
            return str(lista_formatada[indice_no_estilo])

    except Exception as excecao:
        return f"Erro ao criar a referência bibliográfica: {excecao}"
    

    """if (dadosABNT.get('author') or dadosABNT.get('title') == None):
        if soup.find('div', class_='citacao-txt'):
            citacao_abnt = (soup.find('div', class_='citacao-txt')).get_text().strip()

        elif soup.find('p', class_='citation'):
            citacao_abnt = (soup.find('p', class_='citation')).get_text().strip()

    if citacao_abnt:
        return citacao_abnt"""
    
    return "Nenhuma referência encontrada."
    


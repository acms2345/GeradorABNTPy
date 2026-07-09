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
    if dadosJSONSite.get('headline'):
        return dadosJSONSite.get('headline')
    elif soup.find('h1'):
        return soup.find('h1')
    else:
        return soup.title

def obterAutorABNT(soup, dadosSite):
    autor = []
    
    if dadosSite:
    
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
    else:
        metatagValido = False

        seletores_meta = [
        {'name': 'author'},
        {'property': 'article:author'}]

        for seletor in seletores_meta:
            metadadosAutor = soup.find('meta', attrs=seletor)
            if metadadosAutor and metadadosAutor.get('content'):
                nomeAutorTeste = metadadosAutor.get('content')
                if seletor == {'property': 'article:author'}:
                    padraoUrls = r"http*"
                    if re.search(nomeAutorTeste, padraoUrls):
                        pass
                nomeAutorTesteLimpo = nomeAutorTeste.strip().lower()
                nomeAutorTesteLimpo = ''.join(c for c in unicodedata.normalize('NFD', nomeAutorTesteLimpo)
                    if unicodedata.category(c) != 'Mn')
                
                blacklist_exata = {
                    'admin', 'administrator', 'root', 'system', 'sistema', 'webmaster', 'cms', 'wordpress', 'blogger',
                    'none', 'null', 'nil', 'na', 'not applicable', 'unknown', 'desconhecido', 'undefined', 'indefinido',
                    'teste', 'test', 'author', 'autor', 'editor', 'writer', 'staff', 'contributor', 'colaborador',
                    'anonymous', 'anon', 'anonimo', 'user', 'usuario', 'guest', 'visitante', 'convidado', 'profile', 'perfil',
                    'membro', 'member', 'site', 'website', 'homepage', 'web'
                }

                if nomeAutorTesteLimpo in blacklist_exata: pass

                if len(nomeAutorTesteLimpo) < 3 or not any(c.isalpha() for c in nomeAutorTesteLimpo):
                    pass
                termos_parciais = [
                    r'\bequipe\b', r'\bsuporte\b', r'\batendimento\b', r'\bredacao\b', 
                    r'\breporter\b', r'\breportagem\b', r'\bjornalismo\b', r'\bcomunicacao\b', 
                    r'\bconteudo\b', r'\bagencia\b'
                ]
                
                # Compila os termos em uma única expressão regular separada por "OU" (|)
                regex_parcial = re.compile('|'.join(termos_parciais))
                
                if regex_parcial.search(nomeAutorTesteLimpo):
                    pass
                
                autorPartesNome = nomeAutorTeste.strip().split()
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
    dataPublicacao = dadosJSONSite.get('datePublished')
    if dataPublicacao:
        if isinstance(dataPublicacao, (int, float)):
            return int(dataPublicacao)
        elif isinstance(dataPublicacao, str):
            verificacao = re.search(r'\d{4}', dataPublicacao)
            if verificacao:
                return int(verificacao.group(0))
            else:
                return datetime.fromisoformat(dataPublicacao).year
    else:
        meta_site = soup.find("meta", property="article:published_time")

        if meta_site:
            anoPublicacao = meta_site.get("content")
            return anoPublicacao
        else: 
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
        try:
            for dadosSiteTeste in carregarJSONLD(JSONLD):
                if(dadosSiteTeste.get('@type') in {'Article', 'NewsArticle', 'BlogPosting'} ): 
                    dadosSite = dadosSiteTeste
                    break
            if not dadosSite:
                raise ValueError("Nenhum JSON-LD compatível encontrado.")
            

        except Exception as e:
            dadosSite = None

    tituloCompleto = obterTituloABNT(dadosSite)
    nomeSite = obterNomeSiteABNT(soup, dadosSite)
    anoPublicacao = obterAnoPublicacao(dadosSite, soup)
    autor = obterAutorABNT(soup, dadosSite)
        
    dataAcessoInfo = date.today()

    meses = ['jan.', 'fev.', 'mar.', 'abr.', 'mai.', 'jun.', 'jul.', 'ago.', 'set.', 'out.', 'nov.', 'dez.']
    dataAcesso = f"{dataAcessoInfo.day} {meses[dataAcessoInfo.month - 1]} {dataAcessoInfo.year}"
        
        
    
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
    
def inicializar_citeproc(dados_json, caminho_csl):
    """Inicializa a fonte de dados e o motor do CSL."""
    fonte = CiteProcJSON(dados_json)
    estilo = CitationStylesStyle(caminho_csl, locale='pt-BR', validate=False)
    # Usamos plain para texto puro ou html para manter itálicos/negritos
    return CitationStylesBibliography(estilo, fonte, formatter.plain)

bibliografia = None #Será preenchido por citacaoInLine()

def citacaoInLine(soup, url):
    dadosABNT = obterDadosABNT(soup, url)

    try:

        id = dadosABNT.get('id')

        dadosBibliograficos = [dadosABNT]

        global bibliografia

        bibliografia = inicializar_citeproc(dadosBibliograficos, 'ibict-abnt.csl')

        #print("DEBUG dadosBibliograficos:", json.dumps(dadosBibliograficos, ensure_ascii=False, indent=2))

        
        citacao = Citation([CitationItem(id)])
        bibliografia.register(citacao)

        return bibliografia.cite(citacao, lambda x: None)
    except:

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

        return citacaoInLine


    

    
    

    
    

def citacaoRef(soup, url):
    dadosABNT = obterDadosABNT(soup, url)

    if bibliografia is None:
        return "Erro: Você precisa chamar citacaoInLine antes de gerar a referência."
    

    referencias = list(bibliografia.bibliography())
    
    if referencias:
        # Pega o primeiro item [0] e converte em texto puro
        return str(referencias[0])
    
    

    if (dadosABNT.get('autor') or dadosABNT.get('tituloCompleto') == None):
        if soup.find('div', class_='citacao-txt'):
            citacao_abnt = (soup.find('div', class_='citacao-txt')).get_text().strip()

        elif soup.find('p', class_='citation'):
            citacao_abnt = (soup.find('p', class_='citation')).get_text().strip()

    if citacao_abnt:
        return citacao_abnt
    
    return "Nenhuma referência encontrada."
    


import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup

import json
from datetime import date, datetime
import re

from citeproc import CitationStylesStyle, CitationStylesBibliography
from citeproc import formatter
from citeproc import Citation, CitationItem
from citeproc.source.json import CiteProcJSON

from importlib.resources import files

CAMINHO_CSL = files("geradorabnt").joinpath("ibict-abnt.csl")

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

def obterDOI(soup: BeautifulSoup, dadosJSONLDSite):
    def verificarDOIdeStr(texto):
        if not isinstance(texto, str):
            return None
        texto_limpo = texto.replace('https://doi.org/', '').replace('http://doi.org/', '').replace('doi.org/', '')
        match = PADRAO_DOI.search(texto_limpo)
        return match.group(0) if match else None

    
    if dadosJSONLDSite:
        PADRAO_DOI = re.compile(r'10\.\d{4,9}/[-._;()/:A-Za-z0-9]+')

        candidatos = [] #Possíveis campos para encontrar o DOI

        identifierMeta = dadosJSONLDSite.get('identifier')
        if isinstance(identifierMeta, dict):
            candidatos.append(identifierMeta.get('value'))
        elif isinstance(identifierMeta, str):
            candidatos.append(identifierMeta)

        if dadosJSONLDSite.get('@id'):
            candidatos.append(dadosJSONLDSite.get('@id'))
        if dadosJSONLDSite.get('sameAs'):
            candidatos.append(dadosJSONLDSite.get('sameAs'))

        for candidato in candidatos:
            verificacaoDOI = verificarDOIdeStr(candidato)
            if verificacaoDOI is not None:
                return verificacaoDOI 
    
    metadadoDOI = soup.find('meta', attrs={'name': 'citation_doi'})

    if metadadoDOI:
        return metadadoDOI.get('content')

    return None

def obterVolumeArtigo(soup: BeautifulSoup):
    metaCitVolume = soup.find('meta', attrs={'name': 'citation_volume'})
    if metaCitVolume is not None:
        return metaCitVolume.get('content')

    return None

def obterPublicadorArtigo(soup: BeautifulSoup):
    metaCitPublisher = soup.find('meta', attrs={'name': 'citation_publisher'})
    if metaCitPublisher:
        return metaCitPublisher.get('content')

    return None

from typing import Literal, TypeAlias

TipoCitacao: TypeAlias = Literal[
    "article-newspaper",
    "article-journal",
    "post-weblog",
    "thesis",
    "report",
    "webpage",
]
TIPOS_CITACAO = {
    "article-newspaper",
    "article-journal",
    "post-weblog",
    "thesis",
    "report",
    "webpage",
}

def obterTipoCitacao(dadosJSONSite, soup: BeautifulSoup, doiObtido: str | None=None, tipoSolicitado: TipoCitacao |None=None):
    '''Identifica o tipo de citação (para artigos, para sites, etc.) que deve ser usado
    para esse site.
    
    De acordo com os tipos declarados no CSL.'''

    if tipoSolicitado is not None:
        if tipoSolicitado in TIPOS_CITACAO:
            return tipoSolicitado

        print("Erro: o tipo de citação solicitado não será usado. Verifique erros de digitação.")

    MAPEAMENTOTIPOSCITACAO: dict[str, TipoCitacao] = {
        "NewsArticle": "article-newspaper",
        "ScholarlyArticle": "article-journal",
        "BlogPosting": "post-weblog"
    }
    if dadosJSONSite:
        if dadosJSONSite.get('@type'):
            tipoCitacaoDeclarado = dadosJSONSite.get('@type')
            if tipoCitacaoDeclarado in MAPEAMENTOTIPOSCITACAO:
                return MAPEAMENTOTIPOSCITACAO[tipoCitacaoDeclarado]

    metaCitDissert = soup.find('meta', attrs={'name': 'citation_dissertation_institution'})
    if metaCitDissert is not None:
        return "thesis"
    
    metaCitTechnReport = soup.find('meta', attrs={'name': 'citation_technical_report_institution'})
    if metaCitTechnReport is not None:
        return "report"
    
    if doiObtido is not None or soup.find('meta', attrs={'name': 'citation_journal_title'}):
        return "article-journal"
    

    return 'webpage' #Fallback padrão

def obterTituloABNT(soup: BeautifulSoup, dadosJSONSite):
    metaCitTitle = soup.find('meta', attrs={'name': 'citation_title'})
    if metaCitTitle:
        return metaCitTitle.get('content')
    if dadosJSONSite:
        if dadosJSONSite.get('name'):
            return dadosJSONSite.get('name')
        if dadosJSONSite.get('headline'):
            return dadosJSONSite.get('headline')
    if soup.find('h1'):
        return (soup.find('h1')).get_text()
    
    #Se tudo falhar...
    return (soup.title).get_text()

def obterAutorABNT(soup, dadosSite, nomeSite, urlSite):
    """Essa função deve retornar o que o ibict-abnt.csl espera:
    
    - Para autores: family: sobrenome e given : restanteDoNome
    - Para organizações: literal: nome """

    def repartirNomeAutor(
        nome: str | None = None,
        given_name: str | None = None,
        family_name: str | None = None,
        tipo: str | None = None,
    ) -> dict[str, str] | None:
        def limpar(valor: str | None) -> str:
            return valor.strip() if isinstance(valor, str) else ""

        nome = limpar(nome)
        given_name = limpar(given_name)
        family_name = limpar(family_name)
        tipo = limpar(tipo)

        if not nome and not given_name and not family_name:
            return None

        if tipo.lower() == "organization":
            valor_literal = nome or " ".join(
                parte for parte in (given_name, family_name) if parte
            )
            return {"literal": valor_literal.upper()}

        campos_separados_validos = (
            bool(given_name)
            and bool(family_name)
            and "," not in given_name
            and "," not in family_name
            and not (
                nome
                and " ".join((given_name, family_name)).casefold()
                == nome.casefold()
            )
        )

        if campos_separados_validos:
            return {
                "family": family_name.upper(),
                "given": given_name,
            }

        if not nome:
            nome = " ".join(
                parte for parte in (given_name, family_name) if parte
            )

        if not nome:
            return None

        if "," in nome:
            parte_sobrenome, parte_nome = nome.split(",", 1)

            parte_sobrenome = parte_sobrenome.strip()
            parte_nome = parte_nome.strip()

            if not parte_sobrenome or not parte_nome:
                return None

            # Exceção: "João Silva, Jr." não deve ser tratado como
            # "Sobrenome, Nome".
            if parte_nome.casefold() in {
                "jr",
                "jr.",
                "filho",
                "neto",
                "sobrinho",
            }:
                tokens = nome.split()
                if len(tokens) < 2:
                    return None

                return {
                    "family": tokens[-1].upper(),
                    "given": " ".join(tokens[:-1]),
                }

            return {
                "family": parte_sobrenome.upper(),
                "given": parte_nome,
            }

        tokens = nome.split()

        if len(tokens) == 1:
            return {"family": tokens[0].upper(), "given": ""}

        return {
            "family": tokens[-1].upper(),
            "given": " ".join(tokens[:-1]),
        }

    autor = []

    tipo_autor = None

        
    if dadosSite:
    
        autorDados = dadosSite.get('author', {})
        
        if autorDados:
            if isinstance(autorDados, list):
                for autorIndividual in autorDados:
                    
                    nomeCompleto = autorIndividual.get('name')
                    givenName = autorIndividual.get('givenName')
                    familyName = autorIndividual.get('familyName')

                    tipo_autor = autorIndividual.get('@type')

                    if nomeCompleto is not None and ((tipo_autor == 'Organization') or (nomeCompleto.strip().lower() == nomeSite.strip().lower())):
                        tipo_autor = 'Organization'

                        nomeCompleto = nomeCompleto.upper()

                        autor.append({'literal' : nomeCompleto})
                        continue

                
                
                    
                    # autorPartesNome = nomeCompleto.strip().split()
                    # autorSobrenome = autorPartesNome[-1].upper()
                    # autorNomeResto = " ".join(autorPartesNome[:-1])


                    # autor.append({
                    #     'family' : autorSobrenome,
                    #     'given' : autorNomeResto
                    # })
                    dictAutor = repartirNomeAutor(nomeCompleto, tipo=tipo_autor, given_name=givenName, family_name=familyName)

                    if dictAutor is not None: 
                        autor.append(dictAutor) 
                    else: continue
        
            if isinstance(autorDados, dict):
                tipo_autor = autorDados.get('@type')
                
                nomeCompleto = autorDados.get('name')
                givenName = autorDados.get('givenName')
                familyName = autorDados.get('familyName')

                if nomeCompleto:
                    
                    nomeSiteNorm = (nomeSite or '').strip().lower()
                    if tipo_autor == 'Organization' or (nomeSite is not None and nomeCompleto.strip().lower() == nomeSite.strip().lower()):
                        nomeCompleto = nomeCompleto.upper()
                        autor.append({
                            'literal' : nomeCompleto
                        })
                    elif nomeSiteNorm and nomeSiteNorm in nomeCompleto:
                        autor.append({
                            'literal' : nomeSite.upper()
                        })

                    # else:
                    #     autorPartesNome = nomeCompleto.strip().split()
                    #     autorSobrenome = autorPartesNome[-1].upper()
                    #     autorNomeResto = " ".join(autorPartesNome[:-1])

                    #     autor.append({
                    #         'family' : autorSobrenome,
                    #         'given' : autorNomeResto
                    #     })
                dictAutor = repartirNomeAutor(nomeCompleto, tipo=tipo_autor, given_name=givenName, family_name=familyName)
                
                if dictAutor is not None: 
                    autor.append(dictAutor)
                
    
    #Se, mesmo após a verificação do JSON-LD acima, os dados ainda não foram preenchidos...
    if autor == []:

        seletores_meta = [
        {'name': 'citation_author'},
        {'name': 'author'},
        {'property': 'article:author'}]

        for seletor in seletores_meta:
            # Conversão para lista, para verificar vários autores na mesma página
            if seletor == {'name': 'citation_author'}:
                metadadosAutores = soup.find_all('meta', attrs=seletor)
            else:
                metadado = soup.find('meta', attrs=seletor)
                metadadosAutores = [metadado] if metadado is not None else []
            for metadadosAutor in metadadosAutores:
                if not metadadosAutor or not metadadosAutor.get('content'):
                    continue

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
                
                
                dictAutor = repartirNomeAutor(nome=nomeAutorTesteLimpo)
                                
                if dictAutor is not None: 
                    autor.append(dictAutor)

    if autor == [] and nomeSite is not None:
        #A seguir: verificação de sites institucionais
        tlds_institucionais = [
            ".gov.br",
            ".gov",
            ".edu.br",
            ".edu",
            ".jus.br",
            ".leg.br",
        ]
        dominioURL = urlparse(url=urlSite).netloc.lower()

        if any(dominioURL.endswith(tld) for tld in tlds_institucionais):
            autor.append({'literal' : nomeSite})

            return autor

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
    
def obterAnoPublicacao(dadosJSONSite, soup: BeautifulSoup):
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

    metaDadosPossiveisData = [
        {'name': 'citation_publication_date'},
        {'name': 'citation_date'},
        {'property': 'article:published_time'},
    ]
    for metadado in metaDadosPossiveisData:
        meta_site = soup.find("meta", attrs=metadado)

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
        else: 
            continue
        
    #Se tudo falhar...
    return None


def obterDadosABNT(soup, urlSite, tipoCitacaoSolicitado: TipoCitacao | None=None):
    """
    A presente função coleta os dados necessários para criar a
    citação, conforme o solicitado no CSL.

    Os dados obtidos são:

        'author' : autor,
        'title' : tituloCompleto, 
        'accessed' : {a data de acesso - informações no modelo ano-mês-dia}, 
        'URL' : urlSite,
        'container-title' : nomeSite,
        'id' : urlSite,
        'type': tipoCitacao (como exatamente a citação deve ser organizada)

        'DOI',
        'publisher' : publicadorArtigo
    
    Esses são retornados em um dicionário 
    (para compatibilidade com o citeproc e o CSL).

    Primeiro, é feita a análise para saber se o site possui um JSON-LD, 
    arquivo de indexação de busca que pode servir como base de obtenção.
    Se tiver, coleta-se as informações com base nele.

    Senão, há o fallback individual para cada informação.
    """

    #Essa é a estrutura a ser seguida
    autor = []
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
            
            if dadosSite is not None: break

    doi = obterDOI(soup, dadosSite)  
    publicadorArtigo = obterPublicadorArtigo(soup)
    volumeArtigo = obterVolumeArtigo(soup)

    tipoCitacao = obterTipoCitacao(dadosSite, soup, doiObtido=doi, tipoSolicitado=tipoCitacaoSolicitado)
    tituloCompleto = obterTituloABNT(soup, dadosSite)
    nomeSite = obterNomeSiteABNT(soup, dadosSite)
    anoPublicacao = obterAnoPublicacao(dadosSite, soup)
    autor = obterAutorABNT(soup, dadosSite, nomeSite, urlSite)
        
    dataAcessoInfo = date.today()        

       
    #Montagem da lista para retorno

    dados = {
        "author" : autor,
        "title" : tituloCompleto, 
        "accessed" : {"date-parts": [[dataAcessoInfo.year, dataAcessoInfo.month, dataAcessoInfo.day]]}, 
        "URL" : urlSite,
        "publisher" : publicadorArtigo,
        "container-title" : nomeSite,
        "type" : tipoCitacao,
        "id" : urlSite.lower()
    }

    if anoPublicacao is not None:
        dados['issued'] = {"date-parts" : [[anoPublicacao]]}

    if doi is not None:
        dados["DOI"] = doi

    if volumeArtigo is not None:
        dados['volume'] = volumeArtigo

    return dados


bibliografiasPorPasta = {} 
dadosPorPasta = {} 

def criarBibliografia(dados_json, idBibliografia, formatador=formatter.plain):
    """Inicializa a fonte de dados e o motor do CSL.
    Ela recebe os dados JSON (obtidos em `obterDadosABNT()`), o ID de acesso à
    pasta da bibliografia em específico, e formatador (com o padrão sendo o `formatter.plain`,
    mas também aceita `formatter.html` e `formatter.rst`)."""


    fonte = CiteProcJSON(dados_json)
    estilo = CitationStylesStyle(CAMINHO_CSL, locale='pt-BR', validate=False)
    
    bibliografia = CitationStylesBibliography(estilo, fonte, formatador)
    bibliografiasPorPasta[idBibliografia] = bibliografia

    return bibliografia


def citacaoInLine(soup: BeautifulSoup, url: str, pasta: str, formatador=formatter.plain, tipoCitacao: TipoCitacao | None=None, debug: bool = False):
    dadosABNT = obterDadosABNT(soup, url, tipoCitacaoSolicitado=tipoCitacao)

    try:

        id = dadosABNT.get('id')

        citacao = Citation([CitationItem(id)])
        dadosBibliograficos = [dadosABNT]

        if pasta in dadosPorPasta:
            if dadosABNT in dadosPorPasta[pasta]:
                bibliografia = bibliografiasPorPasta[pasta]
            else:            
                dadosPorPasta[pasta].append(dadosABNT)

                dadosBibliograficos = dadosPorPasta[pasta]
                bibliografia = criarBibliografia(dadosBibliograficos, pasta, formatador)
                


        else:
            dadosPorPasta[pasta] = [dadosABNT]  # Cria a lista com o primeiro item
            bibliografia = criarBibliografia(dadosBibliograficos, pasta, formatador)

            
            bibliografia.register(citacao)

        

        try:
            bibliografia = bibliografiasPorPasta[pasta]
        except KeyError:
            bibliografia = criarBibliografia(dadosBibliograficos, pasta, formatador)

        if debug:
            print("DEBUG dadosBibliograficos:", json.dumps(dadosBibliograficos, ensure_ascii=False, indent=2))

        
        citacao = Citation([CitationItem(id)])
        bibliografia.register(citacao)

        return bibliografia.cite(citacao, lambda x: None)
    except Exception as excecao:
        raise excecao

    
    

def citacaoRef(pasta: str, url: str):
    """Retorna a referência bibliográfica do site.
    
    Por pormenores da biblioteca usada, ela SEMPRE deve ser usada DEPOIS da `citacaoInLine()`."""
    try:
        bibliografia = bibliografiasPorPasta[pasta]
        if bibliografia is None:
            return "Erro: Você precisa chamar citacaoInLine antes de gerar a referência."
        

        # 1. Encontra a posição (índice) que a chave ocupa dentro daquela bibliografia
        # O citeproc armazena a ordem em 'keys' dentro do objeto do estilo
        indice_no_estilo = bibliografia.keys.index(url.lower())
        #Obs.: foi descoberto em testes que o 'bibliografia.keys' só guarda as
        #coisas em minúsculo. Por isso, há o 'url.lower()'.
        
        
        if indice_no_estilo is not None:
            # 2. Renderiza a lista da bibliografia e extrai exatamente o item daquele índice
            lista_formatada = bibliografia.bibliography()
            
            return str(lista_formatada[indice_no_estilo])

    except Exception as excecao:
        raise excecao
    
    
    return "Nenhuma referência encontrada."

def limparPasta(pasta):
    dadosPorPasta.pop(pasta, None)
    bibliografiasPorPasta.pop(pasta, None)



# GeradorABNTPy
![Estatísticas de tempo do Hackatime](https://hackatime.hackclub.com/api/v1/badge/acms2345/acms2345/GeradorABNTPy)

Um sistema para criação de citações, no formato da Associação Brasileira de Normas Técnicas (ABNT), de sites. É obtida a URL, e com ela, o sistema entra no site, coleta os dados necessários e realiza a montagem da citação.
Ele foi feito para ser integrável com outros sistemas e softwares que utilizem a linguagem Python, podendo ser utilizado como biblioteca integrada.

Esse sistema está sendo feito com base na NBR 6023 (3ª edição).

## Sobre a estrutura

O sistema atualmente tem uma base mais apropriada para o uso de pastas (você pode, por exemplo, separar referências entre as "pastas" 'quimica' e 'biologia'), mas ainda não conta com um sistema de salvamento local dessas.
Os arquivos atuais são:
```text
GeradorABNTPy
├── pyproject.toml
├── README.md
├── LICENSE
├── play.py
├── .gitignore
└── geradorabnt/
    ├── __init__.py
    ├── core.py
    └── ibict-abnt.csl
```

> Está sendo usado o arquivo CSL (Citation Style Language) feito pelo Instituto Brasileiro de Informação em Ciência e Tecnologia (Ibict) para organizar a citação no formato ABNT; arquivo este que está sob a licença CC BY-SA 3.0 e que foi modificado em poucas linhas quanto a delimitadores de informação para garantir melhor estruturação da citação.
[Link para o estilo ABNT aqui](https://www.zotero.org/styles?q=id%3Ainstituto-brasileiro-de-informacao-em-ciencia-e-tecnologia-abnt).

- `ibict-abnt.csl`: O arquivo criado pelo Ibict, que foi mencionado anteriormente. 
- `geradorabnt/core.py`: O "coração" do sistema. Ele possui todas as funções necessárias para a extração web e a montagem das citações.
- `play.py`: Um código para testes e exemplificação de uso do arquivo.


### "Como usar o código?"

Após baixar o repositório, instale as dependências do código via PIP:

```bash
pip install .
```

O código está adaptado para ser usado anexado a outros códigos. Então, caso desejado, é possível coletar apenas a pasta `geradorabnt/` e importar para seu código:
```python
from geradorabnt import citacaoInLine, citacaoRef
```
Ou `limparPasta()`, a depender de sua demanda.
Recomendo conferir o exemplo de uso presente em `play.py`.
Ou, para aqueles que apenas querem testar a criação das referências, **há a demonstração online do código** em [https://acms2345.github.io/demos/geradorabnt](https://acms2345.github.io/demos/geradorabnt).

## Limitações conhecidas
- Alguns sites, como Gov.br, IBGE e outros não podem ser acessados pelo sistema por bloqueio de acesso de robôs.
- Atualmente, o algoritmo apenas faz o formato de referência para sites e posts online (HTML). Sites que geram seu HTML via JavaScript não podem ser lidos.

## Licença

Esse repositório está sob a licença MIT. Confira `LICENSE` para mais detalhes.
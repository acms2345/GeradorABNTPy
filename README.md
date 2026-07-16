# GeradorABNTPy
![Estatísticas de tempo do Hackatime](https://hackatime.hackclub.com/api/v1/badge/acms2345/acms2345/GeradorABNTPy)
Um sistema para verificação de site e obtenção da citação ABNT dele. 

Esse sistema está sendo feito com base na NBR 6023 (3ª edição).

Esse sistema está usando o CSL (Citation Style Language) feito pelo Instituto Brasileiro de Informação em Ciência e Tecnologia (Ibict) para gerar a citação no formato ABNT.
[Link para o estilo ABNT](https://www.zotero.org/styles?q=id%3Ainstituto-brasileiro-de-informacao-em-ciencia-e-tecnologia-abnt)

## Sobre a estrutura

O sistema atualmente tem uma base mais apropriada para o uso de pastas (você pode, por exemplo, separar referências entre as "pastas" 'quimica' e 'biologia'), mas ainda não conta com um sistema de salvamento local dessas.
Os arquivos atuais são:
- `ibict-abnt.csl`: O arquivo criado pelo Ibict, que foi mencionado anteriormente.
- `geradorabnt.py`: O "coração" do sistema. Ele possui todas as funções necessárias para a extração web e a montagem das citações.
- `play.py`: O exemplo de uso e obtenção das citações por meio do `geradorabnt.py`.

## Limitações conhecidas
- Alguns sites, como Gov.br, IBGE e outros não podem ser acessados pelo sistema por bloqueio de acesso de robôs.
- Atualmente, o algoritmo apenas faz o formato de referência para sites e posts online.

## Licença

Esse repositório está sob a licença MIT. Confira `LICENSE` para mais detalhes.
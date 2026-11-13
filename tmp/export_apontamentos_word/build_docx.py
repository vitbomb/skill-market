# -*- coding: utf-8 -*-
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from xml.sax.saxutils import escape
import xml.etree.ElementTree as ET
import json

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "Apontamentos_Revisao_SkillMarket.docx"
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL = "http://schemas.openxmlformats.org/package/2006/relationships"
parts = []
links = []
sources = [
("Casalhay, Guevarra e Bragas (2025) — artigo completo",
 "https://ijrpr.com/uploads/V6ISSUE5/IJRPR45037.pdf"),
("TIC Domicílios 2020 — resumo executivo",
 "https://cetic.br/media/docs/publicacoes/2/20211124201505/resumo_executivo_tic_domicilios_2020.pdf"),
("TIC Domicílios 2025 — principais resultados e série histórica",
 "https://cetic.br/media/analises/tic_domicilios_2025_principais_resultados.pdf"),
("IBGE — notícia reproduzida pela Agência Gov, 17/10/2025",
 "https://agenciagov.ebc.com.br/noticias/202510/numero-de-trabalhadores-por-aplicativos-cresceu-25-4-entre-2022-e-2024"),
("Wood et al. (2019) — Good Gig, Bad Gig; repositório de Oxford",
 "https://ora.ox.ac.uk/objects/uuid%3A7cc5dd8e-75a8-4af5-86ab-6ed6bd615e72/files/mb56c2ca520db5c9bae17c932be64fda1"),
("Garcia-Parpet e Bevilaqua (2020) — texto completo",
 "https://acervodigital.sistemaindustria.com.br/bitstream/uniepro/281/1/GarciaParpetBevilaqua_NovaEconDig_EstudosProsp_v1n1set20.pdf"),
("Sousa (2024) — histórico da Economia Gig, Migalhas",
 "https://www.migalhas.com.br/depeso/406072/gig-economy-e-protecao-ao-trabalhador-rumo-a-um-marco-regulatorio"),
("Upwork — comissão do profissional",
 "https://support.upwork.com/hc/en-us/articles/211062538-Learn-about-the-Freelancer-Service-Fee"),
("Fiverr — página de ganhos do profissional",
 "https://help.fiverr.com/hc/en-us/articles/9234443621137-Your-earnings-page"),
("99Freelas — funcionamento, taxas e planos",
 "https://www.99freelas.com.br/como-funciona"),
("Google AdSense — cálculo do RPM",
 "https://support.google.com/adsense/answer/190515?hl=pt-BR"),
("Vercel — diretrizes de uso e restrições comerciais",
 "https://vercel.com/docs/limits/fair-use-guidelines"),
("Vercel — preços",
 "https://vercel.com/pricing"),
("Render — plano gratuito",
 "https://render.com/docs/free"),
("Render — preços",
 "https://render.com/pricing"),
("Brevo — planos e preços",
 "https://help.brevo.com/hc/en-us/articles/208589409-About-Brevo-s-pricing-plans"),
("Neon — planos e preços",
 "https://neon.com/pricing")
]
def run(text, bold=False, color=None, size=None):
    pr = ('<w:b/>' if bold else '') + (f'<w:color w:val="{color}"/>' if color else '') + (f'<w:sz w:val="{size}"/>' if size else '')
    return f'<w:r><w:rPr>{pr}</w:rPr><w:t xml:space="preserve">{escape(text)}</w:t></w:r>'
def p(text="", style="Normal", bold=False, keep=False):
    props = f'<w:pStyle w:val="{style}"/>' + ('<w:keepNext/>' if keep else '')
    parts.append(f'<w:p><w:pPr>{props}</w:pPr>{run(text,bold)}</w:p>')
def h(text):
    p(text,"Heading1",keep=True)
def sub(text):
    p(text,"Heading2",keep=True)
def bullet(text):
    p("•  " + text,"Bullet")
def action(text):
    p("O que fazer: " + text,"Action")
def source(ids):
    content = run("Fontes: ","Italic")
    for j, num in enumerate(ids):
        label,url=sources[num-1]
        rid="rIdLink"+str(len(links)+1)
        links.append((rid,url))
        if j: content += run("  •  ")
        content += f'<w:hyperlink r:id="{rid}">{run("["+str(num)+"]","", "008287")}</w:hyperlink>'
    parts.append('<w:p><w:pPr><w:pStyle w:val="Source"/></w:pPr>'+content+'</w:p>')
def linkpara(num,label,url):
    rid="rIdLink"+str(len(links)+1); links.append((rid,url))
    parts.append('<w:p><w:pPr><w:pStyle w:val="Reference"/></w:pPr>'+run(f"[{num:02d}]  ",True)+f'<w:hyperlink r:id="{rid}">{run(label,False,"008287")}</w:hyperlink></w:p>')
def page():
    parts.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')
def table(headers, rows, widths):
    grid=''.join(f'<w:gridCol w:w="{v}"/>' for v in widths)
    data=[]
    for idx,row in enumerate([headers]+rows):
        cells=[]
        for ci,txt in enumerate(row):
            bg="143D59" if idx==0 else ("EFF5F8" if idx%2 else "FFFFFF")
            color="FFFFFF" if idx==0 else "243746"
            paras=[]
            for line in txt.split("\n"):
                paras.append('<w:p><w:pPr><w:pStyle w:val="TableText"/></w:pPr>'+run(line,idx==0,color,18)+'</w:p>')
            cells.append(f'<w:tc><w:tcPr><w:tcW w:w="{widths[ci]}" w:type="dxa"/><w:shd w:fill="{bg}"/><w:vAlign w:val="center"/></w:tcPr>{"".join(paras)}</w:tc>')
        data.append('<w:tr><w:trPr><w:cantSplit/>'+('<w:tblHeader/>' if idx==0 else '')+'</w:trPr>'+''.join(cells)+'</w:tr>')
    parts.append('<w:tbl><w:tblPr><w:tblW w:w="0" w:type="auto"/><w:tblLayout w:type="fixed"/><w:tblBorders><w:top w:val="single" w:sz="4" w:color="D8E3E9"/><w:bottom w:val="single" w:sz="4" w:color="D8E3E9"/><w:insideH w:val="single" w:sz="4" w:color="D8E3E9"/></w:tblBorders><w:tblCellMar><w:top w:w="90" w:type="dxa"/><w:left w:w="100" w:type="dxa"/><w:bottom w:w="90" w:type="dxa"/><w:right w:w="100" w:type="dxa"/></w:tblCellMar></w:tblPr><w:tblGrid>'+grid+'</w:tblGrid>'+''.join(data)+'</w:tbl>')
    p()

# PAGE 1
p("APONTAMENTOS DE REVISÃO","Eyebrow")
p("SkillMarket","Title")
p("Citações, evidências e coerência do artigo","Subtitle")
p("Versão analisada: arquivo “(13)”, com 51 páginas  |  Revisão de 13/11/2026","Meta")
sub("Escopo e parecer")
p("A revisão abrangeu o texto das 51 páginas e a comparação dos principais trechos da fundamentação com fontes disponíveis. Algumas descrições técnicas também foram confrontadas com o código local do projeto.")
p("Os problemas identificados concentram-se na precisão das citações, na interpretação de fontes e na coerência entre as seções. O percentual de 34% apresentado pelo detector não permite concluir a autoria dos trechos.")
p("Os RF e RNF foram considerados de autoria da equipe, conforme informação do autor, e não foram destacados como suspeita de plágio.")
p("Limite da análise: não foram recebidas as correspondências detalhadas do JustDone e não houve acesso às bases privadas desses serviços. Esta revisão não certifica a originalidade integral do documento.","Note")
h("1. Citação de Casalhay usada fora do contexto")
p("Localização: página 4 do PFC.","Location")
p("A fala sobre aplicativos que exigem assinaturas e atualizações foi utilizada para sustentar a discussão sobre custos de plataformas de freelancers. Na fonte original, porém, ela integra a discussão sobre produtos e ferramentas financeiras, como aplicativos de gestão financeira, impostos e poupança. Não se trata de uma reclamação identificada especificamente com Fiverr ou Upwork. A passagem está na página 3555 da publicação.")
action("Retirar a fala desse argumento ou empregá-la no contexto financeiro correto. Para demonstrar cobranças de plataformas de contratação, utilizar suas páginas oficiais. Trata-se de adequação da evidência ao argumento, não de constatação de plágio.")
source([1])
h("2. Confusão entre pessoas e domicílios")
p("Localização: página 7 do PFC.","Location")
p("Os percentuais de 53% e 70% referem-se à proporção de usuários de internet na população rural, e não à proporção de domicílios rurais conectados. Os valores nacionais de 67% dos domicílios em 2018 e 86% em 2025 encontram respaldo na série oficial.")
action("Corrigir o indicador rural e conferir se texto, título e legenda dos gráficos usam a mesma população de referência. Acrescentar observação sobre a metodologia adaptada da edição de 2020 ao interpretar o salto durante a pandemia.")
source([2,3])

# PAGE 2
page()
h("3. Delimitação dos dados do IBGE")
p("Localização: páginas 6, 17 e 18 do PFC.","Location")
p("Os números de 294 mil trabalhadores e 17,8% correspondem à categoria de aplicativos de prestação de serviços gerais ou profissionais. Essa categoria não equivale automaticamente a profissionais de tecnologia que trabalham integralmente pela internet.")
p("O indicador de 6,1% classificados como empregadores descreve a posição na ocupação dos próprios trabalhadores plataformizados. Ele não mede o percentual de clientes ou empresas que contratam freelancers.")
action("Apresentar os 294 mil como contextualização de uma categoria mais ampla e retirar o uso dos 6,1% como evidência sobre o lado contratante.")
source([4])
h("4. Interpretação do controle taylorista")
p("Localização: páginas 13–15 do PFC.","Location")
p("O texto associa a redução da autonomia ao crescimento do controle taylorista e apresenta vigilância e precariedade contratual como duas vias principais da fragmentação. Wood et al., entretanto, destacam limitações da supervisão direta e consideram o controle algorítmico por avaliações e reputação mais eficaz no contexto pesquisado.")
action("Distinguir monitoramento direto, avaliações algorítmicas e insegurança contratual. Evitar apresentar uma interpretação da equipe como conclusão expressa dos pesquisadores.")
source([5])
h("5. Revisão das citações diretas")
p("As falas localizadas nas fontes não parecem inventadas. Os ajustes necessários dizem respeito à contextualização, à indicação de página, às traduções e à atribuição.")
table(["Página","Situação","Ajuste recomendado"],[
["4","Fala de Casalhay sobre assinaturas","Corrigir o contexto; indicar página e tradução."],
["9","Relações de mercado e regulamentações fracas","Conferir a atribuição: Wood reproduz formulação de Kalleberg."],
["12","Definição de worker power","Explicitar a consulta indireta a Kalleberg, caso o acesso tenha ocorrido por Wood."],
["13","Fala de Joseph","Manter a página 68 e padronizar a indicação de tradução."],
["14","Falas dos entrevistados de Casalhay","Acrescentar página e indicação de tradução."],
["15","Fala do trabalhador sul-africano","Acrescentar página e indicação de tradução."],
["17","Fala de Garcia-Parpet e Bevilaqua","Conferir página e marcar a inserção explicativa da equipe."]
],[700,3200,5738])

# PAGE 3
page()
sub("Cuidados complementares com a atribuição")
p("As duas definições apresentadas por meio de Wood aparecem no original atribuídas a Kalleberg. Deve-se indicar com transparência a fonte efetivamente consultada, seguindo o manual da instituição, sem simular leitura do livro original.")
p("Na página 17, a explicação inserida entre parênteses na frase de Garcia-Parpet e Bevilaqua não integra literalmente a formulação original. Usar a convenção de intervenção do autor adotada pela instituição.")
p("O diagnóstico de escassez de pesquisas, publicado em 2020, deve ser situado naquele período. Ele não demonstra sozinho a situação de 2026.")
source([5,6])
h("6. Paráfrases próximas da organização das fontes")
p("Localização: página 8 e páginas 15–16 do PFC.","Location")
bullet("Página 8: a sequência histórica — anos 1990, anos 2000 e década de 2010 — acompanha de perto a apresentação de Sousa. A fonte está citada, mas cabe sintetizar melhor o que interessa ao projeto. Corrigir “Enlace” para “Elance”. A expressão “elaboração oficial” da Economia Gig não é sustentada pela passagem consultada.")
bullet("Páginas 15–16: os argumentos sobre propostas, excesso de trabalhadores, conectividade e medo de substituição acompanham a sequência de Wood. A atribuição existente impede classificar automaticamente esse padrão como plágio, mas recomenda-se maior síntese e análise própria.")
action("Reorganizar a explicação a partir do argumento da equipe e explicitar a relação com o SkillMarket. A simples troca de palavras por sinônimos, preservando toda a estrutura, não amplia a contribuição autoral.")
source([5,7])
h("7. Alcance da justificativa e modelos de cobrança")
p("Localização principal: página 4 do PFC.","Location")
p("A afirmação de que faltam plataformas específicas para esses profissionais, associando as existentes ao segundo grupo da Economia Gig, é difícil de sustentar diante da própria discussão sobre Fiverr, Upwork e 99Freelas.")
p("Uma justificativa mais defensável é demonstrar limitações dos modelos de cobrança e oportunidades para outra forma de apresentação e contato, em vez de afirmar uma ausência geral de plataformas.")
bullet("Upwork: informa comissão de 0% a 15% por contrato.")
bullet("Fiverr: informa que o profissional recebe 80% do valor do pedido.")
bullet("99Freelas: informa cadastro gratuito, planos opcionais e taxa adicionada à oferta, paga pelo contratante. Evitar afirmar que toda cobrança reduz diretamente o recebimento do profissional.")
action("Distinguir cadastro gratuito, assinatura opcional, compra de recursos e comissão sobre serviços.")
source([8,9,10])

# PAGE 4
page()
h("8. Alinhamento entre resumo, resultados e conclusão")
p("Localização: páginas 1, 37–38, 45 e 46 do PFC.","Location")
p("No resumo, chamar a ferramenta de “viável e inclusiva”, associando-a ao aumento da visibilidade e do volume de negócios, ultrapassa o que foi demonstrado. Nas páginas 37–38, o artigo reconhece que não acompanhou aumento de visibilidade ou contratação. Na página 45, reconhece que a sustentabilidade financeira não foi comprovada.")
action("Levar essas delimitações também ao resumo e separar a implementação das funcionalidades dos efeitos ainda não medidos.")
p("As considerações finais da página 46 continuam insuficientes: retomam a finalidade e mencionam continuidade, mas sintetizam pouco os resultados apresentados.")
bullet("Informar quais funcionalidades foram efetivamente desenvolvidas.")
bullet("Distinguir entrega técnica de impacto ainda não medido.")
bullet("Retomar as principais limitações.")
bullet("Apresentar próximos passos específicos, vinculados às limitações.")
p("No último objetivo do Quadro 01, a gratuidade demonstra uma diferença de custo, mas não comprova diferenciação do modelo de apresentação de portfólio.")
h("9. Atualização da descrição técnica")
p("Base da conferência: código local do projeto, consultado em 13/11/2026.","Location")
table(["Local","Descrição no artigo","Situação encontrada no código local"],[
["p. 25","Express 5.3.0","O package-lock.json registra 5.2.1."],
["pp. 26 e 34–35","Testes restritos à criptografia","Há também testes de autenticação, acesso a perfis e tamanho mínimo das senhas."],
["p. 35","Chave JWT padrão ainda pendente","O servidor já rejeita o valor antigo, a ausência e o segredo curto."],
["p. 35","Gravação de perfil ainda sem vinculação","A gravação já utiliza o usuário autenticado."],
["pp. 33 e 35","Consulta individual ainda sem restrição","Perfis não aprovados já são restritos ao proprietário ou administrador."]
],[900,3400,5338])
p("A suíte existente foi executada na revisão: 15 testes passaram, sem falhas. Isso sustenta atualizar a descrição da cobertura, mas não afirmar que todos os fluxos foram testados ou que houve avaliação em produção.")
p("Ainda há pendências, como a atualização da intenção sem autenticação naquela rota. Atualizar as limitações por item, sem excluir o parágrafo inteiro. O chat consulta mensagens a cada três segundos; explicitar a atualização periódica é mais preciso que sugerir comunicação instantânea.")
p("Não foi confirmado que a implantação pública contém exatamente a versão local conferida.","Note")

# PAGE 5
page()
h("10. Fontes dos quadros e viabilidade financeira")
p("Localização: quadros comparativos e páginas 43–45 do PFC.","Location")
p("No quadro sobre Fiverr, Upwork e 99Freelas, “Fonte: Autoria própria” não explica a procedência dos dados externos. A equipe elaborou a comparação, mas informações de preços e funcionalidades vêm das plataformas.")
p("Faltam referências específicas das páginas de preços da Vercel, Render, Brevo e Neon. A referência da API da Brevo não substitui sua página de preços. O Google AdSense também é mencionado sem entrada correspondente na lista final.")
p("A explicação do RPM está coerente com a documentação consultada. Os totais de US$ 27,00 e US$ 64,95 estão aritmeticamente corretos diante dos valores adotados no texto.")
p("A conclusão da página 44 deve ser ajustada: público maior, por si só, não obriga a contratar todos os serviços pagos. Isso depende do consumo e das condições dos fornecedores. Na Vercel, a monetização por anúncios constitui uma restrição específica do Hobby.")
action("Identificar as fontes externas dos quadros, incluir as referências utilizadas e condicionar a necessidade de contratação ao consumo e às regras de cada fornecedor.")
source([8,9,10,11,12,13,14,15,16,17])
h("11. Correções editoriais")
table(["Página","Problema","Correção recomendada"],[
["5","Recorte anunciado de 2019–2026, mas uso de Green (2018)","Ajustar a delimitação ou explicitar a exceção."],
["19","“Kang et al.”","Padronizar com “Khang”."],
["19","“a aprimoração”","Usar “o aprimoramento”."],
["31","“OWASP, [20--]”","Identificar a referência com a letra correspondente."],
["34","“recentes.Periodicamente”","Inserir espaço."],
["41","“contratanto”","Corrigir para “contratante”."],
["43","Infraestrutura identificada como “Quadro 02”","Corrigir para “Quadro 03”, conforme as chamadas."],
["44","“Bravo”","Corrigir para “Brevo”."],
["Referências","Casalhay com link da página inicial da revista","Usar o endereço direto do artigo ou DOI."],
["Referências","Garcia-Parpet e Bevilaqua com páginas 103–128","Conferir a paginação: o arquivo vinculado inclui páginas numeradas além desse intervalo, inclusive 148–150."]
],[1000,4000,4638])
source([1,6])

# PAGE 6
page()
h("Escrita e interpretação do detector")
p("Expressões como “nesse contexto”, “dessa maneira” e “conforme apresentado” não permitem determinar autoria. Há repetições de apresentações de seção e transições que podem ser reduzidas para tornar o artigo mais direto. A melhoria relevante é aumentar a precisão e a análise própria, e não perseguir uma porcentagem do detector.")
sub("Ordem sugerida de correção")
p("Priorizar a citação de Casalhay, os indicadores de internet e IBGE, a atualização técnica e as considerações finais. Em seguida, revisar citações diretas, referências dos quadros e correções editoriais.")
h("Fontes vinculadas aos apontamentos")
p("Links consultados na revisão de 13/11/2026. A numeração corresponde às chamadas ao longo deste documento. Este elenco identifica as fontes dos apontamentos; não substitui a revisão da lista bibliográfica do PFC.","Meta")
for n,(label,url) in enumerate(sources,1):
    linkpara(n,label,url)
p("Documento de apoio à revisão do artigo. As localizações referem-se à versão “(13)” analisada, não à paginação deste arquivo Word.","Note")

styles = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="{W}">
<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:sz w:val="21"/><w:color w:val="243746"/><w:lang w:val="pt-BR"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:after="110" w:line="255" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:pPr><w:widowControl/></w:pPr></w:style>
<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:spacing w:before="0" w:after="80"/></w:pPr><w:rPr><w:b/><w:sz w:val="48"/><w:color w:val="143D59"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Subtitle"><w:name w:val="Subtitle"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:spacing w:after="140"/></w:pPr><w:rPr><w:sz w:val="25"/><w:color w:val="526A79"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Eyebrow"><w:name w:val="Eyebrow"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:spacing w:after="100"/></w:pPr><w:rPr><w:b/><w:sz w:val="18"/><w:color w:val="008287"/><w:spacing w:val="20"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="Heading 1"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:keepLines/><w:spacing w:before="200" w:after="110"/><w:outlineLvl w:val="0"/></w:pPr><w:rPr><w:b/><w:sz w:val="28"/><w:color w:val="143D59"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="Heading 2"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:spacing w:before="130" w:after="100"/><w:outlineLvl w:val="1"/></w:pPr><w:rPr><w:b/><w:sz w:val="23"/><w:color w:val="143D59"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Meta"><w:name w:val="Meta"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:after="150"/></w:pPr><w:rPr><w:sz w:val="18"/><w:color w:val="627887"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Location"><w:name w:val="Location"/><w:basedOn w:val="Normal"/><w:pPr><w:keepNext/><w:spacing w:after="90"/></w:pPr><w:rPr><w:b/><w:sz w:val="19"/><w:color w:val="627887"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Action"><w:name w:val="Action"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:before="60" w:after="100"/><w:pBdr><w:left w:val="single" w:sz="14" w:space="8" w:color="008287"/></w:pBdr><w:ind w:left="160"/></w:pPr></w:style>
<w:style w:type="paragraph" w:styleId="Note"><w:name w:val="Note"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:before="90" w:after="110"/></w:pPr><w:rPr><w:i/><w:sz w:val="18"/><w:color w:val="627887"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Source"><w:name w:val="Source"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:after="100"/></w:pPr><w:rPr><w:sz w:val="18"/><w:color w:val="008287"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Reference"><w:name w:val="Reference"/><w:basedOn w:val="Normal"/><w:pPr><w:keepLines/><w:spacing w:after="95"/><w:ind w:left="420" w:hanging="420"/></w:pPr><w:rPr><w:sz w:val="19"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Bullet"><w:name w:val="Bullet"/><w:basedOn w:val="Normal"/><w:pPr><w:ind w:left="220" w:hanging="220"/><w:spacing w:after="75"/></w:pPr></w:style>
<w:style w:type="paragraph" w:styleId="TableText"><w:name w:val="Table Text"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:before="0" w:after="20" w:line="220" w:lineRule="auto"/></w:pPr><w:rPr><w:sz w:val="18"/></w:rPr></w:style>
</w:styles>'''
sect = '<w:sectPr><w:headerReference w:type="default" r:id="rIdHeader"/><w:footerReference w:type="default" r:id="rIdFooter"/><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1050" w:right="1134" w:bottom="1050" w:left="1134" w:header="450" w:footer="450"/></w:sectPr>'
doc=f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="{W}" xmlns:r="{R}"><w:body>{"".join(parts)}{sect}</w:body></w:document>'
rels=f'<Relationships xmlns="{REL}"><Relationship Id="rIdStyles" Type="{R}/styles" Target="styles.xml"/><Relationship Id="rIdHeader" Type="{R}/header" Target="header1.xml"/><Relationship Id="rIdFooter" Type="{R}/footer" Target="footer1.xml"/><Relationship Id="rIdSettings" Type="{R}/settings" Target="settings.xml"/>'
for rid,url in links:
    rels+=f'<Relationship Id="{rid}" Type="{R}/hyperlink" Target="{escape(url, {chr(34):"&quot;"})}" TargetMode="External"/>'
rels+='</Relationships>'
header=f'<w:hdr xmlns:w="{W}"><w:p><w:pPr><w:pBdr><w:bottom w:val="single" w:sz="5" w:space="5" w:color="D8E3E9"/></w:pBdr></w:pPr>{run("SKILLMARKET  |  REVISÃO DO ARTIGO",True,"627887",16)}</w:p></w:hdr>'
footer=f'<w:ftr xmlns:w="{W}"><w:p><w:pPr><w:jc w:val="right"/></w:pPr>{run("Apontamentos • 13/11/2026    |    ",False,"627887",16)}<w:fldSimple w:instr="PAGE">{run("1",False,"627887",16)}</w:fldSimple></w:p></w:ftr>'
ct='''<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/><Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/><Override PartName="/word/header1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/><Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/><Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/></Types>'''
core='''<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><dc:title>Apontamentos de Revisão — SkillMarket</dc:title><dc:subject>Revisão de citações, evidências e coerência do artigo</dc:subject><dc:creator>ChatGPT</dc:creator><dc:description>Apontamentos referentes ao artigo versão (13), analisado em 13/11/2026.</dc:description></cp:coreProperties>'''
files={
'[Content_Types].xml':ct,
'_rels/.rels':f'<Relationships xmlns="{REL}"><Relationship Id="rId1" Type="{R}/officeDocument" Target="word/document.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/></Relationships>',
'word/document.xml':doc,'word/styles.xml':styles,'word/_rels/document.xml.rels':rels,
'word/header1.xml':header,'word/footer1.xml':footer,
'word/settings.xml':f'<w:settings xmlns:w="{W}"><w:defaultTabStop w:val="720"/><w:compat/><w:updateFields w:val="true"/></w:settings>',
'docProps/core.xml':core}
for name,xml in files.items(): ET.fromstring(xml)
with ZipFile(OUT,'w',ZIP_DEFLATED) as z:
    for name,xml in files.items(): z.writestr(name,xml.encode('utf-8'))
with ZipFile(OUT) as z:
    assert z.testzip() is None
    root=ET.fromstring(z.read('word/document.xml'))
    txt='\n'.join(e.text or '' for e in root.iter(f'{{{W}}}t'))
    for n in range(1,12): assert any(s.startswith(str(n)+'. ') for s in txt.splitlines())
    assert len(root.findall(f'.//{{{W}}}tbl'))==3
    assert len(links)>17
    assert "RF e RNF" in txt and "15 testes" in txt
print(json.dumps({"path":str(OUT),"size":OUT.stat().st_size,"words":len(txt.split()),"planned_pages":6,"tables":3,"hyperlinks":len(links)},ensure_ascii=False))


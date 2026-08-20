"""Gera receitas/data.js com passos (instruções PT) nas receitas existentes
e acrescenta receitas novas vindas do TheMealDB (backend/_search_full.json).

Uso:  python backend/build_data.py
"""
import json
import re
import sys

SRC = "receitas/data.js"

# ---------------------------------------------------------------- passos ------
PASSOS = {
    "sardinhas": [
        "Liga o grelhador no máximo ou o forno a 240 °C e arranja as sardinhas (pede para as amanharem na peixaria).",
        "Tempera com sal grosso e pincela com um fio de azeite.",
        "Grelha ou assa a lume forte, 3–4 minutos de cada lado, até a pele ficar dourada.",
        "Serve com batatas cozidas, pimentos assados e gomos de limão.",
    ],
    "caldeirada": [
        "Corta o peixe em postas e tempera com sal. Reserva enquanto preparas o refogado.",
        "Num tacho largo, aquece o azeite em lume médio e refoga a cebola, o pimento e o tomate picados.",
        "Junta as batatas às rodelas e água quente até quase cobrir. Deixa cozer 10 minutos em lume médio.",
        "Adiciona o peixe e cozinha em lume brando mais 10–15 minutos, sem mexer muito.",
    ],
    "salada-salmao": [
        "Grelha ou passa o salmão na frigideira em lume médio-alto com um fio de azeite, 2–3 minutos de cada lado.",
        "Corta o abacate e o pepino e dispõe com a alface numa taça.",
        "Desfaz o salmão em lascas por cima da salada.",
        "Tempera com sumo de limão, azeite e sal.",
    ],
    "salmao-teriyaki": [
        "Mistura o molho de soja, o mel, o alho picado e o gengibre.",
        "Marina os lombos de salmão na mistura durante 10–15 minutos.",
        "Grelha ou assa os lombos a 200 °C, 3–4 minutos de cada lado, pincelando com a marinada.",
        "Serve com arroz branco e o molho restante.",
    ],
    "salmao-forno": [
        "Pré-aquece o forno a 200 °C.",
        "Corta o funcho fino e dispõe com o tomate cereja num tabuleiro.",
        "Coloca o salmão por cima, tempera e rega com azeite e limão.",
        "Assa 18–20 minutos a 200 °C até o salmão estar cozinhado.",
    ],
    "empadao-peixe": [
        "Coze o peixe em leite com uma folha de louro em lume brando, 5–6 minutos. Reserva o leite e desfaz o peixe.",
        "Coze as batatas 15 minutos em água a ferver; esmaga-as com manteiga e um pouco do leite.",
        "Faz um creme com a farinha e o leite em lume brando, junta o peixe e as ervilhas.",
        "Monta com o peixe por baixo e o puré por cima; leva ao forno a 200 °C até dourar (15–20 minutos).",
    ],
    "paella": [
        "Refoga o pimento e o alho no azeite em lume médio.",
        "Junta o arroz e mexe, depois adiciona o açafrão e caldo quente (o dobro do volume do arroz).",
        "A meio da cozedura junta o camarão, as lulas e os mexilhões.",
        "Tapa e cozinha em lume brando 18–20 minutos, até o arroz absorver o líquido.",
    ],
    "atum-nicoise": [
        "Coze as batatas 15 minutos e o feijão-verde 5 minutos em água a ferver; coze os ovos 9–10 minutos.",
        "Escorre o atum e dispõe tudo numa travessa.",
        "Junta as azeitonas e tempera com azeite, sal e pimenta.",
        "Serve frio ou morno.",
    ],
    "frango-piripiri": [
        "Tempera o frango com piripiri, alho, limão e sal. Deixa marinar (ideal 30 minutos).",
        "Grelha a lume médio ou assa a 200 °C, 12–15 minutos de cada lado, até ficar dourado e cozinhado.",
        "Prepara a salada ralando a cenoura e fatiando a couve.",
        "Serve o frango com a salada por cima.",
    ],
    "frango-basco": [
        "Aloura o frango no azeite em lume médio-alto. Retira.",
        "Na mesma panela refoga o pimento, a cebola e o alho em lume médio.",
        "Junta o tomate e deixa apurar, depois volta a colocar o frango.",
        "Tapa e cozinha 20–25 minutos em lume brando até o molho engrossar.",
    ],
    "cuscuz-frango": [
        "Salteia o frango temperado no azeite em lume médio-alto até dourar.",
        "Junta legumes a gosto e água ou caldo; deixa cozinhar em lume médio.",
        "Hidrata o cuscuz com água a ferver (mesmo volume) e um fio de azeite; tapa 5 minutos.",
        "Solta o cuscuz com um garfo e serve com o frango.",
    ],
    "arroz-frango-chourico": [
        "Refoga a cebola e o alho no azeite em lume médio.",
        "Junta o frango e o chouriço às rodelas e deixa ganhar cor.",
        "Adiciona o arroz e mexe; junta caldo quente (o dobro do volume).",
        "Tapa e cozinha 15–18 minutos em lume brando até o arroz estar pronto.",
    ],
    "frango-teriyaki": [
        "Tempera as coxas de frango e coloca num tabuleiro.",
        "Mistura o molho teriyaki (soja, mel e alho) e rega o frango.",
        "Assa a 200 °C, virando a meio, até caramelizar (25–30 minutos).",
        "Serve com arroz e cebolinho.",
    ],
    "prego": [
        "Tempera os bifes com sal, alho e piripiri verde.",
        "Aquece uma frigideira bem quente em lume alto com azeite e frita os bifes 1–2 minutos de cada lado.",
        "Tosta o pão na gordura do bife.",
        "Monta o prego no pão e serve logo.",
    ],
    "febras": [
        "Tempera as febras com sal, alho, louro e um fio de azeite.",
        "Grelha a lume médio-alto ou assa na airfryer a 200 °C durante 12–15 minutos, até douradas e cozinhadas.",
        "Deixa repousar 2 minutos antes de servir.",
        "Serve com arroz e salada.",
    ],
    "strogonoff": [
        "Aloura a carne cortada em tiras no azeite ou manteiga em lume médio-alto. Retira.",
        "Refoga a cebola e os cogumelos em lume médio; junta mostarda e um pouco de caldo.",
        "Volta a colocar a carne e junta as natas.",
        "Cozinha 5 minutos em lume brando e serve com arroz ou puré.",
    ],
    "vaca-brocolos": [
        "Salteia a carne em tiras num wok em lume alto. Retira.",
        "Salteia os brócolos com o alho e o gengibre em lume alto.",
        "Junta a carne, o molho de soja e um pouco de água.",
        "Cozinha 2–3 minutos em lume forte e serve com arroz.",
    ],
    "moussaka": [
        "Frita ou assa as rodelas de beringela a 200 °C até ficarem macias.",
        "Prepara o recheio de carne com tomate e especiarias em lume médio.",
        "Monta camadas de beringela, carne e bechamel.",
        "Assa a 180 °C até dourar (35–40 minutos).",
    ],
    "carbonara": [
        "Coze o esparguete em água a ferver com sal durante 8–10 minutos.",
        "Salteia a pancetta em lume médio até ficar crocante.",
        "Mistura as gemas com o pecorino e pimenta.",
        "Junta a massa à pancetta, tira do lume e envolve com as gemas até formar o creme.",
    ],
    "bolonhesa": [
        "Refoga a cebola, o alho e a cenoura em lume médio.",
        "Junta a carne picada e deixa alourar.",
        "Adiciona o tomate, a polpa e um pouco de caldo; cozinha 30 minutos em lume brando.",
        "Coze o esparguete 8–10 minutos em água a ferver e serve com o molho e parmesão.",
    ],
    "lasanha": [
        "Prepara o molho bolonhesa e o bechamel.",
        "Monta camadas de placas, carne e bechamel num tabuleiro.",
        "Termina com bechamel e queijo.",
        "Assa a 180 °C durante 35–40 minutos.",
    ],
    "fettuccine": [
        "Coze o fettuccine em água a ferver com sal durante 8–10 minutos.",
        "Derrete a manteiga em lume brando e junta as natas e o parmesão até engrossar.",
        "Envolve a massa no molho.",
        "Serve com mais parmesão e pimenta.",
    ],
    "arrabiata": [
        "Refoga o alho e a malagueta no azeite em lume médio.",
        "Junta o tomate e deixa apurar 10–15 minutos em lume brando.",
        "Coze o penne 9–11 minutos em água a ferver e envolve no molho.",
        "Serve com salsa e parmesão.",
    ],
    "tortilha": [
        "Bate os ovos com sal.",
        "Salteia a batata e a cebola em lume médio até ficarem macias.",
        "Mistura os legumes nos ovos.",
        "Coze em lume médio-baixo dos dois lados numa frigideira (ou 4–5 minutos a 800 W no microondas num recipiente untado).",
    ],
    "shakshuka": [
        "Refoga a cebola, o pimento e o alho em lume médio.",
        "Junta o tomate e as especiarias; cozinha 10 minutos até engrossar.",
        "Abre buracos e parte os ovos por cima.",
        "Tapa e cozinha 6–8 minutos em lume brando até as claras firmarem.",
    ],
    "chili-vegetariano": [
        "Refoga a cebola, o alho e o pimento em lume médio.",
        "Junta o feijão, o tomate, o milho e as especiarias.",
        "Deixa cozinhar 15–20 minutos em lume brando.",
        "Serve com arroz ou tortilhas.",
    ],
    "falafel": [
        "Tritura o grão-de-bico com a cebola, o alho, a salsa e as especiarias.",
        "Forma bolinhas ou discos.",
        "Coze na airfryer a 190 °C durante 12–15 minutos (ou frita a 180 °C) até dourar.",
        "Serve com pão pita, iogurte e salada.",
    ],
    "ratatouille": [
        "Corta a beringela, a curgete, o pimento e o tomate em rodelas ou cubos.",
        "Refoga a cebola e o alho em lume médio; junta os legumes em camadas.",
        "Rega com azeite e tomilho.",
        "Assa a 190 °C até os legumes ficarem macios (35–40 minutos).",
    ],
    "fajitas-grao": [
        "Salteia a cebola e o pimento em lume médio-alto.",
        "Junta o grão-de-bico e as especiarias.",
        "Aquece as tortilhas numa frigideira seca em lume médio.",
        "Recheia e serve com iogurte ou abacate.",
    ],
    "lentilhas-abobora": [
        "Refoga a cebola e o alho em lume médio.",
        "Junta a abóbora, as lentilhas e o caldo.",
        "Cozinha 20–25 minutos em lume brando até a abóbora desfazer.",
        "Tempera com cominhos e pimenta e serve.",
    ],
    "dal": [
        "Lava as lentilhas e coze-as em lume brando com água e curcuma.",
        "Noutra panela, faz o tempero com alho, gengibre e especiarias no azeite em lume médio.",
        "Junta o tempero às lentilhas e cozinha mais 5 minutos em lume brando.",
        "Serve com arroz.",
    ],
    "feijao-curry": [
        "Refoga a cebola, o alho e o gengibre em lume médio.",
        "Junta o caril e o tomate; cozinha 5 minutos em lume médio.",
        "Adiciona o feijão e o leite de coco.",
        "Cozinha 10 minutos em lume brando e serve com arroz.",
    ],
    "rotolo": [
        "Salteia os cogumelos com o alho e os espinafres em lume médio.",
        "Estende a massa, cobre com o recheio e enrola.",
        "Envolve em película e coze 20 minutos em água a ferver (ou assa a 180 °C).",
        "Corta em fatias e serve com molho de tomate.",
    ],
    "batatas-bravas": [
        "Corta as batatas em cubos e tempera.",
        "Assa na airfryer a 200 °C ou no forno a 220 °C durante 20–25 minutos, até douradas e crocantes.",
        "Prepara o molho bravo com tomate, alho e malagueta em lume brando.",
        "Serve as batatas com o molho por cima.",
    ],
    "salada-massa": [
        "Coze a massa 8–10 minutos em água a ferver e arrefece em água fria.",
        "Junta o tomate, o pepino, o pimento, as azeitonas e o feta.",
        "Tempera com azeite, limão e orégãos.",
        "Serve fria.",
    ],
    "pasteis-nata": [
        "Aquece o leite com o açúcar e a canela em lume brando, sem ferver.",
        "Junta a farinha e as gemas, mexendo em lume brando até engrossar (creme).",
        "Forra as formas com massa folhada e enche com o creme.",
        "Assa a 250 °C até queimar ligeiramente por cima.",
    ],
    "crumble": [
        "Descasca e corta as maçãs; coze em lume brando com açúcar e canela.",
        "Mistura a farinha, a manteiga e o açúcar até formar migalhas.",
        "Deita a fruta num tabuleiro e cobre com o crumble.",
        "Assa a 180 °C até dourar (30 minutos).",
    ],
    "bolo-cenoura": [
        "Rala a cenoura e mistura com os secos (farinha e açúcar).",
        "Junta os ovos, o óleo e as nozes.",
        "Deita numa forma e assa a 180 °C durante 40–45 minutos.",
        "Deixa arrefecer antes de desenformar.",
    ],
    "panquecas-banana": [
        "Esmaga as bananas e mistura com os ovos, o leite e a farinha.",
        "Junta o fermento e mexe até ficar homogéneo.",
        "Coze pequenas porções numa frigideira em lume médio até dourar dos dois lados.",
        "Serve com mel ou fruta.",
    ],
    "empanadas-camarao": [
        "Salteia o camarão com o alho e o cebolinho em lume médio. Deixa arrefecer.",
        "Corta círculos na massa quebrada.",
        "Recheia, fecha e pincela com ovo.",
        "Assa a 200 °C (ou frita a 180 °C) até dourar.",
    ],
}

# ------------------------------------------------------- receitas novas ------
# Estrutura: dict com id, nome, nomeOrig, categoria, tempo, preco, alergenios,
# lojas, foto, dica, ingredientes (list de [nome, qtd]), passos (list).
NOVAS = [
    {
        "id": "tortilha-chourico", "nome": "Tortilha de chouriço e batata",
        "nomeOrig": "Chorizo, potato & cheese omelette", "categoria": "Pequeno-almoço",
        "tempo": 25, "preco": 1.8, "alergenios": ["ovo", "lactose"],
        "lojas": ["continente", "pingoDoce", "mercadona"],
        "foto": "https://www.themealdb.com/images/media/meals/0y6uvc1763258983.jpg",
        "dica": "Fica ótimo com pão torrado ao pequeno-almoço.",
        "ingredientes": [("Batatas", "300 g"), ("Azeite", "1 c. sopa"), ("Chouriço", "100 g"),
                         ("Ovos", "6 unidades"), ("Queijo cheddar", "50 g"), ("Salsa", "q.b.")],
        "passos": [
            "Coze as batatas em água a ferver 8–10 minutos, escorre e deixa secar.",
            "Aquece o azeite em lume médio, junta o chouriço e cozinha 2 minutos; adiciona as batatas e deixa dourar mais 5 minutos.",
            "Bate os ovos com sal e verte na frigideira com o chouriço e as batatas.",
            "Quando estiver quase pronta, espalha o queijo e a salsa por cima.",
        ],
    },
    {
        "id": "panquecas", "nome": "Panquecas", "nomeOrig": "Pancakes",
        "categoria": "Pequeno-almoço", "tempo": 25, "preco": 1.2,
        "alergenios": ["ovo", "lactose", "gluten"], "lojas": ["continente", "pingoDoce", "mercadona"],
        "foto": "https://www.themealdb.com/images/media/meals/rwuyqx1511383174.jpg",
        "dica": "Dobra a receita e congela as panquecas para a semana.",
        "ingredientes": [("Farinha", "200 g"), ("Ovos", "2 unidades"), ("Leite", "300 ml"),
                         ("Óleo", "1 c. sopa"), ("Açúcar", "2 c. sopa"), ("Framboesas", "q.b.")],
        "passos": [
            "Mistura a farinha, os ovos, o leite, o óleo e uma pitada de sal até obter uma massa lisa.",
            "Deixa repousar 30 minutos (ou cozinha já).",
            "Aquece uma frigideira untada em lume médio e cozinha as panquecas 1 minuto de cada lado, até dourar.",
            "Serve com açúcar e framboesas por cima.",
        ],
    },
    {
        "id": "panquecas-aveia", "nome": "Panquecas de aveia", "nomeOrig": "Oatmeal pancakes",
        "categoria": "Pequeno-almoço", "tempo": 25, "preco": 1.0,
        "alergenios": ["ovo", "lactose", "gluten"], "lojas": ["continente", "pingoDoce", "mercadona"],
        "foto": "https://www.themealdb.com/images/media/meals/c400ok1764439058.jpg",
        "dica": "Usa aveia normal triturada no liquidificador.",
        "ingredientes": [("Ovos", "1 unidade"), ("Leite", "80 ml"), ("Açúcar", "1 c. sopa"),
                         ("Fermento", "1 c. chá"), ("Aveia", "150 g"), ("Manteiga", "1 c. sopa"),
                         ("Morangos", "q.b.")],
        "passos": [
            "Bate todos os ingredientes (menos os morangos) até ficar homogéneo.",
            "Deixa a massa repousar 10 minutos.",
            "Unta uma frigideira com manteiga em lume médio e coze pequenas porções, virando quando borbulhar.",
            "Serve com os morangos e um fio de mel.",
        ],
    },
    {
        "id": "sopa-abobora", "nome": "Sopa de abóbora tailandesa", "nomeOrig": "Thai pumpkin soup",
        "categoria": "Sopa", "tempo": 45, "preco": 1.5, "alergenios": [],
        "lojas": ["continente", "mercadona"],
        "foto": "https://www.themealdb.com/images/media/meals/1brbso1763585098.jpg",
        "dica": "Um fio de leite de coco extra na hora de servir.",
        "ingredientes": [("Abóbora", "1,2 kg"), ("Óleo", "2 c. sopa"), ("Cebola", "1 unidade"),
                         ("Gengibre", "1 c. sopa"), ("Erva-príncipe", "1 haste"),
                         ("Pasta de caril vermelho", "2 c. sopa"), ("Leite de coco", "400 ml"),
                         ("Caldo de legumes", "800 ml"), ("Malagueta", "1 unidade")],
        "passos": [
            "Assa a abóbora aos cubos com metade do óleo a 200 °C durante 30 minutos, até dourar.",
            "Refoga a cebola, o gengibre e a erva-príncipe no óleo restante em lume médio.",
            "Junta a pasta de caril, a abóbora, o leite de coco e o caldo; cozinha 5 minutos.",
            "Tritura tudo e serve com malagueta fresca.",
        ],
    },
    {
        "id": "sopa-tomate", "nome": "Sopa de tomate cremosa", "nomeOrig": "Creamy tomato soup",
        "categoria": "Sopa", "tempo": 40, "preco": 1.3, "alergenios": ["lactose"],
        "lojas": ["continente", "pingoDoce", "mercadona"],
        "foto": "https://www.themealdb.com/images/media/meals/stpuws1511191310.jpg",
        "dica": "Acompanha com croutons e manjericão.",
        "ingredientes": [("Azeite", "2 c. sopa"), ("Cebola", "1 unidade"), ("Aipo", "2 talos"),
                         ("Cenoura", "1 unidade"), ("Batatas", "300 g"), ("Polpa de tomate", "3 c. sopa"),
                         ("Tomate picado", "1 lata"), ("Caldo de legumes", "2 cubos"), ("Leite", "200 ml")],
        "passos": [
            "Refoga o azeite com a cebola, o aipo, a cenoura, as batatas e o louro em lume médio durante 10–15 minutos.",
            "Junta a polpa, o tomate, os cubos de caldo e 1 L de água a ferver; coze 15 minutos em lume brando.",
            "Tritura até ficar cremosa.",
            "Junta o leite, aquece em lume brando sem ferver e serve.",
        ],
    },
    {
        "id": "sopa-grao", "nome": "Sopa de grão-de-bico", "nomeOrig": "Leblebi soup",
        "categoria": "Sopa", "tempo": 45, "preco": 1.0, "alergenios": [],
        "lojas": ["continente", "mercadona"],
        "foto": "https://www.themealdb.com/images/media/meals/x2fw9e1560460636.jpg",
        "dica": "Serve com pão pita tostado.",
        "ingredientes": [("Azeite", "2 c. sopa"), ("Cebola", "1 unidade"), ("Grão-de-bico", "400 g"),
                         ("Caldo de legumes", "1 L"), ("Cominhos", "1 c. chá"), ("Alho", "3 dentes"),
                         ("Harissa", "1 c. chá"), ("Limão", "1 unidade")],
        "passos": [
            "Refoga a cebola no azeite em lume médio até ficar macia.",
            "Junta o grão-de-bico e o caldo; deixa ferver e cozinha 20 minutos em lume brando.",
            "Torra os cominhos, pisa com o alho e a harissa e junta à sopa.",
            "Serve com sumo de limão e um fio de azeite.",
        ],
    },
    {
        "id": "kofta-burgers", "nome": "Hambúrgueres kofta", "nomeOrig": "Kofta burgers",
        "categoria": "Borrego", "tempo": 35, "preco": 3.5, "alergenios": ["lactose", "gluten"],
        "lojas": ["continente", "pingoDoce", "mercadona"],
        "foto": "https://www.themealdb.com/images/media/meals/lgmnff1763789847.jpg",
        "dica": "Molda com as mãos húmidas para não colar.",
        "ingredientes": [("Borrego picado", "600 g"), ("Cebola", "1 unidade"), ("Alho", "3 dentes"),
                         ("Garam masala", "1 c. sopa"), ("Coentros", "1 maço"),
                         ("Molho de malagueta", "1 c. sopa"), ("Pão pita", "4 unidades"),
                         ("Tomate", "2 unidades"), ("Couve roxa", "100 g"), ("Iogurte", "1 embalagem")],
        "passos": [
            "Mistura a carne com a cebola, o alho, o garam masala, os coentros e o molho de malagueta.",
            "Forma 8 hambúrgueres pequenos e achata.",
            "Grelha a lume médio-alto, 3–4 minutos de cada lado, até dourados.",
            "Serve no pão pita com tomate, couve roxa e iogurte.",
        ],
    },
    {
        "id": "almondegas-borrego", "nome": "Almôndegas de borrego com alperce",
        "nomeOrig": "Lamb & apricot meatballs", "categoria": "Borrego", "tempo": 35, "preco": 3.8,
        "alergenios": ["gluten"], "lojas": ["continente", "pingoDoce", "mercadona"],
        "foto": "https://www.themealdb.com/images/media/meals/72fgzj1764109947.jpg",
        "dica": "Os alperces dão um toque agridoce surpreendente.",
        "ingredientes": [("Azeite", "2 c. sopa"), ("Cebola roxa", "1 unidade"), ("Alho", "4 dentes"),
                         ("Cominhos", "1 c. chá"), ("Tomate picado", "1 lata"), ("Borrego picado", "500 g"),
                         ("Alperces secos", "8 unidades"), ("Pão ralado", "50 g"), ("Hortelã", "q.b."),
                         ("Pão pita", "4 unidades")],
        "passos": [
            "Refoga a cebola no azeite em lume médio; junta o alho e as especiarias e cozinha mais 2 minutos.",
            "Reserva metade; à restante junta o tomate e deixa apurar 10 minutos em lume brando.",
            "Mistura a carne com a cebola reservada, os alperces picados, o pão ralado e a hortelã; forma almôndegas.",
            "Cozinha as almôndegas no molho 15 minutos em lume brando e serve com pão pita.",
        ],
    },
    {
        "id": "caril-katsu", "nome": "Caril katsu de frango", "nomeOrig": "Katsu chicken curry",
        "categoria": "Frango", "tempo": 45, "preco": 3.0, "alergenios": ["gluten", "ovo", "soja"],
        "lojas": ["continente", "pingoDoce", "mercadona"],
        "foto": "https://www.themealdb.com/images/media/meals/vwrpps1503068729.jpg",
        "dica": "Corta o frango panado ainda quente para não soltar o pão ralado.",
        "ingredientes": [("Peito de frango", "600 g"), ("Farinha", "3 c. sopa"), ("Ovos", "1 unidade"),
                         ("Pão ralado", "100 g"), ("Óleo", "q.b."), ("Cebola", "1 unidade"),
                         ("Cenoura", "1 unidade"), ("Alho", "3 dentes"), ("Caril em pó", "2 c. sopa"),
                         ("Caldo de galinha", "500 ml"), ("Mel", "1 c. sopa"), ("Molho de soja", "2 c. sopa")],
        "passos": [
            "Panha o peito de frango em farinha, ovo e pão ralado e frita a 170 °C até dourar.",
            "Para o molho, refoga a cebola, o alho e a cenoura em lume médio; junta a farinha e o caril.",
            "Adiciona o caldo, o mel e o molho de soja e deixa engrossar 15 minutos em lume brando.",
            "Corta o frango panado em tiras e serve com o molho e arroz.",
        ],
    },
    {
        "id": "caril-verde", "nome": "Caril verde tailandês", "nomeOrig": "Thai green curry",
        "categoria": "Frango", "tempo": 35, "preco": 3.2, "alergenios": ["peixe"],
        "lojas": ["continente", "mercadona"],
        "foto": "https://www.themealdb.com/images/media/meals/sstssx1487349585.jpg",
        "dica": "Ajusta a malagueta ao teu gosto.",
        "ingredientes": [("Batatas", "300 g"), ("Feijão-verde", "150 g"), ("Óleo", "1 c. sopa"),
                         ("Alho", "2 dentes"), ("Pasta de caril verde", "2 c. sopa"), ("Leite de coco", "400 ml"),
                         ("Molho de peixe", "1 c. chá"), ("Frango", "450 g"), ("Manjericão", "1 maço"),
                         ("Arroz", "300 g")],
        "passos": [
            "Coze as batatas 5 minutos em água a ferver; junta o feijão-verde e coze mais 3 minutos. Escorre.",
            "Aquece o óleo em lume médio, salteia o alho e junta a pasta de caril.",
            "Adiciona o leite de coco, o molho de peixe e o frango; cozinha 10 minutos em lume brando.",
            "Junta as batatas, o feijão e o manjericão; serve com arroz.",
        ],
    },
    {
        "id": "frango-assado-argelino", "nome": "Frango assado à argelina",
        "nomeOrig": "Algerian roast chicken", "categoria": "Frango", "tempo": 70, "preco": 2.8,
        "alergenios": [], "lojas": ["continente", "pingoDoce", "mercadona"],
        "foto": "https://www.themealdb.com/images/media/meals/nlxald1764112200.jpg",
        "dica": "Deixa marinar de um dia para o outro para mais sabor.",
        "ingredientes": [("Frango inteiro", "1 unidade"), ("Cebola", "1 unidade"), ("Azeite", "5 c. sopa"),
                         ("Vinagre balsâmico", "2 c. sopa"), ("Mostarda Dijon", "1 c. sopa"),
                         ("Alho", "3 dentes"), ("Pimenta preta", "1 c. chá"), ("Cayenne", "1 c. chá")],
        "passos": [
            "Mistura a cebola, o azeite, o vinagre, a mostarda, o alho e as pimentas num recipiente.",
            "Envolve o frango na marinada e deixa repousar (ideal 1 hora ou de um dia para o outro).",
            "Leva ao forno a 175 °C durante 60–75 minutos, regando de vez em quando.",
            "Deixa repousar 10 minutos antes de trinchar.",
        ],
    },
    {
        "id": "costeletas-crioula", "nome": "Costeletas de porco à crioula",
        "nomeOrig": "Pork chops in creole sauce", "categoria": "Porco", "tempo": 30, "preco": 3.0,
        "alergenios": [], "lojas": ["continente", "pingoDoce", "mercadona"],
        "foto": "https://www.themealdb.com/images/media/meals/087fu71783802698.jpg",
        "dica": "Serve com arroz branco e feijão preto.",
        "ingredientes": [("Costeletas de porco", "4 unidades"), ("Óleo", "2 c. sopa"), ("Alho", "3 dentes"),
                         ("Mostarda", "1 c. sopa"), ("Cominhos", "1 c. sopa"), ("Tomate", "3 unidades"),
                         ("Cebola", "1 unidade"), ("Coentros", "q.b.")],
        "passos": [
            "Marina as costeletas com mostarda, cominhos, alho, sal e pimenta (ideal 1 hora).",
            "Aloura as costeletas no óleo em lume médio-alto, 3 minutos de cada lado; retira.",
            "Refoga a cebola e o tomate na mesma frigideira em lume médio até apurar.",
            "Volta a colocar as costeletas no molho, cozinha 5 minutos em lume brando e serve com coentros.",
        ],
    },
    {
        "id": "bolo-chocolate-vegan", "nome": "Bolo de chocolate vegan",
        "nomeOrig": "Vegan chocolate cake", "categoria": "Sobremesa", "tempo": 55, "preco": 1.0,
        "alergenios": ["frutosSecos"], "lojas": ["continente", "pingoDoce", "mercadona"],
        "foto": "https://www.themealdb.com/images/media/meals/qxutws1486978099.jpg",
        "dica": "Decora com framboesas para um contraste bonito.",
        "ingredientes": [("Farinha com fermento", "180 g"), ("Açúcar de coco", "100 g"), ("Cacau", "40 g"),
                         ("Fermento", "1 c. chá"), ("Sementes de linhaça", "2 c. sopa"),
                         ("Leite de amêndoa", "120 ml"), ("Baunilha", "1 c. chá"), ("Água a ferver", "120 ml")],
        "passos": [
            "Prepara o ovo de linhaça: mistura as sementes com 5 c. sopa de água e deixa 10 minutos.",
            "Mistura os secos e depois junta os molhados e a linhaça.",
            "Junta a água a ferver e mexe até ficar liso.",
            "Assa a 180 °C durante 45 minutos e decora com chocolate derretido.",
        ],
    },
    {
        "id": "brownies", "nome": "Brownies de framboesa",
        "nomeOrig": "Chocolate raspberry brownies", "categoria": "Sobremesa", "tempo": 40, "preco": 1.2,
        "alergenios": ["ovo", "lactose", "gluten"], "lojas": ["continente", "pingoDoce", "mercadona"],
        "foto": "https://www.themealdb.com/images/media/meals/yypvst1511386427.jpg",
        "dica": "Corta em quadrados só depois de arrefecer.",
        "ingredientes": [("Chocolate negro", "200 g"), ("Chocolate de leite", "100 g"), ("Manteiga", "250 g"),
                         ("Açúcar amarelo", "400 g"), ("Ovos", "4 unidades"), ("Farinha", "140 g"),
                         ("Cacau", "50 g"), ("Framboesas", "200 g")],
        "passos": [
            "Derrete o chocolate, a manteiga e o açúcar em lume brando.",
            "Junta os ovos um a um, depois a farinha e o cacau peneirados.",
            "Envolve metade das framboesas e verte no tabuleiro; espalha o resto por cima.",
            "Assa a 180 °C durante 30–35 minutos.",
        ],
    },
    {
        "id": "cheesecake", "nome": "Cheesecake de Nova Iorque",
        "nomeOrig": "New York cheesecake", "categoria": "Sobremesa", "tempo": 60, "preco": 1.5,
        "alergenios": ["lactose", "gluten", "ovo"], "lojas": ["continente", "pingoDoce", "mercadona"],
        "foto": "https://www.themealdb.com/images/media/meals/swttys1511385853.jpg",
        "dica": "Deixa no frio de um dia para o outro para firmar.",
        "ingredientes": [("Manteiga", "85 g"), ("Bolachas", "200 g"), ("Açúcar", "2 c. sopa"),
                         ("Queijo creme", "900 g"), ("Açúcar em pó", "250 g"), ("Farinha", "3 c. sopa"),
                         ("Sumo de limão", "2 c. sopa"), ("Ovos", "3 unidades"), ("Natas azedas", "300 ml")],
        "passos": [
            "Derrete a manteiga, mistura com as bolachas trituradas e o açúcar; pressiona na base da forma.",
            "Assa a base 10 minutos a 180 °C e deixa arrefecer.",
            "Bate o queijo creme com o açúcar, a farinha, o limão e os ovos; junta as natas.",
            "Deita sobre a base e assa 45 minutos a 180 °C; deixa arrefecer antes de servir.",
        ],
    },
    {
        "id": "risotto-salmao", "nome": "Risotto de salmão e camarão",
        "nomeOrig": "Salmon & prawn risotto", "categoria": "Peixe", "tempo": 40, "preco": 4.5,
        "alergenios": ["peixe", "marisco", "lactose"], "lojas": ["continente", "pingoDoce", "mercadona"],
        "foto": "https://www.themealdb.com/images/media/meals/xxrxux1503070723.jpg",
        "dica": "Usa arroz arbóreo para um risotto mais cremoso.",
        "ingredientes": [("Manteiga", "50 g"), ("Cebola", "1 unidade"), ("Arroz para risotto", "300 g"),
                         ("Vinho branco", "125 ml"), ("Caldo de legumes", "1 L"), ("Limão", "1 unidade"),
                         ("Camarão", "240 g"), ("Salmão", "300 g"), ("Espargos", "100 g"), ("Parmesão", "50 g")],
        "passos": [
            "Derrete a manteiga em lume brando e refoga a cebola sem deixar ganhar cor.",
            "Junta o arroz e mexe; adiciona o vinho e deixa absorver.",
            "Adiciona o caldo aos poucos, mexendo em lume brando, até o arroz ficar cremoso.",
            "Junta o salmão, o camarão, os espargos e o limão; cozinha 3 minutos e serve com parmesão.",
        ],
    },
    {
        "id": "bourguignon", "nome": "Vaca à bourguignon", "nomeOrig": "Beef bourguignon",
        "categoria": "Carne", "tempo": 150, "preco": 5.0, "alergenios": [],
        "lojas": ["continente", "pingoDoce", "mercadona"],
        "foto": "https://www.themealdb.com/images/media/meals/vtqxtu1511784197.jpg",
        "dica": "Melhor no dia seguinte — os sabores intensificam.",
        "ingredientes": [("Carne de vaca para estufar", "800 g"), ("Bacon", "100 g"), ("Cebolinhas", "200 g"),
                         ("Cogumelos", "250 g"), ("Alho", "2 dentes"), ("Polpa de tomate", "1 c. sopa"),
                         ("Vinho tinto", "750 ml"), ("Cenoura", "1 unidade"), ("Tomilho", "q.b."),
                         ("Louro", "2 folhas")],
        "passos": [
            "Aloura a carne em pedaços numa panela bem quente, em várias vezes.",
            "Na mesma panela, frita o bacon, as cebolinhas, os cogumelos e o alho em lume médio.",
            "Junta a carne, a polpa de tomate, o vinho e as ervas; tapa e cozinha 2 horas em lume brando.",
            "Serve com puré ou batatas assadas.",
        ],
    },
    {
        "id": "estufado-lemongrass", "nome": "Estufado de vaca com erva-príncipe",
        "nomeOrig": "Lemongrass beef stew with noodles", "categoria": "Carne", "tempo": 100, "preco": 3.5,
        "alergenios": ["soja", "gluten"], "lojas": ["continente", "mercadona"],
        "foto": "https://www.themealdb.com/images/media/meals/ntafxw1763586291.jpg",
        "dica": "Serve com noodles e coentros frescos.",
        "ingredientes": [("Gengibre", "1 c. sopa"), ("Alho", "2 dentes"), ("Erva-príncipe", "3 hastes"),
                         ("Coentros", "1 maço"), ("Malagueta", "2 unidades"), ("Óleo", "2 c. sopa"),
                         ("Carne de vaca", "500 g"), ("Molho de soja", "2 c. sopa"),
                         ("Cinco especiarias", "1 c. chá"), ("Caldo de carne", "400 ml"),
                         ("Noodles de arroz", "200 g")],
        "passos": [
            "Tritura o gengibre, o alho, a erva-príncipe, os coentros e 1 malagueta.",
            "Refoga esta pasta no óleo em lume médio 5 minutos; junta a carne, o molho de soja, as especiarias e o caldo.",
            "Tapa e cozinha 1 h 15 em lume brando, depois destapa mais 15 minutos até a carne ficar tenra.",
            "Coze os noodles e serve com o estufado e limão.",
        ],
    },
    {
        "id": "sopa-noodles-salmao", "nome": "Sopa de noodles de salmão",
        "nomeOrig": "Salmon noodle soup", "categoria": "Peixe", "tempo": 20, "preco": 3.5,
        "alergenios": ["peixe", "soja"], "lojas": ["continente", "mercadona"],
        "foto": "https://www.themealdb.com/images/media/meals/ikizdm1763760862.jpg",
        "dica": "Um caldo rápido que se faz em 20 minutos.",
        "ingredientes": [("Caldo de galinha", "1 L"), ("Pasta de caril vermelho", "1 c. chá"),
                         ("Noodles de arroz", "100 g"), ("Cogumelos shiitake", "150 g"), ("Milho", "125 g"),
                         ("Salmão", "2 postas"), ("Limão", "1 unidade"), ("Molho de soja", "1 c. sopa"),
                         ("Coentros", "q.b.")],
        "passos": [
            "Ferve o caldo com a pasta de caril em lume médio-alto.",
            "Junta os noodles e coze 8 minutos; adiciona os cogumelos e o milho e coze mais 2 minutos.",
            "Junta o salmão e cozinha 3 minutos até estar no ponto.",
            "Tira do lume, junta o limão e o molho de soja e serve com coentros.",
        ],
    },
    {
        "id": "camaroes-kungpo", "nome": "Camarões kung po", "nomeOrig": "Kung po prawns",
        "categoria": "Marisco", "tempo": 25, "preco": 4.0, "alergenios": ["marisco", "amendoim", "soja"],
        "lojas": ["continente", "pingoDoce", "mercadona"],
        "foto": "https://www.themealdb.com/images/media/meals/1525873040.jpg",
        "dica": "Serve com arroz de jasmim.",
        "ingredientes": [("Camarão", "400 g"), ("Molho de soja", "2 c. sopa"), ("Polpa de tomate", "1 c. chá"),
                         ("Farinha de milho", "1 c. chá"), ("Açúcar", "1 c. chá"), ("Óleo", "1 c. sopa"),
                         ("Amendoim", "85 g"), ("Malagueta", "3 unidades"), ("Alho", "6 dentes"),
                         ("Gengibre", "q.b.")],
        "passos": [
            "Marina os camarões com a farinha de milho e 1 c. sopa de molho de soja durante 10 minutos.",
            "Mistura o vinagre, o resto do molho de soja, a polpa, o açúcar e 2 c. sopa de água.",
            "Salteia os camarões num wok bem quente; retira.",
            "Salteia o alho, o gengibre e a malagueta, junta o molho e os camarões; serve com amendoim.",
        ],
    },
    {
        "id": "tagine", "nome": "Tagine de borrego", "nomeOrig": "Lamb tagine",
        "categoria": "Borrego", "tempo": 90, "preco": 4.0, "alergenios": [],
        "lojas": ["continente", "pingoDoce", "mercadona"],
        "foto": "https://www.themealdb.com/images/media/meals/yuwtuu1511295751.jpg",
        "dica": "Acompanha com cuscuz solto e salsa.",
        "ingredientes": [("Azeite", "2 c. sopa"), ("Cebola", "1 unidade"), ("Cenoura", "1 unidade"),
                         ("Borrego", "500 g"), ("Alho", "2 dentes"), ("Cominhos", "1 c. chá"),
                         ("Gengibre", "1 c. chá"), ("Canela", "1 c. chá"), ("Mel", "1 c. sopa"),
                         ("Alperces", "100 g"), ("Abóbora", "300 g"), ("Cuscuz", "300 g")],
        "passos": [
            "Refoga a cebola e a cenoura no azeite em lume médio.",
            "Junta o borrego aos cubos e aloura; adiciona o alho e as especiarias.",
            "Junta o mel, os alperces, a abóbora e água até cobrir; cozinha 45–60 minutos em lume brando.",
            "Serve com cuscuz e salsa picada.",
        ],
    },
    {
        "id": "tonkatsu", "nome": "Porco panado tonkatsu", "nomeOrig": "Tonkatsu pork",
        "categoria": "Porco", "tempo": 30, "preco": 2.8, "alergenios": ["gluten", "ovo", "soja"],
        "lojas": ["continente", "pingoDoce", "mercadona"],
        "foto": "https://www.themealdb.com/images/media/meals/lwsnkl1604181187.jpg",
        "dica": "Não sobreponhas as costeletas ao fritar.",
        "ingredientes": [("Costeletas de porco", "4 unidades"), ("Farinha", "100 g"), ("Ovos", "2 unidades"),
                         ("Pão ralado", "100 g"), ("Óleo", "q.b."), ("Ketchup", "2 c. sopa"),
                         ("Molho inglês", "2 c. sopa"), ("Molho de ostra", "1 c. sopa"), ("Açúcar", "1 c. sopa")],
        "passos": [
            "Espalma as costeletas entre duas folhas de papel vegetal até ~1 cm.",
            "Panha em farinha, ovo e pão ralado.",
            "Frita em óleo quente (170 °C) até dourar dos dois lados.",
            "Mistura os molhos com o açúcar e serve por cima, com arroz.",
        ],
    },
    {
        "id": "pho-vaca", "nome": "Pho de vaca", "nomeOrig": "Beef pho",
        "categoria": "Carne", "tempo": 40, "preco": 3.8, "alergenios": ["peixe"],
        "lojas": ["continente", "mercadona"],
        "foto": "https://www.themealdb.com/images/media/meals/pbzcrx1763765096.jpg",
        "dica": "Faz o caldo com antecedência para mais sabor.",
        "ingredientes": [("Caldo de carne", "1 L"), ("Cebola", "1 unidade"), ("Gengibre", "1 pedaço"),
                         ("Canela em pau", "1 unidade"), ("Anis estrelado", "2 unidades"),
                         ("Bife de lombo", "300 g"), ("Molho de peixe", "1 c. sopa"),
                         ("Noodles de arroz", "200 g"), ("Cebolinho", "2 talos"), ("Manjericão", "q.b."),
                         ("Limão", "1 unidade")],
        "passos": [
            "Chama a cebola e o gengibre numa frigideira bem quente até queimarem; junta ao caldo com as especiarias.",
            "Deixa o caldo ferver 20 minutos em lume brando e tempera com molho de peixe.",
            "Coze os noodles e distribui pelas taças; cobre com o bife fatiado fino.",
            "Verte o caldo a ferver por cima e serve com ervas e limão.",
        ],
    },
    {
        "id": "macarrao-pie", "nome": "Empadão de macarrão", "nomeOrig": "Macaroni pie",
        "categoria": "Massas", "tempo": 40, "preco": 1.8, "alergenios": ["gluten", "ovo", "lactose"],
        "lojas": ["continente", "pingoDoce", "mercadona"],
        "foto": "https://www.themealdb.com/images/media/meals/kpiu4t1782242131.jpg",
        "dica": "Usa macarrão curto para segurar o molho.",
        "ingredientes": [("Macarrão", "250 g"), ("Manteiga", "2 c. sopa"), ("Queijo cheddar", "250 g"),
                         ("Ovos", "1 unidade"), ("Leite", "250 ml"), ("Mostarda", "1 c. chá"),
                         ("Pão ralado", "2 c. sopa")],
        "passos": [
            "Coze o macarrão 8–10 minutos em água com sal; escorre e mistura com a manteiga.",
            "Mistura o queijo ralado com o macarrão ainda quente.",
            "Bate o ovo com o leite e a mostarda e envolve no macarrão.",
            "Verte numa forma, cobre com pão ralado e assa a 180 °C durante 25–30 minutos.",
        ],
    },
    {
        "id": "salada-papaia", "nome": "Salada de papaia", "nomeOrig": "Papaya salad",
        "categoria": "Salada", "tempo": 20, "preco": 1.5, "alergenios": ["amendoim"],
        "lojas": ["continente", "pingoDoce", "mercadona"],
        "foto": "https://www.themealdb.com/images/media/meals/7ytdtz1784833420.jpg",
        "dica": "Rala a papaia bem fria para ficar crocante.",
        "ingredientes": [("Papaia verde", "1/2 unidade"), ("Sumo de limão", "1 c. sopa"),
                         ("Cenoura", "1 unidade"), ("Tomate cereja", "1 chávena"), ("Cebolinho", "2 talos"),
                         ("Amendoim torrado", "50 g"), ("Alho", "1 dente")],
        "passos": [
            "Descasca e rala a papaia e a cenoura.",
            "Corta o cebolinho e os tomates ao meio.",
            "Mistura tudo numa taça com o alho picado e o sumo de limão.",
            "Salpica com o amendoim por cima.",
        ],
    },
    {
        "id": "batatas-pequeno-almoco", "nome": "Batatas de pequeno-almoço",
        "nomeOrig": "Breakfast potatoes", "categoria": "Pequeno-almoço", "tempo": 30, "preco": 1.5,
        "alergenios": [], "lojas": ["continente", "pingoDoce", "mercadona"],
        "foto": "https://www.themealdb.com/images/media/meals/1550441882.jpg",
        "dica": "Perfeitas para acompanhar ovos e bacon.",
        "ingredientes": [("Batatas", "3 unidades"), ("Azeite", "1 c. sopa"), ("Bacon", "2 fatias"),
                         ("Alho", "1 dente"), ("Xarope de ácer", "1 c. sopa"), ("Salsa", "q.b.")],
        "passos": [
            "Corta as batatas em cubos e lava em água fria.",
            "Aquece o azeite numa frigideira em lume médio-alto e cozinha as batatas até dourar (cerca de 15 minutos).",
            "Junta o bacon picado e o alho; cozinha até o bacon ficar crocante.",
            "Rega com o xarope de ácer e serve com salsa.",
        ],
    },
    {
        "id": "estufado-irlandes", "nome": "Estufado irlandês", "nomeOrig": "Irish stew",
        "categoria": "Carne", "tempo": 120, "preco": 4.5, "alergenios": [],
        "lojas": ["continente", "pingoDoce", "mercadona"],
        "foto": "https://www.themealdb.com/images/media/meals/sxxpst1468569714.jpg",
        "dica": "O segredo é cozinhar devagar até a carne desfazer.",
        "ingredientes": [("Borrego", "1 kg"), ("Azeite", "2 c. sopa"), ("Cebolinhas", "200 g"),
                         ("Cenoura", "2 unidades"), ("Nabo", "1 unidade"), ("Batatas", "400 g"),
                         ("Vinho branco", "150 ml"), ("Caldo de galinha", "450 ml"), ("Tomilho", "4 hastes")],
        "passos": [
            "Tempera o borrego e aloura em lume alto, em várias vezes.",
            "Junta as cebolinhas, a cenoura, o nabo e as batatas.",
            "Adiciona o vinho, o caldo e o tomilho; tapa.",
            "Leva ao forno a 180 °C (ou lume brando) durante 1 h 30, até a carne desfazer.",
        ],
    },
]

NOVOS_METODOS = {
    "tortilha-chourico": "fogao", "panquecas": "fogao", "panquecas-aveia": "fogao",
    "sopa-abobora": "fogao", "sopa-tomate": "fogao", "sopa-grao": "fogao",
    "kofta-burgers": "fogao", "almondegas-borrego": "fogao",
    "caril-katsu": "fogao", "caril-verde": "fogao", "frango-assado-argelino": "forno",
    "costeletas-crioula": "fogao", "bolo-chocolate-vegan": "forno", "brownies": "forno",
    "cheesecake": "forno", "risotto-salmao": "fogao", "bourguignon": "fogao",
    "estufado-lemongrass": "fogao", "sopa-noodles-salmao": "fogao", "camaroes-kungpo": "fogao",
    "tagine": "fogao", "tonkatsu": "fogao", "pho-vaca": "fogao", "macarrao-pie": "forno",
    "salada-papaia": "sem", "batatas-pequeno-almoco": "fogao", "estufado-irlandes": "forno",
}


def js_str(s):
    return json.dumps(s, ensure_ascii=False)


def js_obj_list(items):
    return "[" + ", ".join('{ nome: %s, qtd: %s }' % (js_str(n), js_str(q)) for n, q in items) + "]"


def js_passos(passos):
    return "[" + ", ".join(js_str(p) for p in passos) + "]"


def main():
    src = open(SRC, encoding="utf-8").read()
    missing = []
    for rid, passos in PASSOS.items():
        m = re.search(r'id: "%s",' % re.escape(rid), src)
        if not m:
            missing.append(rid)
            continue
        close = src.find("\n  },", m.end())
        if close == -1:
            missing.append(rid + " (sem fecho)")
            continue
        block = "\n    passos: " + js_passos(passos) + ","
        src = src[:close] + block + src[close:]

    # Receitas novas: inserir antes do fecho do array window.RECIPES.
    idx = src.rfind("];")
    if idx == -1:
        print("ERRO: não encontrei o fecho '];'")
        sys.exit(1)
    blocos = []
    for r in NOVAS:
        ing = js_obj_list(r["ingredientes"])
        passos = js_passos(r["passos"])
        b = (
            "\n  {\n"
            '    id: %s, nome: %s, nomeOrig: %s,\n'
            '    categoria: %s, tempo: %d, preco: %s, alergenios: %s,\n'
            '    lojas: %s,\n'
            '    foto: %s,\n'
            '    dica: %s,\n'
            '    ingredientes: %s,\n'
            '    passos: %s,\n'
            "  },"
        ) % (
            js_str(r["id"]), js_str(r["nome"]), js_str(r["nomeOrig"]),
            js_str(r["categoria"]), r["tempo"], r["preco"], js_str(r["alergenios"]),
            js_str(r["lojas"]), js_str(r["foto"]), js_str(r["dica"]), ing, passos,
        )
        blocos.append(b)
    src = src[:idx] + "\n" + "\n".join(blocos) + "\n" + src[idx:]

    # Metodos novos: inserir antes do fecho de window.METODOS.
    mm = src.find("window.METODOS = {")
    if mm == -1:
        print("ERRO: não encontrei window.METODOS")
        sys.exit(1)
    mclose = src.find("\n};", mm)
    if mclose == -1:
        print("ERRO: não encontrei fecho de window.METODOS")
        sys.exit(1)
    # Remove uma vírgula final já existente (ex.: `"...": "forno",`) antes de acrescentar.
    corpo = src[mm:mclose].rstrip()
    if corpo.endswith(","):
        corpo = corpo[:-1]
    entradas = ",\n".join('  "%s": "%s"' % (k, v) for k, v in NOVOS_METODOS.items())
    src = src[:mm] + corpo + ",\n" + entradas + src[mclose:]

    open(SRC, "w", encoding="utf-8").write(src)

    if missing:
        print("FALTARAM:", missing)
    else:
        print("OK: passos inseridos em todas as %d receitas existentes" % len(PASSOS))
    print("OK: %d receitas novas + %d métodos" % (len(NOVAS), len(NOVOS_METODOS)))


if __name__ == "__main__":
    main()

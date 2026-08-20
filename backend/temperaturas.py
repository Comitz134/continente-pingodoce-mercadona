# -*- coding: utf-8 -*-
"""Adiciona temperaturas/níveis de lume específicos aos passos das receitas.

Atualiza receitas/data.js (o artefacto servido) e backend/build_data.py
(fonte de verdade) para que fiquem consistentes.

Uso:  python backend/temperaturas.py
"""
import json
import re

NOVOS = {
    # ---------------- Peixe ----------------
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
    # ---------------- Frango ----------------
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
    # ---------------- Carne / Porco ----------------
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
    # ---------------- Massas ----------------
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
    # ---------------- Vegetariano / Ovos ----------------
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
    # ---------------- Sobremesas ----------------
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
    # ---------------- Novas (TheMealDB) ----------------
    "tortilha-chourico": [
        "Coze as batatas em água a ferver 8–10 minutos, escorre e deixa secar.",
        "Aquece o azeite em lume médio, junta o chouriço e cozinha 2 minutos; adiciona as batatas e deixa dourar mais 5 minutos.",
        "Bate os ovos com sal e verte na frigideira com o chouriço e as batatas.",
        "Quando estiver quase pronta, espalha o queijo e a salsa por cima.",
    ],
    "panquecas": [
        "Mistura a farinha, os ovos, o leite, o óleo e uma pitada de sal até obter uma massa lisa.",
        "Deixa repousar 30 minutos (ou cozinha já).",
        "Aquece uma frigideira untada em lume médio e cozinha as panquecas 1 minuto de cada lado, até dourar.",
        "Serve com açúcar e framboesas por cima.",
    ],
    "panquecas-aveia": [
        "Bate todos os ingredientes (menos os morangos) até ficar homogéneo.",
        "Deixa a massa repousar 10 minutos.",
        "Unta uma frigideira com manteiga em lume médio e coze pequenas porções, virando quando borbulhar.",
        "Serve com os morangos e um fio de mel.",
    ],
    "sopa-abobora": [
        "Assa a abóbora aos cubos com metade do óleo a 200 °C durante 30 minutos, até dourar.",
        "Refoga a cebola, o gengibre e a erva-príncipe no óleo restante em lume médio.",
        "Junta a pasta de caril, a abóbora, o leite de coco e o caldo; cozinha 5 minutos.",
        "Tritura tudo e serve com malagueta fresca.",
    ],
    "sopa-tomate": [
        "Refoga o azeite com a cebola, o aipo, a cenoura, as batatas e o louro em lume médio durante 10–15 minutos.",
        "Junta a polpa, o tomate, os cubos de caldo e 1 L de água a ferver; coze 15 minutos em lume brando.",
        "Tritura até ficar cremosa.",
        "Junta o leite, aquece em lume brando sem ferver e serve.",
    ],
    "sopa-grao": [
        "Refoga a cebola no azeite em lume médio até ficar macia.",
        "Junta o grão-de-bico e o caldo; deixa ferver e cozinha 20 minutos em lume brando.",
        "Torra os cominhos, pisa com o alho e a harissa e junta à sopa.",
        "Serve com sumo de limão e um fio de azeite.",
    ],
    "kofta-burgers": [
        "Mistura a carne com a cebola, o alho, o garam masala, os coentros e o molho de malagueta.",
        "Forma 8 hambúrgueres pequenos e achata.",
        "Grelha a lume médio-alto, 3–4 minutos de cada lado, até dourados.",
        "Serve no pão pita com tomate, couve roxa e iogurte.",
    ],
    "almondegas-borrego": [
        "Refoga a cebola no azeite em lume médio; junta o alho e as especiarias e cozinha mais 2 minutos.",
        "Reserva metade; à restante junta o tomate e deixa apurar 10 minutos em lume brando.",
        "Mistura a carne com a cebola reservada, os alperces picados, o pão ralado e a hortelã; forma almôndegas.",
        "Cozinha as almôndegas no molho 15 minutos em lume brando e serve com pão pita.",
    ],
    "caril-katsu": [
        "Panha o peito de frango em farinha, ovo e pão ralado e frita a 170 °C até dourar.",
        "Para o molho, refoga a cebola, o alho e a cenoura em lume médio; junta a farinha e o caril.",
        "Adiciona o caldo, o mel e o molho de soja e deixa engrossar 15 minutos em lume brando.",
        "Corta o frango panado em tiras e serve com o molho e arroz.",
    ],
    "caril-verde": [
        "Coze as batatas 5 minutos em água a ferver; junta o feijão-verde e coze mais 3 minutos. Escorre.",
        "Aquece o óleo em lume médio, salteia o alho e junta a pasta de caril.",
        "Adiciona o leite de coco, o molho de peixe e o frango; cozinha 10 minutos em lume brando.",
        "Junta as batatas, o feijão e o manjericão; serve com arroz.",
    ],
    "frango-assado-argelino": [
        "Mistura a cebola, o azeite, o vinagre, a mostarda, o alho e as pimentas num recipiente.",
        "Envolve o frango na marinada e deixa repousar (ideal 1 hora ou de um dia para o outro).",
        "Leva ao forno a 175 °C durante 60–75 minutos, regando de vez em quando.",
        "Deixa repousar 10 minutos antes de trinchar.",
    ],
    "costeletas-crioula": [
        "Marina as costeletas com mostarda, cominhos, alho, sal e pimenta (ideal 1 hora).",
        "Aloura as costeletas no óleo em lume médio-alto, 3 minutos de cada lado; retira.",
        "Refoga a cebola e o tomate na mesma frigideira em lume médio até apurar.",
        "Volta a colocar as costeletas no molho, cozinha 5 minutos em lume brando e serve com coentros.",
    ],
    "bolo-chocolate-vegan": [
        "Prepara o ovo de linhaça: mistura as sementes com 5 c. sopa de água e deixa 10 minutos.",
        "Mistura os secos e depois junta os molhados e a linhaça.",
        "Junta a água a ferver e mexe até ficar liso.",
        "Assa a 180 °C durante 45 minutos e decora com chocolate derretido.",
    ],
    "brownies": [
        "Derrete o chocolate, a manteiga e o açúcar em lume brando.",
        "Junta os ovos um a um, depois a farinha e o cacau peneirados.",
        "Envolve metade das framboesas e verte no tabuleiro; espalha o resto por cima.",
        "Assa a 180 °C durante 30–35 minutos.",
    ],
    "cheesecake": [
        "Derrete a manteiga, mistura com as bolachas trituradas e o açúcar; pressiona na base da forma.",
        "Assa a base 10 minutos a 180 °C e deixa arrefecer.",
        "Bate o queijo creme com o açúcar, a farinha, o limão e os ovos; junta as natas.",
        "Deita sobre a base e assa 45 minutos a 180 °C; deixa arrefecer antes de servir.",
    ],
    "risotto-salmao": [
        "Derrete a manteiga em lume brando e refoga a cebola sem deixar ganhar cor.",
        "Junta o arroz e mexe; adiciona o vinho e deixa absorver.",
        "Adiciona o caldo aos poucos, mexendo em lume brando, até o arroz ficar cremoso.",
        "Junta o salmão, o camarão, os espargos e o limão; cozinha 3 minutos e serve com parmesão.",
    ],
    "bourguignon": [
        "Aloura a carne em pedaços numa panela bem quente, em várias vezes.",
        "Na mesma panela, frita o bacon, as cebolinhas, os cogumelos e o alho em lume médio.",
        "Junta a carne, a polpa de tomate, o vinho e as ervas; tapa e cozinha 2 horas em lume brando.",
        "Serve com puré ou batatas assadas.",
    ],
    "estufado-lemongrass": [
        "Tritura o gengibre, o alho, a erva-príncipe, os coentros e 1 malagueta.",
        "Refoga esta pasta no óleo em lume médio 5 minutos; junta a carne, o molho de soja, as especiarias e o caldo.",
        "Tapa e cozinha 1 h 15 em lume brando, depois destapa mais 15 minutos até a carne ficar tenra.",
        "Coze os noodles e serve com o estufado e limão.",
    ],
    "sopa-noodles-salmao": [
        "Ferve o caldo com a pasta de caril em lume médio-alto.",
        "Junta os noodles e coze 8 minutos; adiciona os cogumelos e o milho e coze mais 2 minutos.",
        "Junta o salmão e cozinha 3 minutos até estar no ponto.",
        "Tira do lume, junta o limão e o molho de soja e serve com coentros.",
    ],
    "camaroes-kungpo": [
        "Marina os camarões com a farinha de milho e 1 c. sopa de molho de soja durante 10 minutos.",
        "Mistura o vinagre, o resto do molho de soja, a polpa, o açúcar e 2 c. sopa de água.",
        "Salteia os camarões num wok bem quente; retira.",
        "Salteia o alho, o gengibre e a malagueta, junta o molho e os camarões; serve com amendoim.",
    ],
    "tagine": [
        "Refoga a cebola e a cenoura no azeite em lume médio.",
        "Junta o borrego aos cubos e aloura; adiciona o alho e as especiarias.",
        "Junta o mel, os alperces, a abóbora e água até cobrir; cozinha 45–60 minutos em lume brando.",
        "Serve com cuscuz e salsa picada.",
    ],
    "tonkatsu": [
        "Espalma as costeletas entre duas folhas de papel vegetal até ~1 cm.",
        "Panha em farinha, ovo e pão ralado.",
        "Frita em óleo quente (170 °C) até dourar dos dois lados.",
        "Mistura os molhos com o açúcar e serve por cima, com arroz.",
    ],
    "pho-vaca": [
        "Chama a cebola e o gengibre numa frigideira bem quente até queimarem; junta ao caldo com as especiarias.",
        "Deixa o caldo ferver 20 minutos em lume brando e tempera com molho de peixe.",
        "Coze os noodles e distribui pelas taças; cobre com o bife fatiado fino.",
        "Verte o caldo a ferver por cima e serve com ervas e limão.",
    ],
    "macarrao-pie": [
        "Coze o macarrão 8–10 minutos em água com sal; escorre e mistura com a manteiga.",
        "Mistura o queijo ralado com o macarrão ainda quente.",
        "Bate o ovo com o leite e a mostarda e envolve no macarrão.",
        "Verte numa forma, cobre com pão ralado e assa a 180 °C durante 25–30 minutos.",
    ],
    "salada-papaia": [
        "Descasca e rala a papaia e a cenoura.",
        "Corta o cebolinho e os tomates ao meio.",
        "Mistura tudo numa taça com o alho picado e o sumo de limão.",
        "Salpica com o amendoim por cima.",
    ],
    "batatas-pequeno-almoco": [
        "Corta as batatas em cubos e lava em água fria.",
        "Aquece o azeite numa frigideira em lume médio-alto e cozinha as batatas até dourar (cerca de 15 minutos).",
        "Junta o bacon picado e o alho; cozinha até o bacon ficar crocante.",
        "Rega com o xarope de ácer e serve com salsa.",
    ],
    "estufado-irlandes": [
        "Tempera o borrego e aloura em lume alto, em várias vezes.",
        "Junta as cebolinhas, a cenoura, o nabo e as batatas.",
        "Adiciona o vinho, o caldo e o tomilho; tapa.",
        "Leva ao forno a 180 °C (ou lume brando) durante 1 h 30, até a carne desfazer.",
    ],
}


def js_str(s):
    return json.dumps(s, ensure_ascii=False)


def js_arr(steps):
    return "[" + ", ".join(js_str(s) for s in steps) + "]"


def patch_datajs():
    path = "receitas/data.js"
    src = open(path, encoding="utf-8").read()
    missing = []
    for rid, steps in NOVOS.items():
        m = re.search(r'id: "%s"' % re.escape(rid), src)
        if not m:
            missing.append(rid)
            continue
        p = src.find("passos: ", m.end())
        e = src.find("],", p)
        if p == -1 or e == -1:
            missing.append(rid)
            continue
        src = src[:p] + "passos: " + js_arr(steps) + "," + src[e + 2:]
    open(path, "w", encoding="utf-8").write(src)
    print("data.js: %d/%d substituídos" % (len(NOVOS) - len(missing), len(NOVOS)))
    if missing:
        print("  FALTARAM:", missing)


def patch_build():
    path = "backend/build_data.py"
    src = open(path, encoding="utf-8").read()
    missing = []
    for rid, steps in NOVOS.items():
        # 1) Entrada no dict PASSOS = { "id": [ ... ], }
        i = src.find('    "%s": [' % rid)
        if i != -1:
            e = src.find("\n    ],", i)
            if e == -1:
                missing.append(rid + " (PASSOS sem fecho)")
                continue
            lines = "\n".join("        %s," % js_str(s) for s in steps)
            block = '    "%s": [\n%s\n    ],' % (rid, lines)
            src = src[:i] + block + src[e + len("\n    ],"):]
            continue
        # 2) Receita nova na lista NOVAS -> "id": "x", ... "passos": [ ... ],
        i = src.find('"id": "%s"' % rid)
        if i == -1:
            missing.append(rid)
            continue
        p = src.find('"passos": [', i)
        e = src.find("\n        ],", p)
        if p == -1 or e == -1:
            missing.append(rid + " (NOVAS sem fecho)")
            continue
        lines = "\n".join("            %s," % js_str(s) for s in steps)
        block = '"passos": [\n%s\n        ],' % lines
        src = src[:p] + block + src[e + len("\n        ],"):]
    open(path, "w", encoding="utf-8").write(src)
    print("build_data.py: %d/%d substituídos" % (len(NOVOS) - len(missing), len(NOVOS)))
    if missing:
        print("  FALTARAM:", missing)


if __name__ == "__main__":
    patch_datajs()
    patch_build()

"""Genera el informe a partir de consultas ejecutadas y capturas de Neo4j Query."""
import html
import json
import textwrap
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                               TableStyle, Preformatted, Image, PageBreak, KeepTogether)

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'output' / 'pdf' / 'Carlon-Serin.pdf'
OUT.parent.mkdir(parents=True, exist_ok=True)
TMP = ROOT / 'tmp' / 'pdfs'
TMP.mkdir(parents=True, exist_ok=True)
pdfmetrics.registerFont(TTFont('ArialTask', 'C:/Windows/Fonts/arial.ttf'))
pdfmetrics.registerFont(TTFont('ArialTaskBold', 'C:/Windows/Fonts/arialbd.ttf'))
pdfmetrics.registerFont(TTFont('CodeTask', 'C:/Windows/Fonts/consola.ttf'))
pdfmetrics.registerFontFamily('ArialTask', normal='ArialTask', bold='ArialTaskBold',
                            italic='ArialTask', boldItalic='ArialTaskBold')
styles = getSampleStyleSheet()
styles.add(ParagraphStyle('BodyTask', fontName='ArialTask', fontSize=9.5, leading=14,
                          spaceAfter=8, textColor=colors.black))
styles.add(ParagraphStyle('TitleTask', fontName='ArialTaskBold', fontSize=24, leading=29,
                          textColor=colors.black, spaceAfter=18))
styles.add(ParagraphStyle('H1Task', fontName='ArialTaskBold', fontSize=17, leading=21,
                          textColor=colors.black, spaceAfter=12))
styles.add(ParagraphStyle('H2Task', fontName='ArialTaskBold', fontSize=11.5, leading=15,
                          spaceBefore=10, spaceAfter=7, keepWithNext=True))
styles.add(ParagraphStyle('CodeHeadingTask', parent=styles['H2Task'],
                          spaceBefore=6, spaceAfter=5))
styles.add(ParagraphStyle('SmallTask', parent=styles['BodyTask'], fontSize=8, leading=11))
styles.add(ParagraphStyle('CaptionTask', parent=styles['SmallTask'], alignment=TA_CENTER))
styles.add(ParagraphStyle('CellTask', fontName='ArialTask', fontSize=8.4, leading=11))
styles.add(ParagraphStyle('CodeTaskStyle', fontName='CodeTask', fontSize=7.5, leading=9.5,
                          textColor=colors.black))
story = []
data = {int(p.stem.split('_')[1]): json.loads(p.read_text(encoding='utf-8'))
        for p in (ROOT / 'evidencias').glob('consulta_*.json')}


def p(text, style='BodyTask'):
    story.append(Paragraph(text, styles[style]))


def heading(text, new_page=True):
    if new_page:
        story.append(PageBreak())
    p(text, 'H1Task')


def code(n):
    p(f'Consulta {n:02} - Cypher', 'CodeHeadingTask')
    lines = []
    for line in (data[n]['consulta'] + ';').splitlines():
        lines.extend(textwrap.wrap(line, width=100, subsequent_indent='    ',
                                   break_long_words=False, break_on_hyphens=False) or [''])
    numbers = '\n'.join(f'{i:02}' for i in range(1, len(lines) + 1))
    block = Table([[Preformatted(numbers, styles['CodeTaskStyle']),
                    Preformatted('\n'.join(lines), styles['CodeTaskStyle'])]],
                  colWidths=[28, 467], hAlign='LEFT', spaceBefore=2, spaceAfter=4)
    block.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f1f1f1')),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e2e2e2')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#999999')),
        ('LINEAFTER', (0, 0), (0, -1), 0.5, colors.HexColor('#bbbbbb')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(block)


def table(headers, rows, widths=None):
    content = [[Paragraph(html.escape(str(v).lower() if isinstance(v, bool) else str(v)), styles['CellTask']) for v in row]
               for row in [headers] + rows]
    t = Table(content, colWidths=widths, repeatRows=1, hAlign='LEFT')
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dcebf2')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f4f7f9')]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEBELOW', (0, 0), (-1, 0), 0.6, colors.HexColor('#64879a')),
        ('LEFTPADDING', (0, 0), (-1, -1), 7), ('RIGHTPADDING', (0, 0), (-1, -1), 7),
        ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.extend([t, Spacer(1, 10)])


def result(n, headers=None, keys=None, widths=None):
    rows = data[n]['filas']
    keys = keys or list(rows[0])
    table(headers or keys, [[row[k] for k in keys] for row in rows], widths)


def photo(name, caption, crop=None, max_height=290):
    src = ROOT / 'evidencias' / 'capturas' / name
    im = PILImage.open(src)
    if crop:
        im = im.crop(crop)
    target = TMP / (src.stem + ('_' + '_'.join(map(str, crop)) if crop else '') + '.png')
    im.save(target)
    width, height = im.size
    scale = min(495 / width, max_height / height)
    story.append(Image(str(target), width=width * scale, height=height * scale))
    p(caption, 'CaptionTask')


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont('ArialTask', 8)
    canvas.setFillColor(colors.black)
    canvas.drawString(48, 27, 'INF325 | Tarea 3 - Neo4j | Carlon - Serin')
    canvas.drawRightString(A4[0] - 48, 27, str(doc.page))
    canvas.restoreState()


p('Tarea 3<br/>Neo4j y análisis de grafos', 'TitleTask')
p('Bases de Datos Avanzadas - INF325<br/>Universidad Técnica Federico Santa María<br/>'
  'Segundo semestre de 2026')
table(['Integrante', 'Rol universitario'], [
    ['Diego Carlon', '202173540-2'], ['Joshua Serin', '202173644-1']], [310, 185])
p('Repositorio del proyecto: '
  '<link href="https://github.com/JoshuaIV/Tarea3---Neo4j-">'
  'https://github.com/JoshuaIV/Tarea3---Neo4j-</link>', 'SmallTask')
p('Caso Halloween', 'H2Task')
p('Se analizó exclusivamente la base proporcionada en <b>tarea.dump</b>. Cada estudiante '
  'visita cinco casas distintas. Cada visita registra una cantidad de dulces y un tipo. '
  'No se generaron, insertaron, actualizaron ni eliminaron datos originales del caso.')
p('<b>Resultado principal:</b> Tomás ganó con 7 dulces. Las casas 4, 7, 9 y 10 empataron '
  'con 9 visitas cada una. Se registraron 12 visitas sin dulces (16 %).')
p('Configuración y reproducibilidad', 'H2Task')
p('Entorno local Windows con Neo4j Desktop <b>2.3.0</b>. Se creó la instancia '
  '<b>Tarea 3 - Halloween</b> desde el respaldo usando la opción de carga de archivo de '
  'Desktop. Se instaló Graph Data Science desde Plugins y se reinició la instancia. '
  'La base utilizada fue <b>neo4j</b>, no system. Ejecución: 30 de octubre de 2026.')
table(['Componente', 'Versión / valor verificado'], [
    ['Neo4j', data[1]['filas'][0]['versions'][0] + ' Enterprise'],
    ['GDS', data[2]['filas'][0]['versionGDS']], ['Base', 'neo4j'],
    ['Nodos / relaciones', '15 estudiantes + 10 casas / 75 PIDIO_DULCES']], [210, 285])
p('El archivo consultas.cypher contiene todas las consultas de este informe en orden, '
  'separadas por punto y coma y con comentarios por ejercicio. Se ejecuta sobre una copia '
  'recién restaurada del respaldo; la eliminación de la proyección se deja al final. '
  'El ZIP de entrega contiene únicamente el informe y el archivo de consultas.')

heading('Verificación del entorno y de la carga')
for n in range(1, 7):
    code(n)
    rows = data[n]['filas']
    if n == 1:
        table(['Componente', 'Versión', 'Edición'],
              [[r['name'], ', '.join(r['versions']), r['edition']] for r in rows], [195, 180, 120])
    else:
        result(n, widths=[495])
p('Los conteos coinciden con los esperados: 25 nodos y 75 relaciones. Las verificaciones '
  'se ejecutaron por separado sobre la base del caso. La consulta gds.version() se '
  'resolvió correctamente, confirmando que la biblioteca quedó disponible.')

heading('Parte 1.1 - Visualización e interpretación')
code(7)
photo('01_grafo_completo.jpg', 'Figura 1. Captura de Neo4j Query: grafo completo. '
      'Estudiantes celestes; casas rosadas. La consulta incluye también los nodos aislados.',
      (220, 98, 1900, 841), max_height=120)
photo('01_grafo_completo.jpg', 'Figura 1a. Ampliación del sector izquierdo de la misma captura.',
      (275, 515, 1092, 695), max_height=90)
photo('01_grafo_completo.jpg', 'Figura 1b. Ampliación del sector derecho de la misma captura.',
      (1092, 515, 1840, 695), max_height=90)
p('Los nodos Estudiante identifican a personas mediante id; los nodos Casa tienen un id '
  'numérico y una direccion temática. Cada flecha PIDIO_DULCES apunta desde un estudiante '
  'a la casa visitada. Se configuró id como etiqueta visible de estudiantes y direccion '
  'como etiqueta de casas. Los conteos se comprobaron con consultas, independientemente '
  'de lo que muestra la visualización.')
code(8)
result(8, ['Estudiante', 'Casa', 'Dirección', 'Cantidad', 'Tipo'],
       ['estudiante', 'casa', 'direccion', 'cantidad', 'tipo'], [75, 40, 175, 60, 145])
p('La visita de Antonia a Mundo de Jack tiene cantidad = 0 y tipo = Ninguno: hubo visita, '
  'aunque no recibió dulces. El modelo es <b>bipartito</b> porque los nodos se dividen en '
  'estudiantes y casas, y todas las relaciones conectan grupos diferentes; no hay visitas '
  'directas entre dos estudiantes ni entre dos casas.')

heading('Parte 1.2 - Casa con más visitas')
code(9)
result(9, ['ID', 'Dirección', 'Visitas'], ['id', 'direccion', 'visitas'], [45, 350, 100])
code(10)
p('<b>Máximo: 9 visitas.</b> Empatan Guarida del lobo (4), Casa de Gasper (7), '
  'Casa del cuero (9) y Pizzeria de H&amp;W (10). La consulta del máximo devuelve las '
  'cuatro casas, sin descartar empates mediante LIMIT 1.')
p('OPTIONAL MATCH conserva las diez casas, incluso si alguna tuviera cero visitas; '
  'count(r) cuenta solo relaciones presentes. En este respaldo todas tienen visitas. '
  'Una relación con cantidad = 0 también se cuenta porque representa una visita efectiva: '
  'la cantidad de dulces no determina la existencia de la conexión.')

heading('Parte 1.3 - Estudiante con más dulces')
code(11)
result(11, ['Estudiante', 'Visitas', 'Dulces'], ['estudiante', 'visitas', 'dulces'], [285, 105, 105])
code(12)
p('<b>Tomás es el único ganador, con 7 dulces en 5 visitas.</b> La consulta del máximo '
  'retorna una fila y contempla todos los empates si existieran. En conjunto se recibieron '
  '74 dulces en 75 visitas.')
p('count(r) cuenta visitas; sum(r.cantidad) suma los dulces recibidos. Todos tienen '
  'cinco visitas, pero cada relación puede aportar 0, 1 o 2 dulces. Por eso Tomás suma 7 '
  'y Sebastián y Vicente suman 3, pese a realizar la misma cantidad de visitas.')

heading('Parte 1.4 - Visitas sin dulces')
code(13)
result(13, ['Estudiante', 'Dirección', 'Tipo'], ['estudiante', 'direccion', 'tipo'], [110, 270, 115])
code(14)
result(14, ['Sin dulces', 'Visitas totales', 'Porcentaje (%)'],
       ['sinDulces', 'total', 'porcentaje'], [165, 165, 165])
p('El porcentaje observado es 100.0 × 12 / 75 = <b>16 %</b>, cuatro puntos porcentuales '
  'menos que el 20 % utilizado al generar el caso. El 20 % es una probabilidad de '
  'generación, no una cuota obligatoria: en una muestra finita de 75 visitas puede '
  'observarse otro porcentaje. La constante 100.0 fuerza aritmética decimal.')

heading('Parte 2.1 - Proyección del grafo')
code(15)
result(15, ['Proyección', 'Nodos', 'Relaciones'],
       ['graphName', 'nodeCount', 'relationshipCount'], [215, 140, 140])
p('La proyección <b>halloween</b> es una representación en memoria para ejecutar los '
  'algoritmos de GDS. Conserva las dos etiquetas de nodo y las 75 relaciones. No crea '
  'una segunda base ni modifica la original. NATURAL mantiene la dirección almacenada: '
  '<b>Estudiante → Casa</b>.')
p('Los análisis solicitados no tienen pesos: una visita cuenta como una conexión, '
  'incluyendo aquellas con cantidad = 0. No se necesita proyectar cantidad, porque '
  'ni Degree ni la similitud de conjuntos solicitada ponderan las conexiones por dulces.')
p('Para repetir la creación se debe liberar primero únicamente la proyección anterior '
  'con gds.graph.drop. Si se reinicia la instancia y ya no está en el catálogo, se '
  'debe crear nuevamente. El archivo reproducible asume una copia recién cargada.')

heading('Parte 2.2 - Degree Centrality de las casas')
code(16)
code(17)
result(18, ['ID', 'Dirección', 'GDS', 'Visitas', 'Coincide'],
       ['id', 'direccion', 'score', 'visitas', 'coincide'], [30, 235, 65, 65, 100])
p('Los diez puntajes coinciden con las visitas de la Parte 1. Las casas 4, 7, 9 y 10 '
  'comparten el máximo de 9. El filtro de casas se aplica <b>después</b> del algoritmo '
  'para mantener los estudiantes y sus conexiones en la proyección.')
p('Degree calcula conexiones de salida según la orientación de ejecución. Con NATURAL '
  'cada estudiante tendría 5 y cada casa 0. REVERSE invierte la orientación solo para '
  'el análisis y permite medir las visitas recibidas por cada casa, es decir, su '
  'grado de entrada original. Mayor centralidad significa recibir más visitas, '
  'pero no garantiza entregar más dulces: cada visita puede entregar 0, 1 o 2.')
p('Consulta usada para comprobar la equivalencia fila a fila:', 'H2Task')
code(18)

heading('Parte 2.3 - Node Similarity y Jaccard')
code(19)
result(19, ['Estudiante 1', 'Estudiante 2', 'Jaccard'],
       ['estudiante1', 'estudiante2', 'similarity'], [170, 170, 155])
p('Se comparan los vecinos de salida de cada estudiante: las casas visitadas. '
  'Las casas no tienen vecinos de salida en la proyección dirigida. topK:14 permite '
  'considerar a los otros 14 estudiantes; el umbral excluye similitudes nulas. '
  'El filtro a.id &lt; b.id conserva una sola orientación de cada pareja. Los empates '
  'se ordenan por nombres y se muestran exactamente cinco parejas.')
code(20)
result(20, ['ID', 'Casa compartida'], ['id', 'direccion'], [60, 435])
p('La pareja elegida es <b>Isidora y Nicolás</b>, la de mayor similitud. Ambos visitaron '
  'las casas {2, 4, 6, 8, 9}.')

heading('Parte 2.3 - Verificación manual e interpretación')
code(21)
table(['Medida', 'Resultado'], [['|V(Isidora)|', '5'], ['|V(Nicolás)|', '5'],
    ['Intersección', '5 casas'], ['Unión', '5 + 5 - 5 = 5 casas'],
    ['Jaccard manual', '5 / 5 = 1'], ['Jaccard GDS', '1.0']], [260, 235])
p('El resultado manual coincide con GDS. Un valor cercano a 1 indica que los conjuntos '
  'de casas visitadas se parecen mucho; el valor 1 indica que son idénticos. Se '
  'consideran las casas aunque una visita haya entregado cero dulces.')
code(22)
result(22, ['Estudiante', 'Casa', 'Dulces', 'Tipo'],
       ['estudiante', 'casa', 'dulces', 'tipo'], [85, 40, 60, 310])
p('Ambos suman 5 dulces, pero eso es una coincidencia del caso, no una consecuencia '
  'de Jaccard. Por ejemplo, en Guarida del lobo Isidora obtuvo 1 y Nicolás 2; en '
  'Lago de Jason ella obtuvo 1 y él 0. En Casa del leñador recibieron tipos diferentes. '
  'Node Similarity compara conexiones con casas, no cantidad ni tipo de dulces.')

heading('Parte 3.1 - Casas compartidas y caminos de longitud 2')
code(23)
photo('02_casas_compartidas.jpg', 'Figura 2. Captura de Query: Isidora y Nicolás, '
      'las cinco casas compartidas y sus diez relaciones.', (220, 98, 1900, 841), 280)
photo('02_casas_compartidas.jpg', 'Figura 2a. Ampliación de la misma captura para leer '
      'los nombres y las direcciones.', (650, 385, 1470, 680), 190)
p('Las casas compartidas son Mansión del conde (2), Guarida del lobo (4), Lago de Jason '
  '(6), Casa del leñador (8) y Casa del cuero (9). Cada una produce un camino '
  '<b>Isidora - Casa - Nicolás</b> de longitud 2, porque conecta a los estudiantes '
  'mediante dos relaciones de visita. La consulta devuelve los cinco patrones completos, '
  'con nodos y relaciones; no entrega solamente los nombres de las casas.')

heading('Parte 3.2 y 3.3 - Camino más corto e interpretación')
code(24)
photo('03_camino_minimo.jpg', 'Figura 3. Camino mínimo mostrado en la vista gráfica de Query.',
      (890, 420, 1210, 740), 220)
table(['Resultado', 'Valor'], [['Longitud', '2 relaciones'],
    ['Recorrido', 'Isidora → Casa del leñador ← Nicolás'],
    ['Nodos', 'Estudiante, Casa, Estudiante']], [105, 390])
p('El camino alterna estudiantes y casas porque el grafo es bipartito. Se ignora '
  'la dirección únicamente para recorrer conexiones: las flechas originales se mantienen '
  'desde estudiantes hacia casas. Si se exigiera seguirlas siempre hacia adelante, '
  'no se podría salir de una casa para llegar al otro estudiante.')
p('La longitud cuenta relaciones, no dulces. No existe una relación directa entre '
  'dos estudiantes y sí existen casas compartidas; por eso 2 es mínimo. Hay cinco '
  'caminos mínimos posibles de longitud 2, y shortestPath devuelve uno. OPTIONAL MATCH '
  'permitiría registrar p = null si no hubiera conexión. El límite de 24 es suficiente '
  'para un camino mínimo entre nodos distintos de un grafo de 25 nodos.')
p('Este recorrido representa conexiones por visitas compartidas. <b>No es una ruta '
  'geográfica ni determina el orden cronológico de las visitas</b>: el modelo no '
  'almacena coordenadas, distancias ni marcas de tiempo para deducirlo.')

heading('Parte 4 - Reflexión y liberación de la proyección')
p('Cypher identificó a Tomás como ganador al sumar 7 dulces y distinguió ese premio '
  'de las cinco visitas que realizan todos. Degree Centrality confirmó que cuatro '
  'casas son las más conectadas por visitas recibidas, con puntaje 9, mientras '
  'Node Similarity mostró que Isidora y Nicolás eligieron exactamente las mismas '
  'casas. La búsqueda de caminos hizo visible esa conexión mediante una casa '
  'compartida y una longitud mínima de dos relaciones. Así, la agregación de '
  'propiedades explica los premios y el análisis estructural explica los vínculos. '
  'Una limitación del modelo es que no registra la cronología ni la ubicación '
  'geográfica de las visitas; además, una conexión por sí sola no informa cuántos '
  'dulces produjo.')
code(25)
result(25, ['Proyección liberada'], ['graphName'], [495])
code(26)
result(26, ['¿Existe halloween?'], ['exists'], [495])
photo('04_cierre.jpg', 'Figura 4. Evidencia en Query de exists = false después de liberar '
      'la proyección.', (230, 112, 1265, 465), 190)
p('El cierre se realizó después de reunir los resultados y las capturas de los '
  'análisis. gds.graph.drop liberó únicamente la proyección en memoria. La base '
  'neo4j y los datos originales del respaldo se conservaron; los conteos finales '
  'continuaron en 15 estudiantes, 10 casas y 75 visitas.')
SimpleDocTemplate(str(OUT), pagesize=A4, rightMargin=48, leftMargin=48,
                  topMargin=44, bottomMargin=45,
                  title='Tarea 3 - Neo4j y análisis de grafos',
                  author='Diego Carlon; Joshua Serin').build(story, onFirstPage=footer, onLaterPages=footer)
print(OUT)

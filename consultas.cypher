// Tarea 3 - Neo4j y analisis de grafos
// Joshua Serin (202173644-1) y Diego Carlon (202173540-2).
// Ejecutar en la base restaurada desde tarea.dump, nunca en system.
// Estas consultas no modifican los datos originales.

// SETUP: versiones y nombre de la base.
CALL dbms.components() YIELD name, versions, edition
RETURN name, versions, edition;
RETURN gds.version() AS versionGDS;
CALL db.info() YIELD name RETURN name AS base;

// SETUP: comprobar 15 estudiantes, 10 casas y 75 visitas por separado.
MATCH (e:Estudiante) RETURN count(e) AS estudiantes;
MATCH (c:Casa) RETURN count(c) AS casas;
MATCH (:Estudiante)-[r:PIDIO_DULCES]->(:Casa) RETURN count(r) AS visitas;

// PARTE 1.1: grafo completo; tambien incluye nodos aislados.
MATCH (n) OPTIONAL MATCH (n)-[r:PIDIO_DULCES]->(m)
RETURN n, r, m;
// Propiedades de una visita para la interpretacion.
MATCH (e:Estudiante)-[r:PIDIO_DULCES]->(c:Casa)
RETURN e.id AS estudiante, c.id AS casa, c.direccion AS direccion,
       r.cantidad AS cantidad, r.tipo AS tipo
ORDER BY estudiante, casa LIMIT 1;

// PARTE 1.2: ranking de todas las casas, incluidas las que no tienen visitas.
MATCH (c:Casa) OPTIONAL MATCH (:Estudiante)-[r:PIDIO_DULCES]->(c)
RETURN c.id AS id, c.direccion AS direccion, count(r) AS visitas
ORDER BY visitas DESC, id;
// Todas las casas empatadas en el maximo.
MATCH (c:Casa) OPTIONAL MATCH (:Estudiante)-[r:PIDIO_DULCES]->(c)
WITH c, count(r) AS visitas
WITH collect({id:c.id, direccion:c.direccion, visitas:visitas}) AS ranking,
     max(visitas) AS maximo
UNWIND ranking AS fila
WITH fila, maximo WHERE fila.visitas = maximo
RETURN fila.id AS id, fila.direccion AS direccion, fila.visitas AS visitas
ORDER BY id;

// PARTE 1.3: ranking de estudiantes; contar visitas y sumar dulces.
MATCH (e:Estudiante) OPTIONAL MATCH (e)-[r:PIDIO_DULCES]->(:Casa)
RETURN e.id AS estudiante, count(r) AS visitas, sum(r.cantidad) AS dulces
ORDER BY dulces DESC, estudiante;
// Todos los estudiantes empatados en el maximo.
MATCH (e:Estudiante) OPTIONAL MATCH (e)-[r:PIDIO_DULCES]->(:Casa)
WITH e, count(r) AS visitas, sum(r.cantidad) AS dulces
WITH collect({estudiante:e.id, visitas:visitas, dulces:dulces}) AS ranking,
     max(dulces) AS maximo
UNWIND ranking AS fila
WITH fila, maximo WHERE fila.dulces = maximo
RETURN fila.estudiante AS estudiante, fila.visitas AS visitas, fila.dulces AS dulces
ORDER BY estudiante;

// PARTE 1.4: visitas sin dulces y porcentaje con aritmetica decimal.
MATCH (e:Estudiante)-[r:PIDIO_DULCES]->(c:Casa) WHERE r.cantidad = 0
RETURN e.id AS estudiante, c.direccion AS direccion, r.tipo AS tipo
ORDER BY estudiante, direccion;
MATCH (:Estudiante)-[r:PIDIO_DULCES]->(:Casa)
WITH count(r) AS total, sum(CASE WHEN r.cantidad = 0 THEN 1 ELSE 0 END) AS sinDulces
RETURN sinDulces, total,
       CASE WHEN total = 0 THEN 0.0 ELSE 100.0 * sinDulces / total END AS porcentaje;

// PARTE 2.1: ejecutar en una instancia sin una proyeccion halloween previa.
// Si se repite, ejecutar primero CALL gds.graph.drop('halloween', false).
CALL gds.graph.project('halloween', ['Estudiante', 'Casa'],
     {PIDIO_DULCES: {orientation: 'NATURAL'}})
YIELD graphName, nodeCount, relationshipCount
RETURN graphName, nodeCount, relationshipCount;

// PARTE 2.2: grado de entrada; filtrar casas despues del algoritmo.
CALL gds.degree.stream('halloween', {orientation:'REVERSE'})
YIELD nodeId, score
WITH gds.util.asNode(nodeId) AS casa, score WHERE casa:Casa
RETURN casa.id AS id, casa.direccion AS direccion, score
ORDER BY score DESC, id;
// Todos los maximos del grado de entrada.
CALL gds.degree.stream('halloween', {orientation:'REVERSE'})
YIELD nodeId, score
WITH gds.util.asNode(nodeId) AS casa, score WHERE casa:Casa
WITH collect({id:casa.id, direccion:casa.direccion, score:score}) AS ranking,
     max(score) AS maximo
UNWIND ranking AS fila
WITH fila, maximo WHERE fila.score = maximo
RETURN fila.id AS id, fila.direccion AS direccion, fila.score AS score
ORDER BY id;
// Comparacion directa de GDS y Cypher para las diez casas.
CALL gds.degree.stream('halloween', {orientation:'REVERSE'})
YIELD nodeId, score
WITH gds.util.asNode(nodeId) AS casa, score WHERE casa:Casa
OPTIONAL MATCH (:Estudiante)-[r:PIDIO_DULCES]->(casa)
RETURN casa.id AS id, casa.direccion AS direccion, score, count(r) AS visitas,
       score = count(r) AS coincide
ORDER BY score DESC, id;

// PARTE 2.3: cinco parejas distintas, desempate por nombres.
CALL gds.nodeSimilarity.stream('halloween', {
     similarityMetric:'JACCARD', topK:14, similarityCutoff:0.0001})
YIELD node1, node2, similarity
WITH gds.util.asNode(node1) AS a, gds.util.asNode(node2) AS b, similarity
WHERE a:Estudiante AND b:Estudiante AND a.id < b.id
RETURN a.id AS estudiante1, b.id AS estudiante2, similarity
ORDER BY similarity DESC, estudiante1, estudiante2 LIMIT 5;

// PARTE 2.3: casas compartidas por la pareja de maxima similitud.
MATCH (a:Estudiante {id:'Isidora'})-[:PIDIO_DULCES]->(c:Casa)
      <-[:PIDIO_DULCES]-(b:Estudiante {id:'Nicolás'})
RETURN c.id AS id, c.direccion AS direccion ORDER BY id;
// Conjuntos de vecinos, interseccion y union para verificar Jaccard.
MATCH (a:Estudiante {id:'Isidora'})-[:PIDIO_DULCES]->(ca:Casa)
WITH a, collect(DISTINCT ca.id) AS casasA
MATCH (b:Estudiante {id:'Nicolás'})-[:PIDIO_DULCES]->(cb:Casa)
WITH a, b, casasA, collect(DISTINCT cb.id) AS casasB
WITH a, b, casasA, casasB, [c IN casasA WHERE c IN casasB] AS comunes
RETURN a.id AS estudiante1, b.id AS estudiante2, casasA, casasB,
       size(comunes) AS interseccion,
       size(casasA) + size(casasB) - size(comunes) AS union,
       1.0 * size(comunes) / (size(casasA) + size(casasB) - size(comunes)) AS jaccard;
// Dulces y tipos de la pareja: similitud de visitas no equivale a igual premio.
MATCH (e:Estudiante)-[r:PIDIO_DULCES]->(c:Casa)
WHERE e.id IN ['Isidora', 'Nicolás']
RETURN e.id AS estudiante, c.id AS casa, c.direccion AS direccion,
       r.cantidad AS dulces, r.tipo AS tipo ORDER BY estudiante, casa;

// PARTE 3.1: patron completo de las cinco casas compartidas (vista grafica).
MATCH p=(a:Estudiante {id:'Isidora'})-[:PIDIO_DULCES]->(c:Casa)
      <-[:PIDIO_DULCES]-(b:Estudiante {id:'Nicolás'})
RETURN p ORDER BY c.id;
// PARTE 3.2: un camino minimo, su longitud y sus nodos, ignorando direccion.
MATCH (a:Estudiante {id:'Isidora'}), (b:Estudiante {id:'Nicolás'})
OPTIONAL MATCH p=shortestPath((a)-[:PIDIO_DULCES*1..24]-(b))
RETURN p, length(p) AS longitud, nodes(p) AS recorrido,
       [n IN nodes(p) | CASE WHEN n:Estudiante THEN n.id ELSE n.direccion END] AS nombres;

// PARTE 4: ejecutar SOLO despues de obtener todas las evidencias.
CALL gds.graph.drop('halloween', false) YIELD graphName RETURN graphName;
CALL gds.graph.exists('halloween') YIELD exists RETURN exists;

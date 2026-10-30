# Tarea 3 - Neo4j y análisis de grafos

Bases de Datos Avanzadas, INF325, segundo semestre de 2026.

- Joshua Serin: 202173644-1.
- Diego Carlon: 202173540-2.

## Entrega

- [Informe PDF](output/pdf/Carlon-Serin.pdf)
- [Consultas Cypher](consultas.cypher)
- [ZIP para Aula](output/Carlon-Serin.zip)

El ZIP contiene únicamente el informe y `consultas.cypher`. Las capturas están incluidas en el PDF.

## Ejecutar en otro computador

1. Clonar este repositorio.
2. Instalar Neo4j Desktop. El entorno verificado usa Desktop 2.3.0, Neo4j 2026.10.1 Enterprise y GDS 2026.10.1.
3. Descargar `tarea.dump` desde Aula; el respaldo no está incluido en el repositorio.
4. Crear una instancia desde ese respaldo, elegir una contraseña propia e instalar Graph Data Science desde Plugins. Reiniciar la instancia.
5. Abrir Connect > Query y seleccionar la base restaurada, no `system`.
6. Ejecutar `consultas.cypher` por separado y en orden. Crear la proyección antes de los algoritmos y liberarla al terminar.

Los conteos esperados son 15 estudiantes, 10 casas y 75 relaciones `PIDIO_DULCES`. No generar ni modificar los datos originales.

Los resultados numéricos deben coincidir. La disposición gráfica puede variar y `shortestPath` puede elegir otra de las cinco casas compartidas, manteniendo longitud 2.

## Archivos auxiliares

`evidencias/` conserva los resultados reales y las capturas originales. `generar_informe.py` genera el PDF y `verificar_consultas.py` ejecuta las consultas mediante el controlador de Neo4j. Estos scripts son auxiliares: no se necesitan para ejecutar las consultas desde Query.

Para usar los scripts se requiere Python con `neo4j`, `reportlab`, `Pillow` y una configuración local propia en `.local/conexion.json`. El generador del informe utiliza fuentes de Windows. Consultar también `GUIA_LOCAL.txt`.

Las credenciales locales, las dependencias descargadas, los temporales y los archivos `.dump` están excluidos mediante `.gitignore`.

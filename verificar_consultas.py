"""Ejecuta consultas.cypher y conserva resultados reales, sin alterar el caso."""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'herramientas' / 'pythonlibs'))
from neo4j import GraphDatabase
from neo4j.graph import Node, Relationship, Path as GraphPath


def encode(value):
    if isinstance(value, Node):
        return {'elementId': value.element_id, 'labels': sorted(value.labels),
                'properties': dict(value)}
    if isinstance(value, Relationship):
        return {'elementId': value.element_id, 'type': value.type,
                'start': value.start_node.element_id, 'end': value.end_node.element_id,
                'properties': dict(value)}
    if isinstance(value, GraphPath):
        return {'nodes': list(value.nodes), 'relationships': list(value.relationships),
                'length': len(value)}
    if hasattr(value, 'iso_format'):
        return value.iso_format()
    raise TypeError(type(value).__name__)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cierre', action='store_true')
    parser.add_argument('--desde', type=int, default=1)
    args = parser.parse_args()
    config = json.loads((ROOT / '.local' / 'conexion.json').read_text())
    source = (ROOT / 'consultas.cypher').read_text(encoding='utf-8')
    statements = [s.strip() for s in re.sub(r'//[^\n]*', '', source).split(';') if s.strip()]
    selected = list(enumerate(statements, 1))
    selected = selected[-2:] if args.cierre else selected[:-2]
    selected = [(n, q) for n, q in selected if n >= args.desde]
    output = ROOT / 'evidencias'
    output.mkdir(exist_ok=True)
    with GraphDatabase.driver(config['uri'], auth=(config['user'], config['password'])) as driver:
        driver.verify_connectivity()
        with driver.session(database=config['database']) as session:
            for number, query in selected:
                result = session.run(query)
                rows = [dict(record) for record in result]
                summary = result.consume()
                payload = {'numero': number, 'consulta': query, 'filas': rows,
                           'base': summary.database,
                           'tiempo_disponible_ms': summary.result_available_after,
                           'tiempo_consumido_ms': summary.result_consumed_after}
                (output / f'consulta_{number:02}.json').write_text(
                    json.dumps(payload, ensure_ascii=False, indent=2, default=encode), encoding='utf-8')
                print(f'Consulta {number:02}: {len(rows)} filas')
                if len(rows) <= 5 and not any(isinstance(v, (Node, Relationship, GraphPath))
                                              for row in rows for v in row.values()):
                    print(json.dumps(rows, ensure_ascii=False, default=encode))


if __name__ == '__main__':
    main()

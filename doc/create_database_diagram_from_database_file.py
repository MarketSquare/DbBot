import re
import sqlite3
import sys

from os.path import abspath, basename, dirname, join, splitext

try:
  import pydot
except ImportError:
  print '''You need to have pydot and Graphviz installed.

To install Graphviz:
http://www.graphviz.org/Download.php

OR:

Use your OS's package manager.

To install pydot:
$ pip install pydot
'''

DOT_DEFAULTS = {
  'graph_type': 'digraph',
  'compound': 'true',
  'rankdir': 'LR'
}

GRAPH_DEFAULTS = {
  'fontsize': '12.0',
  'fontname': 'times-bold',
  'style': 'filled',
  'fillcolor': 'azure2'
}

NODE_DEFAULTS = {
  'shape': 'box',
  'fontsize': '8.0',
  'style': 'filled',
  'fillcolor': 'white'
}

EDGE_DEFAULTS = {
  'fontsize': '8.0'
}

def print_usage():
  print '''Usage: python create_database_diagram_from_database_file.py [databasefile]
'''

def get_indeces(string):
  paren_index = string.find('(')
  return (string.rfind(',', 0, paren_index) + 2, 
          string.find(')', paren_index, len(string)) + 1)

def handle_constraint_fields(string, fields):
  if '(' in string:
    start_index, end_index = get_indeces(string) 
    fields.append(string[start_index:end_index])
    string = string[0:start_index] + string[end_index:]
    string, fields = handle_constraint_fields(string, fields) 
  return string, fields

def split_foreign_keys_and_rest(string):
  fks = []
  string, fields = handle_constraint_fields(string, [])
  for token in string.split(', '):
    if not token:
      continue
    if token.find('REFERENCES') == -1:
      l = fields
    else:
      l = fks
    l.append(token)
  return {'fields': fields, 'fks':fks}


def get_schema(db_file):
  with sqlite3.connect(db_file) as conn:
    c = conn.cursor()
    return [row[0] for row in c.execute("SELECT sql FROM sqlite_master WHERE type='table'")]

def organize_rows(sql_lines):
  data = {}
  for line in sql_lines:
    if line.startswith('CREATE TABLE'):
      m = re.match('CREATE TABLE (\w+) \((.*)\)', line)
      if m:
        data[m.group(1)] = split_foreign_keys_and_rest(m.group(2))
  return data

def populate_nodes_and_clusters(data, graph):
  for table_name, value in data.iteritems():
    node = pydot.Node('\n'.join(value['fields']))
    cluster = pydot.Cluster(table_name, label=table_name)
    cluster.add_node(node)
    graph.add_subgraph(cluster)
    data[table_name]['node'] = node
    data[table_name]['cluster'] = cluster

def populate_edges(data, graph):
  for table_data in data.itervalues():
    for fk in table_data['fks']:
      target = fk.split(' REFERENCES ')[1]
      target_name = fk.split()[0]
      graph.add_edge(pydot.Edge(table_data['node'], 
                                data[target]['node'], 
                                label=target_name,
                                ltail=table_data['cluster'].get_name(),
                                lhead=data[target]['cluster'].get_name()))

def create_graph(data):
  graph = pydot.Dot(**DOT_DEFAULTS) 
  graph.set_graph_defaults(**GRAPH_DEFAULTS)
  graph.set_node_defaults(**NODE_DEFAULTS)
  graph.set_edge_defaults(**EDGE_DEFAULTS)
  populate_nodes_and_clusters(data, graph)
  populate_edges(data, graph)
  return graph

if __name__ == '__main__':
  if len(sys.argv) < 2:
    print_usage()
    sys.exit(1)
  file_name = sys.argv[1]
  data = organize_rows(get_schema(file_name))
  file_name = splitext(basename(file_name))[0]
  graph = create_graph(data)
  graph.write_png('%s.png' % file_name)
  print 'DONE'



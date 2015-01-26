from geosolver.ontology.states import Type, OntologyPath
from geosolver.ontology.states import Function
from geosolver.ontology.states import BasicOntology

__author__ = 'minjoon'


def get_ontology_path_cost(ontology_path):
    """
    In general, penalty = number of functions implied. (excluding start and end)
    However, penalty differs to prioritize some implications.

    Concretely,

    (number) -> [lengthOf ->] (line): -0.5
    (line) -> [line -> (reference) ->] AB: -0.5
    (point) -> [point -> (reference) ->] E: -0.5
    (number) -> [angleOf:arc ->] (arc): -0.5
    (number) -> [angleOf:angle ->] (angle): -0.5
    (truth) -> [exists ->] (entity): -1

    :param ontology_path:
    :return:
    """
    assert isinstance(ontology_path, OntologyPath)
    cost = 0
    basic_ontology = ontology_path.basic_ontology


    for idx, node in enumerate(ontology_path.path_nodes[:-1]):
        if not isinstance(node, Function):
            continue
        nn_node = ontology_path.path_nodes[idx+2]
        if idx == 0:
            if basic_ontology.isinstance(node.return_type, basic_ontology.types['entity']):
                if node.name == 'point':
                    if len(nn_node.name) == 1:
                        cost += 1
                    else:
                        cost += 100
                elif node.name == 'line':
                    if len(nn_node.name) > 1:
                        cost += 1
                    else:
                        cost += 100
                elif node.name == 'quadrilateral':
                    if len(nn_node.name) == 4:
                        cost += 1
                    else:
                        cost += 100
                elif node.name == 'triangle':
                    if len(nn_node.name) == 3:
                        cost += 1
                    else:
                        cost += 100
                elif node.name == 'circle':
                    if len(nn_node.name) == 1:
                        cost += 1
                    else:
                        cost += 100
                elif node.name == 'arc':
                    if len(nn_node.name) == 2:
                        cost += 1
                    else:
                        cost += 100
                elif node.name == 'angle':
                    if len(nn_node.name) in [1,3]:
                        cost += 1
                    else:
                        cost += 100
                else:
                    cost += 1
            else:
                cost += 1
        else:
            if node.name in ['?number', '?truth', 'lengthOf', 'angleOf:arc', 'angleOf:angle']:
                cost += 2
            else:
                cost += 100

    return cost

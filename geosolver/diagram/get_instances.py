import itertools
from geosolver.diagram.computational_geometry import angle_in_radian
from geosolver.diagram.states import GraphParse
from geosolver.ontology.instantiator_definitions import instantiators
from geosolver.text2.ontology import FormulaNode, function_signatures

__author__ = 'minjoon'


def get_instances(graph_parse, instance_type_name, is_variable=False, *args):
    assert instance_type_name in instantiators
    if instance_type_name in ["triangle", "quad"]:
        return _get_polygons(graph_parse, instance_type_name, is_variable, *args)
    else:
        return eval("_get_%ss(graph_parse, is_variable, *args)" % instance_type_name)


def get_all_instances(graph_parse, instance_type_name, is_variable=False):
    assert instance_type_name in instantiators
    if instance_type_name in ["triangle", "quad", "hexagon"]:
        if instance_type_name == 'triangle': n = 3
        elif instance_type_name == 'quad': n = 4
        elif instance_type_name == 'hexagon': n = 6
        return _get_all_polygons(graph_parse, instance_type_name, n, is_variable)
    else:
        return eval("_get_all_%ss(graph_parse, is_variable)" % instance_type_name)


def _get_points(graph_parse, is_variable, key):
    if key in graph_parse.intersection_points:
        if is_variable:
            return {key: graph_parse.core_parse.point_variables[key]}
        else:
            return {key: graph_parse.intersection_points[key]}
    else:
        return {}


def _get_all_points(graph_parse, is_variable):
    items = []
    for key in graph_parse.intersection_points.keys():
        items.extend(_get_points(graph_parse, is_variable, key).iteritems())
    return dict(items)


def _get_lines(graph_parse, is_variable, a_key, b_key):
    assert isinstance(graph_parse, GraphParse)
    if graph_parse.line_graph.has_edge(a_key, b_key):
        if is_variable:
            line = graph_parse.line_graph[a_key][b_key]['variable']
        else:
            line = graph_parse.line_graph[a_key][b_key]['instance']
        return {(a_key, b_key): line}
    else:
        return {}


def _get_all_lines(graph_parse, is_variable):
    assert isinstance(graph_parse, GraphParse)
    items = []
    for a_key, b_key in graph_parse.line_graph.edges():
        items.extend(_get_lines(graph_parse, is_variable, a_key, b_key).iteritems())
    return dict(items)


def _get_circles(graph_parse, is_variable, center_key):
    assert isinstance(graph_parse, GraphParse)
    if center_key in graph_parse.circle_dict:
        circles = {}
        for radius_key, d in graph_parse.circle_dict[center_key].iteritems():
            if is_variable:
                circle = d['variable']
            else:
                circle = d['instance']
            circles[(center_key, radius_key)] = circle
        return circles
    else:
        return {}


def _get_all_circles(graph_parse, is_variable):
    assert isinstance(graph_parse, GraphParse)
    items = []
    for center_key in graph_parse.circle_dict:
        items.extend(_get_circles(graph_parse, is_variable, center_key).iteritems())
    return dict(items)


def _get_arcs(graph_parse, is_variable, a_key, b_key):
    assert isinstance(graph_parse, GraphParse)
    arcs = {}
    for circle_key in _get_all_circles(graph_parse):
        if graph_parse.arc_graphs[circle_key].has_edge(a_key, b_key):
            if is_variable:
                arc = graph_parse.arc_graphs[circle_key][a_key][b_key]['variable']
            else:
                arc = graph_parse.arc_graphs[circle_key][a_key][b_key]['instance']
            arc_key = (circle_key, a_key, b_key)
            arcs[arc_key] = arc
    return arcs


def _get_all_arcs(graph_parse, is_variable):
    assert isinstance(graph_parse, GraphParse)
    items = []
    for a_key, b_key in itertools.permutations(graph_parse.intersection_points, 2):
        items.extend(_get_arcs(graph_parse, is_variable, a_key, b_key).iteritems())
    return dict(items)

def _get_polygons(graph_parse, name, is_variable, *args):
    # TODO : include ignore_trivial parameter. This ignores area-0 polygons.
    assert isinstance(graph_parse, GraphParse)
    line_graph = graph_parse.line_graph
    if all(line_graph.has_edge(args[idx-1], arg) for idx, arg in enumerate(args)):
        if is_variable:
            points = tuple(graph_parse.core_parse.point_variables[key] for key in args)
        else:
            points = tuple(graph_parse.intersection_points[key] for key in args)
        polygon = instantiators[name](*points)
        polygon_key = tuple(args)
        return {polygon_key: polygon}
    else:
        return {}

def _get_all_polygons(graph_parse, name, n, is_variable):
    polygons = {}
    frozensets = set()
    line_graph = graph_parse.line_graph
    for keys in itertools.permutations(graph_parse.intersection_points, n):
        if frozenset(keys) in frozensets:
            continue
        if not all(line_graph.has_edge(keys[idx-1], key) for idx, key in enumerate(keys)):
            continue

        angles = []
        for idx, key in enumerate(keys):
            angles.extend(_get_angles(graph_parse, False, keys[idx-2], keys[idx-1], key).values())
        if len(angles) < n:
            continue

        if is_variable:
            points = tuple(graph_parse.core_parse.point_variables[key] for key in keys)
        else:
            points = tuple(graph_parse.intersection_points[key] for key in keys)
        polygon = instantiators[name](*points)
        polygon_key = tuple(keys)
        polygons[polygon_key] = polygon
        frozensets.add(frozenset(keys))
    return polygons



def _get_angles(graph_parse, is_variable, a_key, b_key, c_key, ignore_trivial=True):
    assert isinstance(graph_parse, GraphParse)
    line_graph = graph_parse.line_graph
    if line_graph.has_edge(a_key, b_key) and line_graph.has_edge(b_key, c_key):
        if ignore_trivial:
            # line_a = line_graph[b_key][a_key]['instance']
            a_points = line_graph[b_key][a_key]['points']
            # line_c = line_graph[b_key][c_key]['instance']
            c_points = line_graph[b_key][c_key]['points']
            if c_key in a_points or a_key in c_points:
                return {}
            if line_graph.has_edge(a_key, c_key):
                """
                Removes flat angle (180 degrees)
                """
                b_points = line_graph[a_key][c_key]['points']
                if b_key in b_points:
                    return {}

        if is_variable:
            points = graph_parse.core_parse.point_variables
        else:
            points = graph_parse.intersection_points
        a, b, c = points[a_key], points[b_key], points[c_key]
        angle = instantiators['angle'](a, b, c)
        angle_key = (a_key, b_key, c_key)
        return {angle_key: angle}
    else:
        return {}

def _get_all_angles(graph_parse, is_variable, ignore_trivial=True):
    """
    If ignore_trival is set to true, then 0 degree / 360 degree angles are not considered.
    :param graph_parse:
    :param ignore_trival:
    :return:
    """
    assert isinstance(graph_parse, GraphParse)
    items = []
    for a_key, b_key, c_key in itertools.permutations(graph_parse.intersection_points, 3):
        items.extend(_get_angles(graph_parse, is_variable, a_key, b_key, c_key, ignore_trivial=ignore_trivial).iteritems())
    return dict(items)

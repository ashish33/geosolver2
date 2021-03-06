import networkx as nx

__author__ = 'minjoon'


class Signature(object):
    def __init__(self, id_, return_type, valence, name=None):
        self.id = id_
        self.return_type = return_type
        if name is None:
            if isinstance(id_, str):
                name = id_
            else:
                name = repr(id_)
        self.name = name
        self.valence = valence

    def __eq__(self, other):
        assert isinstance(other, Signature)
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

class FunctionSignature(Signature):
    def __init__(self, id_, return_type, arg_types, arg_pluralities=None, is_symmetric=False, name=None):
        super(FunctionSignature, self).__init__(id_, return_type, len(arg_types), name=name)
        self.arg_types = arg_types
        if arg_pluralities is None:
            arg_pluralities = (False,) * len(arg_types)
        self.arg_pluralities = arg_pluralities
        self.is_symmetric = is_symmetric
        self.valence = len(arg_types)

    def __repr__(self):
        return self.name



class VariableSignature(Signature):
    def __init__(self, id_, return_type, name=None):
        super(VariableSignature, self).__init__(id_, return_type, 0, name=name)

    def __repr__(self):
        return self.name


class FormulaNode(object):
    def __init__(self, signature, children):
        self.signature = signature
        self.children = children
        self.return_type = signature.return_type

    def is_leaf(self):
        return len(self.children) == 0

    def replace_signature(self, tester, getter):
        """
        iterate through all formula nodes and if tester(signature) is true,
         then replace_signature it with getter(signature).
        :param function tester:
        :param function getter:
        :return:
        """
        new_sig = self.signature
        args = [child.replace_signature(tester, getter) for child in self.children]
        if tester(self.signature):
            new_sig = getter(self.signature)
        return FormulaNode(new_sig, args)

    def replace_node(self, tester, getter):
        if tester(self):
            return getter(self)
        else:
            args = [child.replace_node(tester, getter) for child in self.children]
            return FormulaNode(self.signature, args)


    def __add__(self, other):
        current = function_signatures['Add']
        return FormulaNode(current, [self, other])

    def __radd__(self, other):
        current = function_signatures['Add']
        return FormulaNode(current, [other, self])

    def __mul__(self, other):
        current = function_signatures['Mul']
        return FormulaNode(current, [self, other])

    def __rmul__(self, other):
        current = function_signatures['Mul']
        return FormulaNode(current, [other, self])

    def __sub__(self, other):
        current = function_signatures['Sub']
        return FormulaNode(current, [self, other])

    def __rsub__(self, other):
        current = function_signatures['Sub']
        return FormulaNode(current, [other, self])

    def __div__(self, other):
        current = function_signatures['Div']
        return FormulaNode(current, [self, other])

    def __rdiv__(self, other):
        current = function_signatures['Div']
        return FormulaNode(current, [other, self])

    def __pow__(self, power, modulo=None):
        current = function_signatures['Pow']
        return FormulaNode(current, [self, power])

    def __rpow__(self, power, modulo=None):
        current = function_signatures['Pow']
        return FormulaNode(current, [power, self])

    def __eq__(self, other):
        current = function_signatures['Equals']
        return FormulaNode(current, [self, other])

    def __ge__(self, other):
        current = function_signatures['Ge']
        return FormulaNode(current, [self, other])

    def __lt__(self, other):
        current = function_signatures['Lt']
        return FormulaNode(current, [self, other])

    def __repr__(self):
        if self.is_leaf():
            return repr(self.signature)
        else:
            return "%r(%s)" % (self.signature, ",".join(repr(child) for child in self.children))


class SetNode(object):
    def __init__(self, children, head_index=0):
        self.children = children
        self.head = children[head_index]

    def is_singular(self):
        return len(self.children) == 1

    def is_plural(self):
        return len(self.children) > 1

    def __repr__(self):
        return "{%s}" % ",".join(repr(child) for child in self.children)

    def replace_node(self, tester, getter):
        if tester(self):
            return getter(self)
        else:
            args = [child.replace_node(tester, getter) for child in self.children]
            return SetNode(self.signature, args)


types = ('root', 'truth', 'number', 'entity', 'line', 'circle', 'triangle', 'quad', 'polygon')
type_inheritances = (
    ('root', 'truth'),
    ('root', 'number'),
    ('root', 'entity'),
    ('entity', 'point'),
    ('entity', '1d'),
    ('1d', 'line'),
    ('1d', 'angle'),
    ('1d', 'arc'),
    ('entity', '2d'),
    ('2d', 'polygon'),
    ('2d', 'circle'),
    ('polygon', 'triangle'),
    ('polygon', 'quad'),
    ('polygon', 'hexagon'),

)
type_graph = nx.DiGraph()
for parent, child in type_inheritances:
    type_graph.add_edge(parent, child)


def issubtype(child_type, parent_type):
    return nx.has_path(type_graph, parent_type, child_type)

function_signature_tuples = (
    ('Not', 'truth', ['truth']),
    ('True', 'truth', ['truth']),
    ('IsLine', 'truth', ['line']),
    ('IsPoint', 'truth', ['point']),
    ('IsCircle', 'truth', ['circle']),
    ('IsTriangle', 'truth', ['triangle']),
    ('IsQuad', 'truth', ['quad']),
    ('IsRectangle', 'truth', ['quad']),
    ('IsTrapezoid', 'truth', ['quad']),
    ('IsPolygon', 'truth', ['polygon']),
    ('IsRegular', 'truth', ['polygon']),
    ('Point', 'point', ['number', 'number']),
    ('Line', 'line', ['point', 'point'], None, True),
    ('Arc', 'arc', ['circle', 'point', 'point']),
    ('Circle', 'line', ['point', 'number']),
    ('Angle', 'angle', ['point', 'point', 'point']),
    ('Triangle', 'triangle', ['point', 'point', 'point']),
    ('Quad', 'quad', ['point', 'point', 'point', 'point']),
    ('Arc', 'arc', ['circle', 'point', 'point']),
    ('Polygon', 'polygon', ['*point']),
    ('Hexagon', 'hexagon', ['point', 'point', 'point', 'point', 'point', 'point']),
    ('IntersectionOf', 'point', ['entity', 'entity'], None, True),
    ('Is', 'truth', ['root', 'root'], None, True),
    ('Equals', 'truth', ['number', 'number']),
    ('Add', 'number', ['number', 'number'], None, True),
    ('Mul', 'number', ['number', 'number'], None, True),
    ('Sub', 'number', ['number', 'number']),
    ('Div', 'number', ['number', 'number']),
    ('Pow', 'number', ['number', 'number']),
    ('Ge', 'truth', ['number', 'number']),
    ('What', 'number', []),
    ('ValueOf', 'number', ['number']),
    ('IsInscribedIn', 'truth', ['polygon', 'circle']),
    ('IsCenterOf', 'truth', ['point', '2d']),
    ('IsDiameterLineOf', 'truth', ['line', 'circle']),
    ('DegreeMeasureOf', 'number', ['angle']),
    ('IsAngle', 'truth', ['angle']),
    ('Equilateral', 'truth', ['triangle']),
    ('Isosceles', 'truth', ['triangle']),
    ('IsSquare', 'truth', ['quad']),
    ('IsRight', 'truth', ['triangle']),
    ('AreaOf', 'number', ['2d']),
    ('IsAreaOf', 'truth', ['number', '2d']),
    ('IsLengthOf', 'truth', ['number', 'line']),
    ('IsRectLengthOf', 'truth', ['number', 'quad']),
    ('IsDiameterNumOf', 'truth', ['number', 'circle']),
    ('IsSideOf', 'truth', ['number', 'quad']),
    ('PerimeterOf', 'number', ['polygon']),
    ('IsMidpointOf', 'truth', ['point', 'line']),
    ('IsWidthOf', 'truth', ['number', 'quad']),
    ('LengthOf', 'number', ['line']),
    ('CC', 'truth', ['root', 'root'], None, True),
    ('Is', 'truth', ['entity', 'entity'], None, True),
    ('MeasureOf', 'number', ['angle']),
    ('Perpendicular', 'truth', ['line', 'line'], None, True),
    ('IsChordOf', 'truth', ['line', 'circle']),
    ('Tangent', 'truth', ['line', 'circle']),
    ('RadiusNumOf', 'number', ['circle']),
    ('IsRadiusNumOf', 'truth', ['number', 'circle']),
    ('IsRadiusLineOf', 'truth', ['line', 'circle']),
    ('PointLiesOnLine', 'truth', ['point', 'line']),
    ('PointLiesOnCircle', 'truth', ['point', 'circle']),
    ('Sqrt', 'number', ['number']),
    ('Parallel', 'truth', ['line', 'line'], None, True),
    ('IntersectAt', 'truth', ['*line', 'point']),
    ('Two', 'truth', ['*entity']),
    ('Three', 'truth', ['*entity']),
    ('Five', 'truth', ['*entity']),
    ('Six', 'truth', ['*entity']),
    ('BisectsAngle', 'truth', ['line', 'angle']),
    ('WhichOf', 'root', ['*root']),
    ('Following', '*root', []),
    ('What', 'number', []),
    ('AverageOf', 'number', ['*number']),
    ('SumOf', 'number', ['*number']),
    ('Twice', 'number', ['number']),
    ('RatioOf', 'number', ['number', 'number']),
    ('Integral', 'truth', ['number']),
    ('SquareOf', 'number', ['number']),
)

abbreviations = {
    '+': 'Add',
    '-': 'Sub',
    '*': 'Mul',
    '/': 'Div',
    ':': 'Div',
    '=': 'Equals',
    '<': 'Ge',
    '^': 'Pow',
    '\\sqrt': 'Sqrt',
    '||': 'Parallel',
}

def get_function_signatures():
    local_function_signatures = {}
    for tuple_ in function_signature_tuples:
        if len(tuple_) == 3:
            id_, return_type, arg_types = tuple_
            function_signature = FunctionSignature(id_, return_type, arg_types)
        elif len(tuple_) == 5:
            id_, return_type, arg_types, arg_pluralities, is_symmetric = tuple_
            function_signature = FunctionSignature(id_, return_type, arg_types, arg_pluralities, is_symmetric)
        local_function_signatures[id_] = function_signature
    return local_function_signatures

function_signatures = get_function_signatures()
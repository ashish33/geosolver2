import itertools
import numpy as np
import scipy
import networkx as nx

__author__ = 'minjoon'


class FunctionSignature(object):
    def __init__(self, name, return_type, arg_types):
        self.name = name
        self.return_type = return_type
        self.arg_types = arg_types

    def is_leaf(self):
        return len(self.arg_types) == 0

    def is_unary(self):
        return len(self.arg_types) == 1

    def is_binary(self):
        return len(self.arg_types) == 2

    def __hash__(self):
        return hash((self.name, self.return_type, tuple(self.arg_types)))

    def __repr__(self):
        return "%s %s(%s)" % (self.return_type, self.name, ", ".join(self.arg_types))


def add_function_signature(signatures, signature_tuple):
    name, return_type, arg_types = signature_tuple
    assert name not in signatures
    signatures[name] = FunctionSignature(name, return_type, arg_types)


types = ['start', 'number', 'modifier', 'circle', 'line', 'truth']
function_signatures = {}
tuples = (
    ('StartTruth', 'start', ['truth']),
    ('RadiusOf', 'number', ['circle']),
    ('Equal', 'truth', ['number', 'number']),
    ('Circle', 'circle', ['modifier']),
)
for tuple_ in tuples:
    add_function_signature(function_signatures, tuple_)


class Node(object):
    def __init__(self, function_signature, children):
        assert isinstance(function_signature, FunctionSignature)
        for child in children:
            assert isinstance(child, Node)

        self.function_signature = function_signature
        self.children = children

    def __hash__(self):
        return hash((self.function_signature, tuple(self.children)))


class TagRule(object):
    def __init__(self, words, syntax_tree, index, signature):
        self.words = words
        self.syntax_tree = syntax_tree
        self.index = index
        self.signature = signature

    def __repr__(self):
        return "%r->%s" % (self.index, self.signature.name)


class DeterministicTagModel(object):
    def __init__(self, tag_rules, feature_function):
        pass

    def get_tag_distribution(self, words, syntax_tree, index):
        """
        Returns a dictionary of signature:probability pair
        :param words:
        :param syntax_tree:
        :param index:
        :return:
        """

    def get_best_tag(self, words, syntax_tree, index):
        if words[index] == 'radius':
            return function_signatures['RadiusOf'], 0.0
        elif words[index] == 'circle':
            return function_signatures['Circle'], 0.0
        elif words[index] == 'O':
            return FunctionSignature('O', 'modifier', []), 0.0
        elif words[index] == '5':
            return FunctionSignature('5', 'number', []), 0.0
        else:
            return None, 0.0

    def get_best_tags(self, words, syntax_tree):
        tags = {index: self.get_best_tag(words, syntax_tree, index) for index in words.keys()}
        return tags



class UnaryRule(object):
    def __init__(self, words, syntax_tree, tags, parent_index, parent_signature, child_index, child_signature):
        self.words = words
        self.syntax_tree = syntax_tree
        self.tags = tags
        self.parent_index = parent_index
        self.parent_signature = parent_signature
        self.child_index = child_index
        self.child_signature = child_signature

    def __hash__(self):
        return hash((self.parent_index, self.parent_signature, self.child_index, self.child_signature))

    def __repr__(self):
        return "%s@%r->%s@%r" % (self.parent_signature.name, self.parent_index,
                                 self.child_signature.name, self.child_index)


class BinaryRule(object):
    def __init__(self, words, syntax_tree, tags,
                 parent_index, parent_signature, a_index, a_signature, b_index, b_signature):
        self.words = words
        self.syntax_tree = syntax_tree
        self.tags = tags
        self.parent_index = parent_index
        self.parent_signature = parent_signature
        self.a_index = a_index
        self.a_signature = a_signature
        self.b_index = b_index
        self.b_signature = b_signature

    def __hash__(self):
        return hash((self.parent_index, self.parent_signature,
                     self.a_index, self.a_signature, self.b_index, self.b_signature))

    def __repr__(self):
        return "%s@%r->%s@%r|%s@%r" % (self.parent_signature.name, self.parent_index,
                                        self.a_signature.name, self.a_index,
                                        self.b_signature.name, self.b_index)


def uff1(unary_rule):
    # For now, just distance between them in dependency tree and sentence and their product
    assert isinstance(unary_rule, UnaryRule)
    if unary_rule.parent_index is not None and unary_rule.child_index is not None:
        f1 = nx.shortest_path_length(unary_rule.syntax_tree, unary_rule.parent_index, unary_rule.child_index)
        f2 = abs(unary_rule.parent_index - unary_rule.child_index)
    else:
        f1 = len(unary_rule.words)/2.0
        f2 = f1
    f3 = np.sqrt(f1*f2)
    return np.array([f1, f2, f3])


def bff1(binary_rule):
    """
    binary feature function version 1
    Usually, this will depend on unary feature function.

    :param binary_rule:
    :return:
    """
    assert isinstance(binary_rule, BinaryRule)
    unary_rule_a = UnaryRule(binary_rule.words, binary_rule.syntax_tree, binary_rule.tags, binary_rule.parent_index,
                             binary_rule.parent_signature, binary_rule.a_index, binary_rule.a_signature)
    unary_rule_b = UnaryRule(binary_rule.words, binary_rule.syntax_tree, binary_rule.tags, binary_rule.parent_index,
                             binary_rule.parent_signature, binary_rule.b_index, binary_rule.b_signature)
    if binary_rule.a_index is not None and binary_rule.b_index is not None:
        f1 = nx.shortest_path_length(binary_rule.syntax_tree, binary_rule.a_index, binary_rule.b_index)
        f2 = abs(binary_rule.a_index - binary_rule.b_index)
    else:
        f1 = len(binary_rule.words)/2.0
        f2 = f1
    f3 = np.sqrt(f1*f2)

    a1 = uff1(unary_rule_a)
    a2 = uff1(unary_rule_b)
    a3 = [f1, f2, f3]

    return np.array(list(itertools.chain(a1, a2, a3)))


class SemanticModel(object):
    def __init__(self, feature_function, initial_weights):
        self.feature_function = feature_function
        self.weights = initial_weights

    def optimize_weights(self, rules, reg_const):
        """
        Obtain weights that maximizes the likelihood of the unary rules
        Log linear model with L2 regularization (ridge)
        Use BFGS for gradient descent
        Update the self.weights

        :param rules:
        :param reg_const:
        :return:
        """
        def loss_function(weights):
            model = self.__class__(self.feature_function, weights)
            return sum(model.get_log_prob(rule) for rule in rules) - \
                   0.5*reg_const*np.dot(weights, weights)

        def grad_function(weights):
            model = self.__class__(self.feature_function, weights)
            return sum(model.get_log_grad(rule) for rule in rules) - reg_const*weights

        negated_loss = lambda weights: -loss_function(weights)
        negated_grad = lambda weights: -grad_function(weights)

        optimized_weights = scipy.optimize.minimize(negated_loss, self.weights, method='BFGS', jac=negated_grad)
        self.weights = optimized_weights

    def get_log_distribution(self, words, syntax_tree, tags, parent_index, parent_signature, excluding_indices=()):
        """
        dictionary of unary_rule : log probability pair
        The distribution must be well defined, i.e. must sum up to 1.
        To be implemented by the inheriting class

        :param words:
        :param syntax:
        :param tags:
        :param parent_index:
        :param parent_signature:
        :return:
        """
        distribution = {}
        local_unary_rules = self.get_possible_rules(words, syntax_tree, tags, parent_index, parent_signature,
                                                    excluding_indices)
        for unary_rule in local_unary_rules:
            features = self.feature_function(unary_rule)
            numerator = np.dot(self.weights, features)
            distribution[unary_rule] = numerator

        normalized_distribution = log_normalize(distribution)

        return normalized_distribution

    def get_log_prob(self, rule, excluding_indices=()):
        assert isinstance(rule, UnaryRule)
        distribution = self.get_log_distribution(rule.words, rule.tags, rule.parent_index,
                                                 rule.parent_signature, excluding_indices)
        if rule in distribution:
            return distribution[rule]

        return -np.inf

    def get_log_grad(self, rule, excluding_indices=()):
        distribution = self.get_log_distribution(rule.words, rule.tags, rule.parent_index,
                                                 rule.parent_signature, excluding_indices)
        log_grad = self.feature_function(rule) - sum(np.exp(logp) * self.feature_function(each_rule)
                                                     for each_rule, logp in distribution.iteritems())
        return log_grad

    def get_possible_rules(self, words, syntax_tree, tags, parent_index, parent_signature, excluding_indices=()):
        """
        NEED TO BE OVERRIDDEN
        Need to enforce type-matching here! That is, get only rules consistent with the ontology.
        (perhaps remove equivalent rules. For instance, equality. but this might be bad.. or add symmetry feature)

        :param words:
        :param syntax_tree:
        :param tags:
        :param parent_index:
        :param parent_signature:
        :param excluding_indices:
        :return list:
        """
        assert False
        return []


def log_normalize(distribution):
    sum_value = sum(logp for _, logp in distribution)
    normalized_distribution = {key: value-sum_value for key, value in distribution.iteritems()}
    return normalized_distribution


class UnarySemanticModel(SemanticModel):
    def get_possible_rules(self, words, syntax_tree, tags, parent_index, parent_signature, excluding_indices=()):
        assert isinstance(parent_signature, FunctionSignature)
        assert parent_signature.is_unary()
        excluding_indices = set(excluding_indices)
        excluding_indices.add(parent_index)
        available_indices = set(words.keys()).difference(excluding_indices).union(function_signatures.values())
        rules = []
        for child_index in available_indices:
            if isinstance(child_index, int):
                child_signature = tags[child_index]
            else:
                assert isinstance(child_index, FunctionSignature)
                child_signature = child_index
                child_index = None
            if parent_signature.arg_types[0] == child_signature.return_type:
                # ontology enforcement
                rule = UnaryRule(words, syntax_tree, tags, parent_index, parent_signature, child_index, child_signature)
                rules.append(rule)
        return rules


class BinarySemanticModel(SemanticModel):
    def get_possible_rules(self, words, syntax_tree, tags, parent_index, parent_signature, excluding_indices=()):
        assert isinstance(parent_signature, FunctionSignature)
        assert parent_signature.is_binary()
        excluding_indices = set(excluding_indices)
        excluding_indices.add(parent_index)
        available_indices = set(words.keys()).difference(excluding_indices).union(function_signatures.values())
        rules = []
        for a_index, b_index in itertools.permutations(available_indices, 2):
            # i.e. argument order matters, but no duplicate (this might not be true in future)
            if isinstance(a_index, int):
                a_signature = tags[a_index]
            else:
                a_signature = a_index
                a_index = None
            if isinstance(b_index, int):
                b_signature = tags[b_index]
            else:
                b_signature = b_index
                b_index = None
            if tuple(parent_signature.arg_types) == (a_signature.return_type, b_signature.return_type):
                # ontology enforcement
                rule = BinaryRule(words, syntax_tree, tags, parent_index, parent_signature,
                                  a_index, a_signature, b_index, b_signature)
                rules.append(rule)
        return rules


class TopDownNaiveDecoder(object):
    def __init__(self, unary_semantic_model, binary_semantic_model):
        assert isinstance(unary_semantic_model, UnarySemanticModel)
        assert isinstance(binary_semantic_model, BinarySemanticModel)
        self.unary_semantic_model = unary_semantic_model
        self.binary_semantic_model = binary_semantic_model

    def get_formula_distribution(self, words, syntax_tree, tags):
        """
        Returns a fully-grounded node : probability pair
        In naive case, this will be well-defined.

        :param words:
        :param syntax_tree:
        :param tags:
        :return:
        """

        # TODO : enforce non-redundancy within formula
        # TODO : since this is top-down, no syntactic feature for implied functions. Reweight formulas in another method

        def _recurse_unary(unary_rule, excluding_indices):
            assert isinstance(unary_rule, UnaryRule)
            assert isinstance(excluding_indices, set)
            excluding_indices = excluding_indices.union({unary_rule.parent_index})

            if unary_rule.child_signature.is_leaf():
                child_nodes = {Node(unary_rule.child_signature, []): 0}
            elif unary_rule.child_signature.is_unary():
                distribution = self.unary_semantic_model.get_log_distribution(words, syntax_tree, tags,
                    unary_rule.child_index, unary_rule.child_signature, excluding_indices)
                child_nodes = {node: logp + logq
                               for current_unary_rule, logp in distribution.iteritems()
                               for node, logq in _recurse_unary(current_unary_rule).iteritems()}
            elif unary_rule.child_signature.is_binary():
                distribution = self.binary_semantic_model.get_log_distribution(words, syntax_tree, tags,
                    unary_rule.child_index, unary_rule.child_signature, excluding_indices)
                child_nodes = {node: logp + logq
                               for current_binary_rule, logp in distribution.iteritems()
                               for node, logq in _recurse_binary(current_binary_rule).iteritems()}

            parent_nodes = [Node(unary_rule.parent_signature, [child_node]) for child_node in child_nodes]
            return parent_nodes

        def _recurse_binary(binary_rule, excluding_indices):
            assert isinstance(binary_rule, BinaryRule)
            assert isinstance(excluding_indices, set)
            excluding_indices = excluding_indices.union({binary_rule.parent_index})

            if binary_rule.a_signature.is_leaf():
                a_nodes = {Node(binary_rule.a_signature, []): 0}
            elif binary_rule.a_signature.is_unary():
                distribution = self.unary_semantic_model.get_log_distribution(words, syntax_tree, tags,
                        binary_rule.a_index, binary_rule.a_signature, excluding_indices)
                a_nodes = {node: logp + logq
                           for current_unary_rule, logp in distribution.iteritems()
                           for node, logq in _recurse_unary(current_unary_rule).iteritems()}
            elif binary_rule.a_signature.is_binary():
                distribution = self.binary_semantic_model.get_log_distribution(words, syntax_tree, tags,
                        binary_rule.a_index, binary_rule.a_signature, excluding_indices)
                a_nodes = {node: logp + logq
                           for current_binary_rule, logp in distribution.iteritems()
                           for node, logq in _recurse_binary(current_binary_rule).iteritems()}

            if binary_rule.b_signature.is_leaf():
                b_nodes = {Node(binary_rule.b_signature, []): 0}
            elif binary_rule.b_signature.is_unary():
                distribution = self.unary_semantic_model.get_log_distribution(words, syntax_tree, tags,
                    binary_rule.b_index, binary_rule.b_signature, excluding_indices)
                b_nodes = {node: logp + logq
                           for current_unary_rule, logp in distribution.iteritems()
                           for node, logq in _recurse_unary(current_unary_rule).iteritems()}
            elif binary_rule.b_signature.is_binary():
                distribution = self.binary_semantic_model.get_log_distribution(words, syntax_tree, tags,
                    binary_rule.b_index, binary_rule.b_signature, excluding_indices)
                b_nodes = {node: logp + logq
                           for current_binary_rule, logp in distribution.iteritems()
                           for node, logq in _recurse_binary(current_binary_rule).iteritems()}

            parent_nodes = {Node(binary_rule.parent_signature, [a_node, b_node]): a_nodes[a_node] + b_nodes[b_node]
                            for a_node, b_node in itertools.product(a_nodes, b_nodes)}

            return parent_nodes

        start_unary_rules = self.unary_semantic_model.get_possible_rules(words, syntax_tree, tags, None,
                                                                         function_signatures['StartTruth'])
        nodes = dict(itertools.chain(*(_recurse_unary(start_unary_rule).iteritems()
                                       for start_unary_rule in start_unary_rules)))

        return nodes


def tuple_to_tag_rules(words, syntax_tree, tuple_):
    splitter = '@'
    implication = 'i'
    tag_rules = []
    for string in tuple_:
        function_name, index = string.split(splitter)
        if function_name in function_signatures:
            function_signature = function_signatures[function_name]
        elif (function_name[0], function_name[-1]) == tuple("''"):
            function_signature = FunctionSignature(function_name[1:-1], 'modifier', [])
        elif (function_name[0], function_name[-1]) == tuple("[]"):
            function_signature = FunctionSignature(function_name[1:-1], 'number', [])
        elif (function_name[0], function_name[-1]) == tuple("<>"):
            function_signature = FunctionSignature(function_name[1:-1], 'variable', [])
        else:
            raise Exception()

        if index == implication:
            index = None
        else:
            index = int(index)
        tag_rule = TagRule(words, syntax_tree, index, function_signature)
        tag_rules.append(tag_rule)
    return tag_rules


def tuples_to_semantic_rules(words, syntax_tree, tuples):
    tag_rules_list = [tuple_to_tag_rules(words, syntax_tree, tuple_) for tuple_ in tuples]
    tags = {tag_rule.index: tag_rule.signature for tag_rule in itertools.chain(*tag_rules_list)}
    for index in words:
        if index not in tags:
            tags[index] = None

    unary_rules = []
    binary_rules = []
    for tag_rules in tag_rules_list:
        if len(tag_rules) == 2:
            unary_rule = UnaryRule(words, syntax_tree, tags, tag_rules[0].index, tag_rules[0].signature,
                                   tag_rules[1].index, tag_rules[1].signature)
            unary_rules.append(unary_rule)
        elif len(tag_rules) == 3:
            binary_rule = BinaryRule(words, syntax_tree, tags, tag_rules[0].index, tag_rules[0].signature,
                                     tag_rules[1].index, tag_rules[1].signature,
                                     tag_rules[2].index, tag_rules[2].signature)
            binary_rules.append(binary_rule)
    return unary_rules, binary_rules


def run():
    sentence = "circle O has a radius of 5"
    word_list = sentence.split(' ')
    words = {index: word_list[index] for index in range(len(word_list))}
    syntax_tree = nx.DiGraph()
    tuples = (
        ('StartTruth@i', 'Equal@i'),
        ('Equal@i', 'RadiusOf@4', '[5]@6'),
        ('RadiusOf@4', 'Circle@0'),
        ('Circle@0', "'O'@1"),
    )
    tag_rules = list(itertools.chain(*(tuple_to_tag_rules(words, syntax_tree, tuple_) for tuple_ in tuples)))
    tagging_feature_function = lambda x: None

    unary_rules, binary_rules = tuples_to_semantic_rules(words, syntax_tree, tuples)
    tag_model = DeterministicTagModel(tag_rules, tagging_feature_function)
    tags = tag_model.get_best_tags(words, syntax_tree)
    for index, signature in tags.iteritems():
        print index, signature


if __name__ == "__main__":
    run()
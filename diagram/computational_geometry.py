import numpy as np
from geosolver.ontology.instantiator_definitions import instantiators

__author__ = 'minjoon'

def distance_between_points(p0, p1):
    return np.linalg.norm(dimension_wise_distance_between_points(p0, p1))


def distance_between_points_squared(p0, p1):
    return (p0.x-p1.x)**2 + (p0.y-p1.y)**2


def dimension_wise_distance_between_points(p0, p1):
    return abs(p0.x-p1.x), abs(p0.y-p1.y)


def dot_distance_between_points(unit_vector, point, reference_point):
    """
    Distance between two points dot-producted by the unit vector

    :param line:
    :param point:
    :param reference_point:
    :return:
    """
    return np.dot(unit_vector, np.array(point) - np.array(reference_point))


def line_length(line):
    return distance_between_points(line.a, line.b)


def line_unit_vector(line):
    array = (np.array(line[1]) - np.array(line[0]))/line_length(line)
    return tuple(array)


def line_normal_vector(line):
    unit_vector = line_unit_vector(line)
    return unit_vector[1], -unit_vector[0]


def circumference(circle):
    return 2*np.pi*circle.radius


def midpoint(p0, p1):
    return instantiators['point'](*((np.array(p0) + np.array(p1))/2.0))


def distance_between_line_and_point(line, point):
    """
    This function is slow... Please improve!

    :param line:
    :param point:
    :return:
    """
    p = midpoint(line.a, line.b)
    vector = point.x - p.x, point.y - p.y
    u = line_unit_vector(line)
    n = line_normal_vector(line)
    perpendicular_distance = abs(np.dot(vector, n))
    parallel_distance = abs(np.dot(vector, u))
    if parallel_distance <= line_length(line)/2.0:
        return perpendicular_distance
    else:
        return min(distance_between_points(point, line.a),
                   distance_between_points(point, line.b))


def distance_between_circle_and_point(circle, point):
    return abs(circle.radius - distance_between_points(circle.center, point))

def intersections_between_lines(line0, line1, eps):
    line0a = np.array(line0)
    line1a = np.array(line1)
    x = line0a[0] - line1a[0]
    d1 = line1a[1] - line1a[0]
    d2 = line0a[1] - line0a[0]
    cross = d1[0]*d2[1] - d1[1]*d2[0]
    if abs(cross) < eps:
        return []

    t1 = float(x[0]*d2[1] - x[1]*d2[0])/cross
    r = line1a[0] + d1*t1
    p = instantiators['point'](*r)
    if distance_between_line_and_point(line1, p) < eps and distance_between_line_and_point(line0, p) < eps:
        return [p]
    else:
        return []


def intersections_between_circle_and_line(circle, line, eps):
    min_angle = 30
    temp_sln = []
    normal_vector = np.array(line_normal_vector(line))
    parallel_vector = np.array(line_unit_vector(line))
    d = np.dot(np.array(midpoint(*line))-np.array(circle.center), normal_vector)
    perp_vector = d*normal_vector

    # Tangency
    D = circle.radius**2 - d**2

    # Error tolerant step
    if D < 0:
        D = (circle.radius + eps)**2 - d**2
        if D >= 0:
            par_vector = np.sqrt(D) * parallel_vector
            pt = instantiators['point'](*(circle.center + perp_vector))
            temp_sln.append(pt)

    else:
        par_vector = np.sqrt(D) * parallel_vector
        pt = instantiators['point'](*(np.array(circle.center) + perp_vector + par_vector))
        temp_sln.append(pt)
        pt = instantiators['point'](*(np.array(circle.center) + perp_vector - par_vector))
        temp_sln.append(pt)

    # Check if the point is on the line
    sln = []
    for point in temp_sln:
        if distance_between_line_and_point(line, point) < eps:
            pt = instantiators['point'](*point)
            sln.append(pt)

    if len(sln) == 2:
        angle = instantiators['angle'](sln[0], circle.center, sln[1])
        if angle_in_degree(angle) < min_angle:
            return [midpoint(sln[0], sln[1])]

    return sln

def intersections_between_circles(circle0, circle1):
    """
    TO BE IMPLEMENTED
    :param circle0:
    :param circle1:
    :return:
    """
    return []


def angle_in_radian(angle, smaller=True):
    a = line_length(instantiators['line'](angle.b, angle.c))
    b = line_length(instantiators['line'](angle.c, angle.a))
    c = line_length(instantiators['line'](angle.a, angle.b))
    smaller_angle = np.sqrt((a**2 + b**2 - c**2) / (2*a*b))
    if smaller:
        return smaller_angle


def angle_in_degree(angle, smaller=True):
    return 180*angle_in_radian(angle, smaller=smaller)/np.pi


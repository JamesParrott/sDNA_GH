
# random is used here for fuzz testing, not Cryptography.  
# But could Windows OS generated randomness be repeatable
# between instances of the same VM image, e.g. CI runners?  
# If so use:
# random.seed(time.time())
# Otherwise, assuming os.urandom includes the time already:
SEED = os.urandom(10)
random.seed(SEED)

# Extents of viewport
MIN_X, MAX_X, MIN_Y, MAX_Y = -10.0, 110.0, -10.0, 40.0

def random_number(min_ = MIN_X, max_ = MAX_X):
    return random.uniform(min_, max_)

def random_pair():
    return random_number(), random_number()

def random_triple():
    return random_pair() + (random_number(),)

def random_int(min_ = 2, max_ = 17):
    return random.randint(min_, max_)

def random_triples(n = None):
    n = n or random_int(min_ = 3)
    return tuple(random_triple() for __ in range(n))

# def random_point():

def random_nurbs_curve(length = None, degree = None):
    length = length or random_int()

    # The control points are a list of at least degree+1 points.
    # https://developer.rhino3d.com/guides/opennurbs/nurbs-geometry-overview/
    degree = degree or random_int(1, length-1)

    # The knots are a list of degree+N-1 numbers, where N is the number of control points. Sometimes this list of numbers is called the knot vector. In this term, the word vector does not mean 3‑D direction.
    # This list of knot numbers must satisfy several technical conditions. The standard way to ensure that the technical conditions are satisfied is to require the numbers to stay the same or get larger as you go down the list and to limit the number of duplicate values to no more than the degree. For example, for a degree 3 NURBS curve with 11 control points, the list of numbers 0,0,0,1,2,2,2,3,7,7,9,9,9 is a satisfactory list of knots. The list 0,0,0,1,2,2,2,2,7,7,9,9,9 is unacceptable because there are four 2s and four is larger than the degree.
    # The number of times a knot value is duplicated is called the knot’s multiplicity. In the preceding example of a satisfactory list of knots, the knot value 0 has multiplicity three, the knot value 1 has multiplicity one, the knot value 2 has multiplicity three, the knot value 3 has multiplicity one, the knot value 7 has multiplicity two, and the knot value 9 has multiplicity three. A knot value is said to be a full-multiplicity knot if it is duplicated degree many times. In the example, the knot values 0, 2, and 9 have full multiplicity. A knot value that appears only once is called a simple knot. In the example, the knot values 1 and 3 are simple knots.
    # If a list of knots starts with a full multiplicity knot, is followed by simple knots, terminates with a full multiplicity knot, and the values are equally spaced, then the knots are called uniform. For example, if a degree 3 NURBS curve with 7 control points has knots 0,0,0,1,2,3,4,4,4, then the curve has uniform knots. The knots 0,0,0,1,2,5,6,6,6 are not uniform. Knots that are not uniform are called non‑uniform. The N and U in NURBS stand for non‑uniform and indicate that the knots in a NURBS curve are permitted to be non-uniform.
    # Duplicate knot values in the middle of the knot list make a NURBS curve less smooth. At the extreme, a full multiplicity knot in the middle of the knot list means there is a place on the NURBS curve that can be bent into a sharp kink. For this reason, some designers like to add and remove knots and then adjust control points to make curves have smoother or kinkier shapes. Since the number of knots is equal to (N+degree‑1), where N is the number of control points, adding knots also adds control points and removing knots removes control points. Knots can be added without changing the shape of a NURBS curve. In general, removing knots will change the shape of a curve.
    knots = []

    i = 0
    while len(knots) < degree + length -1:
        multiplicity = random_int(1, degree)
        knots.extend([i,] * multiplicity)
        i += 1

    #
    points = random_triples(length)

    return rs.AddNurbsCurve(points, knots, degree) 

try:
    unichr
except NameError:
    unichr = chr

def random_string(length = None):
    length = length or random_int()
    return u''.join(unichr(random_int()) for __ in range(length))


OBJECT_GENERATORS = [rs.AddArc3Pt, rs.AddBox, rs.AddCircle3Pt, 
                     rs.AddCone, rs.AddCurve, rs.AddEllipse3Pt, rs.AddLine,
                     rs.AddPoint, rs.AddPolyline,
                     rs.AddRectangle, rs.AddSphere, rs.AddSpiral, rs.AddTorus,
                     rs.AddTextDot, random_nurbs_curve
                     ]

def needed_args(func):
    arg_spec = inspect.getargspec(func)
    if arg_spec.defaults is None:
        return arg_spec.args
    return arg_spec.args[:-len(arg_spec.defaults)]

#for obj_gen in OBJECT_GENERATORS:
#    break
#    print('%s: %s' % (obj_gen.__name__, needed_args(obj_gen)))

random_funcs = OrderedDict([
                     (('start', 'end', 'first', 'second', 'third', 'center'), random_triple),
                     (('points','corners'), random_triples),
                     (('point', ), random_triple),
                     (('plane','base'), lambda : rs.WorldXYPlane()),
                     (('height', 'width', 'radius', 'pitch'), random_number),
                     (('turns',), random_int),
                     (('text',), random_string),
                     ])


def random_Geometry():

    N = random_int(1, 14)

    Geom = []
    for __ in range(N):
        obj_gen = random.choice(OBJECT_GENERATORS)
        kwargs = {}
        for arg in needed_args(obj_gen):
            names_and_random_funcs = ((name, v) 
                                    for k, v in random_funcs.items()
                                    for name in k)
            for name, random_func in names_and_random_funcs:
                if name in arg:
                    kwargs[arg] = random_func()
                    break
                #
            else: # no break in inner most for loop - no name found
                raise KeyError('No random func found for arg: %s' % arg)
        try:
            geom = obj_gen(**kwargs)        
        except Exception:
            print('Oops! %s ' % [obj_gen.__name__, kwargs])
            continue
        if geom:
            Geom.append(str(geom))
    
    return Geom
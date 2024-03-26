from . import make_unit_test_TestCase_instance_generator, get_comp_from_or_add_comp_to_canvas
from .helpers import run_comp, get_or_add_comp, add_instance_of_userobject_to_canvas

# This module must be run from a Grasshopper Document with a 
# Component_Random and GH_GradientControl already placed.
GHRandomComponent = GH_Doc_components['Random']
GHGradientComponent = GH_Doc_components['Gradient']

Recolour_Objects = get_comp_from_or_add_comp_to_canvas('Recolour_Objects')


def test_recolouring_random_num_of_random_objs_random_cols(self):

    sc.doc = Rhino.RhinoDoc.ActiveDoc
    Geom = random_Geometry()

    N = len(Geom)

    cols = []



    
    for __ in range(N):



        random_retvals = run_comp(GHRandomComponent, N=1, S = random_int(0, 250000))

        gradient_retvals = run_comp(GHGradientComponent, L0=-123, L1 = 172, t = random_retvals['nums'])

        col = gradient_retvals['C']
        cols.append(col.Value)




    run_comp(Recolour_Objects, go=True, Data=cols, Geom=Geom)

    j = 0
    for geom, colour in zip(Geom, cols):
        guid = System.Guid(geom)
        j += 1
        if not guid:
            print('j: %s, Falsey guid: %s' % (j, guid))
            continue
        obj = Rhino.RhinoDoc.ActiveDoc.Objects.Find(guid)
        if not obj:
            print('j: %s, Falsey obj: %s' % (j, obj))
            continue
        if self is not None:
            self.assertEqual(obj.Attributes.ObjectColor, colour)
        print('%s: Correct colour: %s' % (guid, obj.Attributes.ObjectColor == colour))
      




test_case_generator = make_unit_test_TestCase_instance_generator(
                            Class = RandomNumberOfRandomObjectsRandomlyRecolourTests,
                            method = test_recolouring_random_num_of_random_objs_random_cols,
                            )
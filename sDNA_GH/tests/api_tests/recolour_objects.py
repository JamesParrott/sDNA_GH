import System
import Rhino

from . import make_unit_test_TestCase_instance_generator
from ..helpers import run_comp,get_user_obj_comp_from_or_add_to_canvas
from ..fuzzers import random_Geometry



if Rhino.RhinoDoc.ActiveDoc.Name:
    raise Exception("These tests require a clean Rhino Document to test in. "
                    "To protect your document: save your Rhino file"
                    ", create a new one (and don't save it)"
                    ", run an Unload_sDNA component"
                    ", and re-initialise this component to restart the tests. "
                   )



try:
    GHRandomComponent = GH_Doc_components['Random']
    GHGradientComponent = GH_Doc_components['Gradient']
    GHDomainComponent = GH_Doc_components['Construct Domain (Dom)']
except KeyError:
    raise Exception("These tests require a Random Sequence component"
                    ", a Gradient component "
                    ", and a Construct Domain (Dom) component"
                    " on the canvas. "
                    "Place these components, run an Unload_sDNA component"
                    ", and then re-initialise this component to restart the tests. "
                   )

Recolour_Objects = get_user_obj_comp_from_or_add_to_canvas('Recolour_Objects')


def test_recolouring_random_num_of_random_objs_random_cols(self):

    sc.doc = Rhino.RhinoDoc.ActiveDoc
    Geom = random_Geometry()

    N = len(Geom)

    colours = []



    
    # TODO: Work out how to pass in, and extract lists from Grasshopper components.
    for __ in range(N):

        random_retvals = run_comp(GHRandomComponent, N=1, S = random_int(0, 250000))

        gradient_retvals = run_comp(GHGradientComponent, L0=-123, L1 = 172, t = random_retvals['nums'])

        col = gradient_retvals['C']
        colours.append(col.Value)




    run_comp(Recolour_Objects, go=True, Data=colours, Geom=Geom)

    j = 0
    for geom, colour in zip(Geom, colours):
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
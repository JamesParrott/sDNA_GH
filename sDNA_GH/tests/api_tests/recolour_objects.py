import System
import Rhino
import scriptcontext as sc

from . import make_unit_test_TestCase_instance_generator
from ..helpers import run_comp, get_user_obj_comp_from_or_add_to_canvas, GH_DOC_COMPONENTS
from ..fuzzers import random_Geometry, random_int



if Rhino.RhinoDoc.ActiveDoc.Name:
    raise Exception("These tests require a clean Rhino Document to test in. "
                    "To protect your document: save your Rhino file"
                    ", create a new one (and don't save it)"
                    ", run an Unload_sDNA component"
                    ", and re-initialise this component to restart the tests. "
                   )



try:
    GHRandomComponent = GH_DOC_COMPONENTS['Random']
    GHGradientComponent = GH_DOC_COMPONENTS['Gradient']
    GHDomainComponent = GH_DOC_COMPONENTS['Dom']
except KeyError:
    raise Exception("These tests require a Random Sequence component"
                    ", a Gradient component "
                    ", and a Construct Domain (Dom) component"
                    " on the canvas. "
                    "Place these components, run an Unload_sDNA component"
                    ", and then re-initialise this component to restart the tests. "
                   )

Recolour_Objects = get_user_obj_comp_from_or_add_to_canvas('Recolour_Objects')


def recolouring_random_num_of_random_objs_random_cols(self):

    sc.doc = Rhino.RhinoDoc.ActiveDoc
    Geom = random_Geometry()

    N = len(Geom)

    colours = []

    L0, L1 = -123, 172

    domain_retvals = run_comp(GHDomainComponent, A=L0, B=L1)

    
    # TODO: Work out how to pass in, and extract lists from Grasshopper components.
    for __ in range(N):

        random_retvals = run_comp(GHRandomComponent, R = domain_retvals['I'], N=1, S = random_int(0, 250000))

        gradient_retvals = run_comp(GHGradientComponent, L0=L0, L1=L1, t = random_retvals['nums'])

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
            self.assertEqual(
                obj.Attributes.ObjectColor
                ,colour
                ,msg='geom: %s\n expected: %s\n actual: %s\n guid: %s' % (geom, colour, obj.Attributes.ObjectColor, guid)
                )
        print('%s: Correct colour: %s' % (guid, obj.Attributes.ObjectColor == colour))
      




test_case_generator = make_unit_test_TestCase_instance_generator(
                            method = recolouring_random_num_of_random_objs_random_cols,
                            )

#def make_random_objects_random_colours_tester():

def test_recolouring_random_num_of_random_objs_random_cols(self):

    sc.doc = Rhino.RhinoDoc.ActiveDoc
    Geom = random_Geometry()

    N = len(Geom)

    cols = []

    GHRandomComponent = GH_Doc_components['Random']
    GHGradientComponent = GH_Doc_components['Gradient']
#    print('Grad.NickName: %s ' % GHGradientComponent.NickName)
#    print('Grad.Name: %s ' % GHGradientComponent.Name)

#    print([(Output.NickName, Output.Name) 
#           for Output in GHGradientComponent.Params.Output
#          ])


    # func = make_callable_using_node_in_code(name)
    
    for __ in range(N):

        #
#        I = [-123, 173, random_int(-123, 173)];
        #
#        result = func(*I);
        #
#        a = result[0]; #//this is output R
        
#        print(type(a))
        
#        cols.append(a)

#         randomise seed
#        set_data_on(GHRandomComponent.Params.Input[2], random_int())
#        set_data_on(GHRandomComponent.Params.Input[1], 1)

        random_retvals = run_comp(GHRandomComponent, N=1, S = random_int(0, 250000))

        gradient_retvals = run_comp(GHGradientComponent, L0=-123, L1 = 172, t = random_retvals['nums'])


        # print()
#        col = get_data_from(GHGradientComponent.Params.Output[0])
        col = gradient_retvals['C']
        cols.append(col.Value) #System.Drawing.Color(col))


    # print([dir(col.Value) for col in cols])
    # print([col.Value for col in cols])
    # print([isinstance(col.Value, System.Drawing.Color) for col in cols])
    # print([type(col.Value) for col in cols])
    # print([type(geom) for geom in Geom])

    # sc.doc = ghdoc
    # print()

    # cols = th.list_to_tree(cols)

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
      

def API_unittest_TestCase_instances():


    class RandomNumberOfRandomObjectsRandomlyRecolourTests(unittest.TestCase):
        pass


    # NUM_TESTS = 5

    # method_names = []

    while True:
    #    test_recolouring_random_num_of_random_objs_random_cols(None)
        method_name = 'test_recolouring_random_num_of_random_objs_random_cols_%s' % (i+1)
        setattr(RandomNumberOfRandomObjectsRandomlyRecolourTests
            ,method_name
            ,test_recolouring_random_num_of_random_objs_random_cols
            )
        # method_names.append(method_name)

        yield RandomNumberOfRandomObjectsRandomlyRecolourTests(method_name)
            
    # test_suite = unittest.TestSuite()
    # for method_name in method_names:
        # # test_suite.addTest(RandomNumberOfRandomObjectsRandomlyRecolourTests(method_name))
        # yield RandomNumberOfRandomObjectsRandomlyRecolourTests(method_name)

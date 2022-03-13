if      '__file__' in __builtins__  and  __name__ in __file__ and '__main__' not in __file__ and '<module>' not in __file__:                     
    # Assert:  We're in a module!
    pass
else:
    pass
    #print 


""" print(__name__)
if __name__ == '':
    pass # Module only code.  No else associates with this if to avoid indentation.  Are there module imports without __name__=='' ?
if __name__ == '__main__':  # Name is still '__main__' in an uncompiled grasshopper component as well as in scripts.
    from argparse import ArgumentParser()
    ap=ArgumentParser()
    if ap.prog != '':   #TODO Test for Rhinoscript
                        # we could assert ap.prog == 'GHsDNA.py' but perhaps the user has renamed this file.
        print('Running module as script e.g. from the command line')
        #ap.add_argument('Rhino_file',help='The .3dm file defining the spatial network',type=str)
        #ap.add_argument('output_file',help='The name of the .shp file (suite) to write the results from sDNA to',type=str)
        #args=ap.parse_args()
        #TODO Use command line args to run test definitions if '--test' is present
        test_cases=import_module_or_search_for_it('test_cases')
    else:  
        pass # code to run only if in an uncompiled grasshopper component
             # in an uncompiled grasshopper component ap.prog == '' (also when imported as a module)
        print('Running module in an uncompiled grasshopper component (plain source in a python component in a .gh file)')

else:
    lower_case_hex_digit_pattern='[a-f|\d]'
    uuid_pattern_no_hyphens=lower_case_hex_digit_pattern+'{32}'
    grasshopper_compiled_component___name___pattern='\APython_'+uuid_pattern_no_hyphens+'\Z'
    from re import match
    # This regex will match __name__='Python_d396a1fb0e6441508fa6555b4d306ff5' for example
    if match(grasshopper_compiled_component___name___pattern,__name__):
        print('Running module in a compiled grasshopper component (in a .ghpy file within a .gh file)')
        pass
        # code to run only if in a compiled grasshopper component
    else:
        pass         
        print('Running module as a module import.  __name__=='+__name__)
        #code to run only if we're imported as a module """
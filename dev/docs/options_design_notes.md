# OPTIONS FOR YOUR OPTIONS
#
# a) Use a local dictionary
# b) Use a simple class
# c) Use a named tuple
# d) Use a global variable
#
# tl;dr The structure for this code base is a main function call, within which the options
# variable have no reason to change.  The author prefers it not to be possible to change them
# and also would rather not have to put 'quotes' around the option field names.  Therefore 
# a namedtuples is used for the options instead of a dictionary.
#
# If your design is different - i.e. if you are using this code and altering it for a different 
# purpose, in which the options need to change within the current code in the function bodies 
# (in the same scope), you will need to use a dictionary or a Class instead.
#
# A local dictionary is the best simple way.  Dictionaries are brilliant but mutable.  Therefore they
# can unfortunately be changed by accidental coding typos after initiation.  Also I for one prefer 
# not to read or write square brackets [ ] quotation marks "''" to index the keys with string 
# literals.  A simple class or instance thereof is highly customisable, but its main attributes 
# (non '__abcdef__' ones ) are not so elegantly iterable over (nor testable against) over.  And like 
# dictionaries
# they can  be changed inadvertently.  Enter named tuples.  They are immutable, indexable without ['']
# but require a little boilerplate code to set up.  They can easily be created from dictionaries and lists.
# But they do still require e.g. ._fields to iterate over their field names or test for membership
#  but dir ( ) can be avoided along (with the special methods it outputs).  
# 
# Finally if you want an easy bad option for your options
# and are happy with global variables (even though you shouldn't be), it's possible to leave the options 
# as a global variable (or defined in a parent scope), and have to write much less code.  
#

#Old:

###############################################################################################################
# Override (3) user installation specific options with (2) previously updated options in Grasshopper definition 
# from another sDNA_GH component
#new_nt = options_manager.override_namedtuple_with_namedtuple(installation_nt, old_nt_or_dict, add_in_new_options_keys=True, check_types = True, strict = False)
#new_metas = options_manager.override_namedtuple_with_namedtuple(test_metas, new_metas, add_in_new_options_keys=True, check_types = True, strict = False)
#new_options = options_manager.override_namedtuple_with_namedtuple(test_options, new_options, True, add_in_new_options_keys=True, check_types = True, strict = False)
                                                            # Both must have an _asdict() method.  See note 1) above.
                                                            # Assume both came from a previous call to this function
                                                            # and so already contain hardcoded and installation options
                                                            # i.e.  no fields are missing.

#if 'config_file_path' in args_metas:
#    ###########################################################################################################################
#    # Override (2) previously updated options in Grasshopper definition with (1) latest (e.g. different) project file's options
#    new_metas = options_manager.override_namedtuple_with_ini_file(  args_metas[config_file_path]
#                                                                   ,new_metas
#                                                                   ,opts['metas'].add_in_new_options_keys
#                                                                   ,False
#                                                                   ,'Metas'
#                                                                   ,False
#                                                                   ,None
#                                                                   )
#    new_options = options_manager.override_namedtuple_with_ini_file( args_metas[config_file_path]
#                                                                    ,new_options
#                                                                    ,opts['metas'].add_in_new_options_keys
#                                                                    ,False
#                                                                    ,'Metas'
#                                                                    ,False
#                                                                    ,None
#                                                                    )
# Note, the order of the processing of hardcoded and installation config.ini options is unlikely to matter but
# the user may expect arg_metas (processed below) to occur before project config.ini options_manager.overrides new_options (processed above)
# TODO: Nice to have.  Switch this order if a meta is changed (need to always check for this meta in higher priorities first, 
# before overriding lower priority options).

#######################################################################################################################
# Override (1) latest project file's options with (0) options arguments directly supplied to the Grasshopper component
#new_metas = options_manager.override_namedtuple_with_dict(args_metas, new_metas, True, 'Metas')
#new_options = options_manager.override_namedtuple_with_dict(args_options, new_options, True, 'Options')
#return new_nt
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
# they can  be changed inadvertantly.  Enter named tuples.  They are immutable, indexable without ['']
# but require a little boilerplate code to set up.  They can easily be created from dictionaries and lists.
# But they do still require e.g. ._fields to iterate over their field names or test for membership
#  but dir ( ) can be avoided along (with the special methods it outputs).  
# 
# Finally if you want an easy bad option for your options
# and are happy with global variables (even though you shouldn't be), it's possible to leave the options 
# as a global variable (or defined in a parent scope), and have to write much less code.  
#
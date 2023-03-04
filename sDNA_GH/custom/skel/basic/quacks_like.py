#! /usr/bin/python
# -*- coding: utf-8 -*-
__author__ = 'James Parrott'
__version__ = '2.2.0'


import abc


abstractmethod = abc.abstractmethod

if hasattr(abc, 'ABC'):
    ABC = abc.ABC
else:
    class ABC(object):
        __metaclass__ = abc.ABCMeta
    
    
class BasicABC(ABC):
    @abstractmethod
    def f(self):
        '''Do nothing'''

class BasicClass(object):
    def f(self):
        '''Do nothing'''

abc_only_attrs = [x for x in dir(BasicABC) 
                    if x not in dir(BasicClass)]
abc_only_attrs += [x for x in dir(BasicABC.f) 
                     if x not in dir(BasicClass.f)]


#   to allow a non-abstract obj to quack like an abstract obj in a Structural
#   Typing test. 
#   e.g. abc_only_attrs += ['__isabstractmethod__'], but there are a lot more!
#   __isabstractmethod__ is set==True by @abstractmethod on attrs of 
#   ABC subclasses https://peps.python.org/pep-3119/

def quacks_like(Duck
               ,obj
               ,check_attr_types = True
               ,check_dunders = False
               ):
    #type(type[Any], type[Any], bool, bool) -> bool

    # A simple (naive) Structural Typing checker, to permit duck typing.  
    # Checks instances as well as classes.  Untested on waterfowl.  
    #
    # A template Tool is provided below to 
    # define the interface supported by run_tools,
    # but I don't want to force power 
    # users importing the package
    # to inherit from ABCs, as instances of 
    # Tool (with __call__) can equally well be 
    # replaced by normal Python functions 
    # with a few extra attributes.

    return (  isinstance(obj, Duck.__class__ )
              or all( hasattr(obj, attr) and 
                        (not check_attr_types or 
                         quacks_like(getattr(Duck, attr)
                                    ,getattr(obj, attr)
                                    ,check_attr_types
                                    ,check_dunders
                                    )
                         )
                      for attr in dir(Duck) if (check_dunders or 
                                                not attr.startswith('_') and
                                                attr not in abc_only_attrs 
                                                )
                    )
            )

def basic_function():
    pass


#! /usr/bin/python
# -*- coding: utf-8 -*-




import sys, os, logging, inspect


# set a format which is simpler for console use
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')


def add_custom_file_to_logger(logger
                             ,custom_file_object = None
                             ,custom_logging_level = 'INFO'
                             ):
    try:
        custom_stream=logging.StreamHandler(custom_file_object)
        custom_stream.setLevel(getattr(logging,custom_logging_level))
        custom_stream.setFormatter(formatter)
        logger.addHandler(custom_stream)
    except: 
        pass

def new_Logger(  logger_name = 'main'
                ,file_name = os.path.join(sys.path[0]
                                         ,sys.argv[0].rsplit('.')[0] + '.log'
                                         )
                ,file_logging_level = 'DEBUG'
                ,console_logging_level = 'WARNING'
                ,custom_file_object = None
                ,custom_logging_level = 'INFO'):
    # type : (str,str,str,str,stream,str) -> Logger
    # stream is any'file-like object' supporting write() and flush() methods
    """ Convenience wrapper for Vinay Sajip's logger recipe with customisable
        console output 
        https://docs.python.org/2.7/howto/logging-cookbook.html#logging-cookbook """


    file_logging_level = file_logging_level.upper()
    console_logging_level = console_logging_level.upper()
    custom_logging_level = custom_logging_level.upper()

    logging.basicConfig( level = getattr(logging, file_logging_level)
                        ,format = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
                        ,datefmt = '%d-%m-%y %H:%M'
                        ,filename = file_name
                        ,filemode = 'w')
    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(getattr(logging,console_logging_level))
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    logger=logging.getLogger(logger_name)
    logger.addHandler(console)
    if custom_file_object:            
        add_custom_file_to_logger(logger, custom_file_object, custom_logging_level)
    return logger 
    #
####################################################################################

def make_self_logger(self, logger = None, module_name = '', name = None):
    if name is None:
        name = self.__class__.__name__
    if module_name:
        module_name += '.'
    if logger:
        logger = logger.getChild(name)
    else:
        logger = logging.getLogger(module_name + name)
    logger.addHandler(logging.NullHandler())
    return logger

def make_log_message_maker(method, logger = None, module_name = None):
    if module_name is None:
        module_name = __name__
    def f(self, message, *args):
        if not hasattr(self, 'logger'):
            self.logger = make_self_logger(self, logger, module_name)
        getattr(self.logger, method)(message, *args)
        return message
    return f

def add_methods_decorator(obj, methods = None, method_maker = make_log_message_maker, **kwargs):
    if methods is None:
        methods = ('debug', 'info', 'warning', 'error', 'critical', 'exception')
    for method in methods:
        setattr(obj, method, method_maker(method, **kwargs))

def class_logger_factory(logger = None, module_name = None):
    """ Factory for ClassLogger Classes.  Otherwise __name__ will 
        be 'wrapper.logging' now matter which module they were instantiated
        in.  """
    class ClassLogger(object):
        """ Class to inherit a class logger from, e.g. via co-operative 
            multiple inheritance (CMI).  After instantiation, .SubClassName is
            appended to module_name in its logs, e.g. to aid debugging.  
            
            To add in a class logger via 
            composition instead of inheritance, assign the attribute directly 
            to make_self_logger() with the desired name as an argument"""
        pass
    add_methods_decorator(ClassLogger, logger = logger, module_name = module_name)
    return ClassLogger



class Output(object): 
    """   Wrapper class for logger, logging, print, with a cache.  Example setup:
    import logging
    logger = logging.getLogger(__name__)
    logger.addHandler(logging.NullHandler())
    cache = []
    output = Output(cache, logger)
    """
    def set_logger(self, logger, flush = True):
        self.logger = logger
        if flush and self.tmp_logs:
            self.flush()

    def __init__(self
                ,tmp_logs = None
                ,logger = None
                ):
        if not isinstance(tmp_logs, list): #assert not isinstance(None, list)
            tmp_logs = []
        self.tmp_logs = tmp_logs
        if logger is not None:
            self.set_logger(logger, flush = False)



    def store(self, message, logging_level):
        self.tmp_logs.append( (message, logging_level) )

    def __call__(self, message, logging_level = "INFO", logging_dict = {}):
        #type: (str, str, dict, list) -> str
        
        #print(message)

        if logging_dict == {} and hasattr(self, 'logger'): 
            logging_dict = dict( DEBUG = self.logger.debug
                                ,INFO = self.logger.info
                                ,WARNING = self.logger.warning
                                ,ERROR = self.logger.error
                                ,CRITICAL = self.logger.critical
                                )

        logging_level = logging_level.upper()
        if logging_level in logging_dict:
            logging_dict[logging_level](message)
        else:
            self.store(message, logging_level)

        return logging_level + ' : ' + message + ' '

    def flush(self):
        tmp_logs = self.tmp_logs[:] # __call__ might cache back to tmp_logs
        self.tmp_logs[:] = [] # Mutate list initialised with
        for tmp_log_message, tmp_log_level in tmp_logs:
            self.__call__(tmp_log_message, tmp_log_level)



##############################################################################
#
#
# Python 3 only
#
#
class Debugger(object):
    """ Wrapper class for quick debugging messages that prepends a variable's 
    name (if it can be found) to its value, then calls an output callable.  
    Example setup:
    import logging
    logger = logging.getLogger(__name__)
    logger.addHandler(logging.NullHandler())
    cache = []
    output = Output(cache, logger)
    debug = Debugger(output)
    """
    def __init__(self, output = None):
        #type(type[any], function) -> None  # callable object
        if output is None:
            output = Output()
        self.output = output # want to call an instance that we also use for
                             # higher logging level messages so 
                             # composition instead of inheritance is used
    def __call__(self, x):
        c = inspect.currentframe().f_back.f_locals.items()

        names = [name.strip("'") for name, val in c if val is x]
        # https://stackoverflow.com/questions/18425225/getting-the-name-of-a-variable-as-a-string
        # https://stackoverflow.com/a/40536047

        if names:
            return self.output(str(names) + ' == ' + str(x)+' ','DEBUG')
        else:
            return self.output(str(x)+' ','DEBUG')
#
#
##############################################################################

#! /usr/bin/python
# -*- coding: utf-8 -*-




import sys, os, logging


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


def make_log_message_maker(method, logger = None, module_name = None):
    if module_name is None:
        module_name = __name__
    def f(self, message, *args):
        if not hasattr(self, 'logger'):
            if logger:
                self.logger = logger.getChild(self.__class__.__name__)
            else:
                self.logger = logging.getLogger(module_name + '.' + self.__class__.__name__)
            self.logger.addHandler(logging.NullHandler())
        getattr(self.logger, method)(message, *args)
        return message
    return f

def class_logger_factory(logger = None, module_name = None):
    """ Factory for ClassLogger Classes.  Otherwise __name__ will 
        be 'wrapper.logging' now matter which module they were instantiated
        in.  """
    class ClassLogger:
        """ Class to inherit a class logger from, e.g. via co-operative 
            multiple inheritance.  After instantiation, 
            .SubClassName is appendeded to module_name 
            in its logs, to aid debugging.  """
        pass
    methods = ('debug', 'info', 'warning', 'error', 'critical', 'exception')
    for method in methods:
        setattr(ClassLogger, method, make_log_message_maker(method, logger, module_name))
    return ClassLogger




#! /usr/bin/python
# -*- coding: utf-8 -*-

# MIT License

# Copyright (c) [2021] [Cardiff University, a body incorporated
# by Royal Charter and a registered charity (number:
# 1136855) whose administrative offices are at 7th floor 30-
# 36 Newport Road, UniversityCF24 0DE, Wales, UK]

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

__author__ = 'James Parrott'
__version__ = '1.0'

import sys
import os
import logging
import functools
import inspect

try:
    basestring #type: ignore
except NameError:
    basestring = str

class LoggingOptions(object):
    default_path = __file__
    working_folder = os.path.dirname(default_path)
    logger_name = 'root'
    propagate = False
    log_file = __name__ + '.log'
    log_file_mode = 'w'
    log_file_encoding = 'utf-8'
    logs_dir = 'logs'
    log_file_level = 'DEBUG'
    log_console_level = 'INFO'
    #
    log_custom_level = 'INFO'
    log_file_fmt_str = '%(name)s: %(levelname)s: %(message)s' #%(asctime)s 
    log_console_fmt_str = '%(name)s: %(levelname)s: %(message)s'
    log_custom_fmt_str = log_console_fmt_str
    log_date_fmt = '%d-%m-%y %H:%M'







def get_existing_stream_handler_or_add_new_one(logger
                                              ,level = None
                                              ,fmt = None
                                              ,stream = sys.stdout
                                              ,options = LoggingOptions
                                              ):
    #type(logging.Logger, str, str, Stream, LoggingOptions) -> logging.StreamHandler
    # A Stream is a file-like object with flush and write methods.
    if level is None:
        level = options.log_console_level.upper()
    if fmt is None:
        fmt = options.log_console_fmt_str

    for handler in logger.handlers:
        if (isinstance(handler, logging.StreamHandler) and
            not isinstance(handler, logging.FileHandler) and
            handler.stream is stream):
            #
            stream_handler = handler
            break
    else:
        stream_handler=logging.StreamHandler(stream)
        logger.addHandler(stream_handler)

    stream_handler.setLevel(level)
    stream_formatter = logging.Formatter(fmt = fmt)
    stream_handler.setFormatter(stream_formatter)
    
    return stream_handler


def set_handler_level(handler, level):
    #type(logging.Handler, str/int) -> None
    if isinstance(level, basestring):
        if level.isnumeric():
            level = int(level)
        else:    
            level = level.upper()
            if not hasattr(logging, level):
                raise ValueError('Unsupported logging level: %s' % level)
            level = getattr(logging, level)
    if isinstance(handler, logging.Handler) and handler.level != level:
        # allow custom numeric levels
        handler.setLevel(level)


def get_existing_file_handler_or_add_new_one(logger, options = LoggingOptions):
    #type:(logging.Logger, LoggingOptions | tuple) -> logging.FileHandler
    dir_name = os.path.join(options.working_folder, options.logs_dir)

    if not os.path.isdir(dir_name):
        os.mkdir(dir_name)

    file_name = os.path.join(dir_name, options.log_file)

    for handler in logger.handlers:
        if (isinstance(handler, logging.FileHandler) and
            handler.baseFilename == file_name):
            if (handler.mode != options.log_file_mode and 
                handler.encoding != options.log_file_encoding):
                #
                handler.close()
            else:
                file_handler = handler
                break
    else:
        file_handler = logging.FileHandler(filename = file_name
                                          ,mode = options.log_file_mode
                                          ,encoding = options.log_file_encoding
                                          )
        logger.addHandler(file_handler)


    file_logging_level = options.log_file_level.upper()
    set_handler_level(file_handler, file_logging_level)
    log_file_formatter = logging.Formatter(fmt = options.log_file_fmt_str
                                          ,datefmt = options.log_date_fmt
                                          )
    file_handler.setFormatter(log_file_formatter)

    return file_handler



def get_logger_and_handlers(stream = None
                           ,options = LoggingOptions
                           ):
    # type : (stream, type[any]/namedtuple) -> logging.Logger, logging.Handler, logging.Handler, logging.Handler
    """ Returns logger, and two or three handlers.   

        stream is any'file-like object' supporting write() and flush() methods
    """
    
    logger = logging.getLogger(options.logger_name)
    logger.setLevel('DEBUG')
    logger.propagate = options.propagate



    if options.log_file:
        file_handler = get_existing_file_handler_or_add_new_one(logger, options)
    else:
        file_handler = logging.NullHandler()

    console_handler = get_existing_stream_handler_or_add_new_one(
                                             logger
                                            ,level = options.log_console_level
                                            ,fmt = options.log_console_fmt_str
                                            ,stream = sys.stdout
                                            ,options = options
                                            )


    if stream:            
        stream_handler = get_existing_stream_handler_or_add_new_one(
                                             logger
                                            ,level = options.log_custom_level
                                            ,fmt = options.log_custom_fmt_str
                                            ,stream = stream
                                            ,options = options
                                            )
    else:
        stream_handler = logging.NullHandler()
    
    return logger, file_handler, console_handler, stream_handler 


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


def make_log_message_maker(method
                          ,logger = None
                          ,module_name = None
                          ,warn = True
                          ,raise_error = True):
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
#
#
####################################################################################



####################################################################################
#

#
#
class Output(object): 
    """ A single callable wrapper with a cache.  Saves logging messages from before the
        logger system is setup until they can be flushed into the logger, and provides
        a central point to redirect all log messaging calls through, (e.g. if the logger
        itself needs debugging, providing the perfect place to temporarily use logger.debug)

        Wrapper class for logger, logging, logger.debug, with a cache.  Example setup:
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

        return '%s : %s ' %(logging_level, message )

    def __getattr__(self, attr):
        return functools.partial(self.__call__, logging_level = attr.upper())

    def flush(self):
        tmp_logs = self.tmp_logs[:] # __call__ might cache back to tmp_logs
        self.tmp_logs[:] = [] # Mutate list initialised with
        for tmp_log_message, tmp_log_level in tmp_logs:
            self.__call__(tmp_log_message, tmp_log_level)
#
#
#
##############################################################################
#

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

    Supplements an instance of the above Output Class by adding in the names found
    for a variable
    to a debug message (as well as its value) just by calling:.

    debug(variable)

    Python 3 only, to get in inspect.currentframe() to work as intended
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
            return self.output('%s == %s '%(names, x),'DEBUG')
        else:
            return self.output(str(x),'DEBUG')
#
#
##############################################################################

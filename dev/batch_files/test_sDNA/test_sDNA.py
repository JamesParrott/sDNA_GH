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

""" Test running sDNA Integral with different versions of Python. 


    
    Command line usage:
    
    python test_sDNA [python_version] [sDNA_version] [input_shp] [output_shp] [log_file] [hush|quiet]
    
    Optional Post processing code is run to demonstrate a specific bug with 
    Iron Python 2.7 and sDNA, using PyShp.

    Example output:
        sDNA output shapefile: 15x15randomGrid_sDNA_python.shp.shapeType == 13
        sDNA output shapefile: 15x15randomGrid_sDNA_iron.shp.shapeType == 960051513
 """

import sys
import os
import logging
import itertools
import subprocess

import shapefile


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
logger.setLevel(logging.DEBUG)


pythons_dict = dict(python_2_7 = r'C:\Python27\python.exe'
                   ,iron_python_2_7 = r'C:\Program Files\IronPython 2.7\ipy.exe'
                   #,python_3_10_0 = r'C:\Program Files (x86)\Python_3.10\python-3.10.0-embed-amd64\python.exe'
                   #,python_3_10_1 = r'C:\Program Files\Python310\python.exe'
                   #,python_3_8 = r'C:\Program Files\Python38\python.exe'
                   #,python_3_9 = r'C:\Python39\python.exe'
                   #,qgis_python = r'C:\Program Files\QGIS 3.16.12\bin\python.exe'
                   )
extended_pythons = pythons_dict.copy()              
extended_pythons['python'] = pythons_dict['python_2_7']
extended_pythons['ironpython'] = extended_pythons['iron'] = pythons_dict['iron_python_2_7']


def run_sDNA(python = 'python_2_7'
            ,sDNA = None 
            ,input_shp = None 
            ,output_shp = None
            ,pythons_dict = extended_pythons
            ):
    #type(str, str, str, str/None) -> None
    """ Run sDNA Integral using the specified Python version, input shapefile
        and output shapefile.  
    """
    if sDNA is None:
        sDNA = 'sdnaintegral.py'
        logger.debug('Supplying default sDNA file %s' % sDNA)
    if not os.path.isdir(os.path.dirname(sDNA)):
        paths = os.getenv('PATH')
        sDNA_dirs = [path 
                     for path in paths 
                     if 'sDNA' in path
                    ]
        if sDNA_dirs:
            if len(sDNA_dirs) >= 2:
                logger.warning('No sDNA specified and more than one sDNA in '
                              +'using first item of sDNA_dirs: '
                              +str(sDNA_dirs)
                              )
            sDNA_dir = sDNA_dirs[0]
        else:
            sDNA_dir = r'C:\Program Files (x86)\sDNA\bin'
        sDNA = os.path.join(sDNA_dir, os.path.basename(sDNA))
    if not os.path.isfile(sDNA):
        # if a folder was specified, but no file
        if not os.path.isdir(sDNA):
            sDNA = os.path.dirname(sDNA)
        sDNA = os.path.join(sDNA, 'sdnaintegral.py')

    if input_shp is None:
        input_shp = '15x15randomGrid.shp'

    if output_shp is None:
        name, extension = os.path.splitext(input_shp)
        output_shp = '%s_sDNA_%s%s' % (name, python, extension) 
    
    logger.debug('python = %s, sDNA = %s, input_shp = %s, output_shp = %s' % (python, sDNA, input_shp, output_shp))
    
    command_str = '"%s" -u "%s" -i %s -o %s' % (extended_pythons.get(python, python), sDNA, input_shp, output_shp)
    # e.g. C:\Python27\python.exe -u "C:\Program Files (x86)\sDNA\bin\sdnaintegral.py" -i 15x15randomGrid.shp -o 15x15randomGrid_sDNA_Python2_7.shp
    
    logger.info('Running: %s \n' % command_str)
    output_lines = subprocess.check_output(command_str)
    logger.debug(output_lines)
    
    if 'shapefile' in globals() and os.path.isfile(output_shp):
        with shapefile.Reader(output_shp) as r:
            logger.info(' \n sDNA output shapefile: %s.shapeType == %s \n' %(output_shp, r.shapeType))

def run_all_sDNAs(pythons = None
                 ,sDNAs = None
                 ,input_shp_files = None
                 ,output_shp_files = None
                 ,pythons_dict = extended_pythons
                 ):
    #type(dict, list, list, list) -> None
    """ Test all specified sDNA versions against all specified python versions 
        for all specified input and output file pairs
    """
    
    if not pythons:
        pythons = list(pythons_dict.keys())
        
    if not sDNAs:
        sDNAs = [None]
        
    if not input_shp_files:
        input_shp_files = [None]
        
    if not output_shp_files:
        output_shp_files = [None]
    if isinstance(output_shp_files, str):
        output_shp_files = [output_shp_files]
    if len(output_shp_files) !=  len(input_shp_files):
        output_shp_files = itertools.repeat(output_shp_files[0:1])
    
    output_files = []
    
    for python in pythons:
        for sDNA in sDNAs:
            for input_shp, output_shp in zip(input_shp_files, output_shp_files):
                output_files += [ run_sDNA(python, sDNA, input_shp, output_shp, pythons_dict) ]



if __name__ == '__main__':

    args = sys.argv[1:]

    log_files = [arg 
                 for arg in args 
                 if arg.endswith('.log') and os.path.isdir(os.path.basename(arg))
                ]
    if log_files:
        log_file = log_files[-1]
        args.remove(log_file)
    else:
        log_file = 'test_sDNA_results.log'
    file_handler = logging.FileHandler(os.path.join(os.getcwd(), log_file))
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
        
    be_quiet_args = any(arg  
                        for arg in args
                        if arg.lower().strip('-') in ('hush','quiet')
                       )
    if be_quiet_args:                            
        args.remove(be_quiet_args[-1])
    else:
        logging_level_args = {arg : getattr(logging, arg.upper())
                              for arg in args
                              if arg.lower().strip('-') in ('debug'
                                                           ,'info'
                                                           ,'warning'
                                                           ,'error'
                                                           ,'critical'
                                                           )
                             }
        if logging_level_args:
            logging_level_num = min(logging_level_args.values())
            logging_level = [key 
                             for key, val in logging_level_args.items()
                             if val == logging_level_num
                            ][0]
        else:
            logging_level = 'INFO'
        std_err_handler = logging.StreamHandler(sys.stderr) # default is sys.stderr
        std_err_handler.setLevel(getattr(logging, logging_level.upper()))
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        std_err_handler.setFormatter(formatter)
        logger.addHandler(std_err_handler)

    if 'shapefile' in globals():
        logger.info('Pyshp (shapefile.py) version == %s' % shapefile.__version__)
    else:
        logger.warning('PyShp (shapefile.py) not found. Cannot read shapefile type. ')

    if not args:
        logger.info('Running default test')
        run_all_sDNAs(pythons =('iron', 'python'))
    else:    
        logger.debug('Parsing args')
        input_shp_files = [arg
                           for arg in args
                           if arg.endswith('.shp') and os.path.isfile(arg)
                          ]

        logger.debug('input_shp_files == %s' % input_shp_files)
        

        output_shp_files = [arg
                            for arg in args
                            if arg.endswith('.shp') and (any(  ('output' in arg or
                                                               arg.startswith(os.path.splitext(input_file)[0] + '_')
                                                               )
                                                               for input_file in input_shp_files
                                                            )                                                    
                                                        or not os.path.isfile(arg)
                                                        )
                           ]

        logger.debug('output_shp_files == %s' % output_shp_files)


        sDNAs = [arg
                for arg in args
                if ('sdna' in os.path.basename(arg).lower() 
                    and ((os.path.isfile(arg) 
                        and '.py' in os.path.splitext(arg)[1]
                        ) 
                        or os.path.isdir(arg)
                        )
                    )    
                ]

        logger.debug('sDNAs == %s' % sDNAs)

            
        pythons = [arg 
                   for arg in args
                   if arg.lower() in extended_pythons 
                  ]

        logger.debug('Pythons == %s' % pythons)
        logger.info('Starting test... ')
        output_files = run_all_sDNAs(pythons
                                    ,sDNAs
                                    ,input_shp_files
                                    ,output_shp_files
                                    ,extended_pythons
                                    )
    
    

    


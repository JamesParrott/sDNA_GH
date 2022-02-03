#import logging
print('Hello there!')
from sys import path as sys_path
from os.path import isfile, sep, normpath

import logging,wrapper_logging

default_options=dict(    overwrite_shp_file = True
                        ,suppress_overwrite_warning = False
                        ,platform = 'NT' # in {'NT','win32','win64'} for now
                        ,encoding = 'utf-8'
                        ,rhino_executable = 'C:\Program Files\Rhino 7\System\Rhino.exe'
                        ,python_exe = ''
                        ,number_of_parent_directories_to_search_for_missing_module_files = 2
                        ,logger_file_level = 'DEBUG'
                        ,logger_console_level = 'WARNING'
                        ,logger_custom_level = 'INFO'
                    )

''" logger = wrapper_logger.new_Logger(  __name__
                                    ,sys_path[0]+sep+__name__ + '.log'
                                    ,default_options['logger_file_level']
                                    ,default_options['logger_console_level']
                                    ,a
                                    ,default_options['logger_custom_level']
                                  ) ''"

                                  # set up logging to file - see previous section for more details


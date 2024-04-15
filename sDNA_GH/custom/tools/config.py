

class ConfigManager(sDNA_GH_Tool):

    """ Updates opts objects, and loads and saves config.toml files.  

        All args connected to its input Params are loaded into opts,
        even if go is False.  

        If go is True, tries to save the options to the toml file in 
        save_to (needs to be a valid file path ending 
        in toml) overwriting an existing file, the installation-wide
        options file by default, or if specified by the user e.g. 
        creating a project specific options file.  
        
        Only string keyed str, bool, int, float, list, tuple, and dict 
        values in opts are saved to the toml file on disk.
    """


    class Metas(sDNAMetaOptions):
        config = os.path.join(launcher.USER_INSTALLATION_FOLDER
                             ,launcher.PACKAGE_NAME  
                             ,'config.toml'
                             )

    class Options(PythonOptions):
        pass
    Options.save_to = Metas.config


    param_infos = sDNA_GH_Tool.param_infos + (
                   ('save_to', add_params.ParamInfo(
                             param_Class = Param_FilePath
                            ,Description = ('The name of the .toml file to '
                                           +'save your options to. '
                                           +'Default: %(save_to)s'
                                           )
                            ))
                  ,('python', add_params.ParamInfo(
                             param_Class = Param_FilePath
                            ,Description = ('File path of the Python '
                                           +'executable to run sDNA with, '
                                           +'or its parent folder. '
                                           +'Python is required for sDNA '
                                           +'tools (download link in readme). '
                                           +'Default: %(python)s'
                                           )
                            ))
                  ,('sDNA_paths', add_params.ParamInfo(
                             param_Class = Param_FilePath
                            ,Description = ('File path to the folder of the '
                                           +'sDNA installation to be used with'
                                           +' sDNA_GH. This must contain '
                                           +'%(sDNAUISpec)s.py and '
                                           +'%(runsdnacommand)s.py. '
# metas take priority in all_options_dict so even though there is a name 
# clash, the module names in metas will be interpolated over the Sentinels or
# actual modules in options.
                                           +'Default: %(sDNA_paths)s'
                                           )
                            ))
                  ,('auto_get_Geom', add_params.ParamInfo(
                             param_Class = Param_Boolean
                            ,Description = ('true: Run Read Rhino geometry '
                                           +'before Read User Text.  ' 
                                           +"false: don't. "
                                           +'Default: %(auto_get_Geom)s' 
                                           )
                            )) 
                  ,('auto_read_User_Text', add_params.ParamInfo(
                             param_Class = Param_Boolean
                            ,Description = ('true: Run Read User Text before'
                                           +" Write shapefile.  false: don't. "
                                           +'Default: %(auto_read_User_Text)s' 
                                           )
                            )) 
                  ,('auto_write_Shp', add_params.ParamInfo(
                             param_Class = Param_Boolean
                            ,Description = ('true: Run Write shapefile before'
                                           +" sDNA tools.  false: don't. "
                                           +'Default: %(auto_write_Shp)s' 
                                           )
                            )) 
                  ,('auto_read_Shp', add_params.ParamInfo(
                             param_Class = Param_Boolean
                            ,Description = ('true: Run Read shapefile after'
                                           +" sDNA tools.  false: don't. "
                                           +'Default: %(auto_read_Shp)s' 
                                           )
                            )) 
                  ,('auto_plot_data', add_params.ParamInfo(
                             param_Class = Param_Boolean
                            ,Description = ('true: Run Recolour objects after'
                                           +" Read shapefile.  false: don't. "
                                           +'Default: %(auto_plot_data)s' 
                                           )
                            ))         
                  ,('show_all', add_params.ParamInfo(
                             param_Class = Param_Boolean
                            ,Description = ('true: show all possible input '
                                           +'Params on sDNA tools.  '
                                           +'false: only show required '
                                           +'Params. '
                                           +'Default: %(show_all)s' 
                                           )

                            ))                       

                                               )
    component_inputs = ('save_to' # Primary Meta
                       ,'python'
                       ,'sDNA_paths'
                       ,'auto_get_Geom' 
                       ,'auto_read_User_Text'
                       ,'auto_write_Shp'
                       ,'auto_read_Shp'
                       ,'auto_plot_data'
                       ,'show_all'
                       ,'sync'
                       )

    def __call__(self, opts, local_metas):
        self.debug('Starting class logger')

        metas = opts['metas']
        options = opts['options']
                
        python, sDNA_paths = options.python, metas.sDNA_paths
        save_to = options.save_to

        self.debug('save_to : %s, python : %s, sDNA_paths : %s' 
                  % (save_to, python, sDNA_paths)
                  )


        check_python(opts)
        import_sDNA(opts)

        self.logger.debug('options == %s ' % (opts['options'],))

        # self.logger.debug('opts == %s' % '\n\n'.join(str(item) 
        #                                      for item in opts.items()
        #                                      )
        #           )


        parsed_dict = parse_values_for_toml(opts)   
        parsed_dict['local_metas'] = parse_values_for_toml(local_metas)   
        parsed_dict['metas'].pop('config') # no nested options files

        if 'sDNA' in parsed_dict['metas']:
            parsed_dict['metas'].pop('sDNA') # read only.  auto-updated.

        # self.logger.debug('parsed_dict == %s' % '\n\n'.join(str(item) 
        #                                              for item in parsed_dict.items()
        #                                             )
        #           )

        save_to = options.save_to

        if not isinstance(save_to, basestring):
            msg = 'File path to save to: %s needs to be a string' % save_to
            self.logger.error(msg)            
            raise TypeError(msg)
        if not save_to.endswith('.toml'):
            msg = 'File path to save to: %s needs to end in .toml' % save_to
            self.logger.error(msg)
            raise ValueError(msg)

        if save_to == self.Metas.config:
            self.logger.warning('Saving opts to installation wide '
                               +'file: %s' % save_to
                               )
            parsed_dict['options'].pop('path') # no project-specific paths are
                                               # saved to the installation wide 
                                               # config file's options
            parsed_dict['options'].pop('working_folder')
            parsed_dict['options']['message'] = 'Installation wide user options file. '
        else:
            parsed_dict['options']['message'] = 'Project specific user options file. '

        options_manager.save_toml_file(save_to, parsed_dict)
        
        retcode = 0
        locs = locals().copy()
        return tuple(locs[retval] for retval in self.retvals)

    retvals = ('retcode',)
    component_outputs = ()

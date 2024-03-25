tests_log_file_suffix = '_unit_test_results'





def make_test_running_component_class(Component
                                     ,package_location
                                     ,run_launcher_tests = None
                                     ,output_stream = sys.stderr
                                     ,test_suite = ()
                                     ):
    #type(ghpythonlib.componentbase.executingcomponent, str, Callable) -> TestRunningComponent
    """ Class Decorator to add in package location and replace 
        RunScript with a test launcher. 
    """


    if run_launcher_tests is None:

        output_stream.write('Exit Rhino after tests: %s (env var SDNA_GH_NON_INTERACTIVE)'
                           % ('Yes' if os.getenv('SDNA_GH_NON_INTERACTIVE', '') else 'No')
                           )

        exit = False if os.getenv('SDNA_GH_NON_INTERACTIVE', '').lower() in ('', '0', 'false') else True


        start_dir = package_location #os.path.join(package_location, launcher.package_name)

        if not test_suite:

            output_stream.write('Loading unit tests from: %s \n' % start_dir)
            test_suite = unittest.TestLoader().discover(start_dir = start_dir
                                                        # Non standard pattern ensures 
                                                        # tests requiring Grasshopper are
                                                        # skipped by the default discovery 
                                                        ,pattern = '*test*.py'
                                                        )

        def run_launcher_tests(self, *args):
            """ Set MyComponent.RunScript to this function to run sDNA_GH 
                unit tests in Grasshopper. 
            """            

            log_file_dir = os.path.dirname(checkers.get_path(fallback = package_location))
            if os.path.isfile(log_file_dir):
                log_file_path = os.path.splitext(log_file_dir)[0]
            else:
                log_file_path =  os.path.join(log_file_dir, launcher.PACKAGE_NAME)
            test_log_file_path = log_file_path + tests_log_file_suffix + '.log'
            test_log_file = open(test_log_file_path,'at')
            output_double_stream = FileAndStream(test_log_file, output_stream)

            with output_double_stream as o:

                o.write('Unit test run started at: %s ... \n\n' % asctime())

                result = unittest.TextTestRunner(o, verbosity=2).run(test_suite)
                
                o.write('sDNA API Test Summary')
                o.write('Errors: %s' % (result.errors,))
                o.write('Failures: %s' % (result.failures,))

                if not result.wasSuccessful():
                    # Special string to tell run_api_tests to return non-zero exit code
                    o.write('SDNA_GH_API_TESTS_FAILED')


            if exit:
                exit_Rhino()
                # exit_Rhino(23)
                # exit_Rhino(not result.wasSuccessful())
                
            
            # return (False, ) + tuple(repeat(None, len(self.Params.Output) - 1))
            # False is for "ok" not "output"
            return tuple(repeat(None, len(self.Params.Output) - 1))



    class TestRunningComponent(Component):
        _RunScript = Component.RunScript
        RunScript = run_launcher_tests


    return TestRunningComponent

def make_noninteractive_test_running_component_class(Component
                                                    ,package_location
                                                    ,test_suite
                                                    ,port=9999
                                                    ,host='127.0.0.1'
                                                    ):
    udp_stream = UDPStream(port, host)
    return make_test_running_component_class(Component
                                            ,package_location
                                            ,output_stream = udp_stream
                                            ,test_suite = test_suite
                                            )
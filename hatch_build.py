import os
import sys
import subprocess
import pathlib

import Cheetah_GH

# https://discuss.python.org/t/custom-build-steps-moving-bokeh-off-setup-py/16128/3
from hatchling.builders.hooks.plugin.interface import BuildHookInterface

REPO_DIR = pathlib.Path(__file__).parent

BUILDER_GH = REPO_DIR / 'dev' / 'sDNA_build_components.gh'

if not BUILDER_GH.is_file():
    raise FilePathError(f'Builder file not found at: {BUILDER_GH=}')

class CustomHook(BuildHookInterface):
    def initialize(self, version, build_data):
        if self.target_name in ('wheel', 'bdist'):
            Cheetah_GH.run_GH_file(
                 gh_file=BUILDER_GH
                ,extra_env_vars = {
                     # Pass in the path to sDNA_GH's deps 
                     # installed by pip in its build environment
                     'SDNA_GH_BUILD_DEPS' : sys.path[-1]
                    # ,'CHEETAH_GH_NON_INTERACTIVE' : 'False'
                    }
                )


    
    def finalize(self, version, build_data, artifact_path):
        src_components_dir = (REPO_DIR / 'src' 
                                       / 'sDNA_GH' 
                                       / 'components'
                                       / 'automatically_built'
                             )
        for path in src_components_dir.glob('*.ghuser'):
            path.unlink()
        
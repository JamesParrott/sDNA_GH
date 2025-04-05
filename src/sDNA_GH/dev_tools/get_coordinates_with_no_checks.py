import Rhino
import scriptcontext as sc

import System

from collections import defaultdict
from sDNA_GH.skel.tools.helpers.rhino_gh_geom import (
                                            get_geom_and_source_else_leave
                                           ,get_points_from_obj
                                           )
from sDNA_GH.skel.tools.helpers.funcs import is_uuid



ghenv.Component.ToggleObsolete(False)


points_types = defaultdict(list)

for obj in x: #[0]:
    
    geom, source = get_geom_and_source_else_leave(obj)
    try:
        points_list = get_points_from_obj(geom)
    except:
        points_list = 'Error when getting points'
    
    if points_list == 'Error when getting points':
        num_type_names = container_type_names = points_list
    else:
        num_type_names = frozenset(
                               type(coord).__name__
                               for point in points_list
                               for coord in point
                              ) 
                              
        
        container_type_names = frozenset(
                               type(point).__name__
                               for point in points_list
                              ) 
    
    points_types[
        (type(obj).__name__,
         type(geom).__name__,
         container_type_names,
         num_type_names,
        )].append(obj)
    
    
a = '\n'.join('# of (Obj type: %s, geom_type: %s, converts to: %s containing: %s) : %s' % (k[0],
                                                                                           k[1],
                                                                                           ', '.join(k[2]),
                                                                                           ', '.join(k[3]), 
                                                                                           len(v)
                                                                                           ) 
               for k, v in points_types.items()
             )
             
print(a)
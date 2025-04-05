from collections import defaultdict
from sDNA_GH.skel.tools.helpers.rhino_gh_geom import get_geom_and_source_else_leave



ghenv.Component.ToggleObsolete(False)


obj_types = defaultdict(list)

for obj in x:
    geom, source = get_geom_and_source_else_leave(obj)
    
    obj_types[(type(obj).__name__, type(geom).__name__)].append(obj)
    
    
a = '\n'.join('# of (Obj type: %s, geom_type: %s) : %s' % (k + (len(v),) )
               for k, v in obj_types.items()
             )
             
print(a)
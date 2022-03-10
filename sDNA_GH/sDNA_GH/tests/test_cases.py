def create_random_grid_network():
    import rhinoscriptsyntax as rs
    import scriptcontext
    import Rhino


    def grid_point_coords(n, m):
        for y in xrange(n):
            for x in xrange(m):
                yield x, y

    def make_poly_line(x1, y1, x2, y2, store,offset = [x, y]):
        if random_num() > p:
            x1 += offset[0]; x2 += offset[0]
            y1 += offset[1]; y2 += offset[1]
            store += [rs.AddLine([x1, y1, 0], [x2, y2, 0])]

    if Go == True:  #if Go is canonical in Rhino.  ==True stops execution on
                # input of a truthy variable
        M, N = map(floor,[M, N])
        geometries = []
    #    rhino_brep = []
        for col,row in grid_point_coords(N, M):
                if col < M-1:
                    make_poly_line(col, row, col+1, row, geometries)
                if row < N-1:
                    make_poly_line(col, row, col, row+1, geometries)
        a1 = geometries                
        #        Baking code from ScottD
        #        https://developer.rhino3d.com/guides/rhinopython/ghpython-bake/
        # Baking geometry 
        #scriptcontext.doc = Rhino.RhinoDoc.ActiveDoc
        #for geometry in geometries:
        #    doc_object = scriptcontext.doc.Objects.Find(geometry)
        #    rhino_brep += [scriptcontext.doc.Objects.Add(doc_object)]
        #if not rs.IsLayer(L):
        #    rs.AddLayer(L)
        #rs.ObjectLayer(rhino_brep, L)
        #scriptcontext.doc = ghdoc
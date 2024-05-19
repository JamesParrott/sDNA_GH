def AddPolyline(points, replace_id=None):
    """Adds a polyline curve to the current model
    Parameters:
      points ([guid|point, guid|point, ...]): list of 3D points. Duplicate, consecutive points will be
               removed. The list must contain at least two points. If the
               list contains less than four points, then the first point and
               last point must be different.
      replace_id (guid, optional): If set to the id of an existing object, the object
               will be replaced by this polyline
    Returns:
      guid: id of the new curve object if successful
    Example:
      import rhinoscriptsyntax as rs
      points = rs.GetPoints(True)
      if points: rs.AddPolyline(points)
    See Also:
      IsPolyline
    """
    points = rhutil.coerce3dpointlist(points, True)
    if replace_id: replace_id = rhutil.coerceguid(replace_id, True)
    rc = System.Guid.Empty
    pl = Rhino.Geometry.Polyline(points)
    pl.DeleteShortSegments(scriptcontext.doc.ModelAbsoluteTolerance)
    if replace_id:
        if scriptcontext.doc.Objects.Replace(replace_id, pl):
            rc = replace_id
    else:
        rc = scriptcontext.doc.Objects.AddPolyline(pl)
    if rc==System.Guid.Empty: raise Exception("Unable to add polyline to document")
    scriptcontext.doc.Views.Redraw()
    return rc


def AddPoint(point, y=None, z=None):
    """Adds point object to the document.
    Parameters:
      point (point): a point3d or list(x,y,z) location of point to add
    Returns:
      guid: identifier for the object that was added to the doc
    Example:
      import rhinoscriptsyntax as rs
      rs.AddPoint( (1,2,3) )
    See Also:
      IsPoint
      PointCoordinates
    """
    if y is not None: point = Rhino.Geometry.Point3d(point, y, z or 0.0)
    point = rhutil.coerce3dpoint(point, True)
    rc = scriptcontext.doc.Objects.AddPoint(point)
    if rc==System.Guid.Empty: raise Exception("unable to add point to document")
    scriptcontext.doc.Views.Redraw()
    return rc
    
    

def AddPoints(points):
    """Adds one or more point objects to the document
    Parameters:
      points ([point, ...]): list of points
    Returns:
      list(guid, ...): identifiers of the new objects on success
    Example:
      import rhinoscriptsyntax as rs
      points = rs.GetPoints(True, True, "Select points")
      if points: rs.AddPoints(points)
    See Also:
      AddPoint
      AddPointCloud
    """
    points = rhutil.coerce3dpointlist(points, True)
    rc = [scriptcontext.doc.Objects.AddPoint(point) for point in points]
    scriptcontext.doc.Views.Redraw()
    return rc



def AddMesh(vertices, face_vertices, vertex_normals=None, texture_coordinates=None, vertex_colors=None):
    """Add a mesh object to the document
    Parameters:
      vertices ([point, ...]) list of 3D points defining the vertices of the mesh
      face_vertices ([[number, number, number], [number, number, number, number], ...]) list containing lists of 3 or 4 numbers that define the
                    vertex indices for each face of the mesh. If the third a fourth vertex
                     indices of a face are identical, a triangular face will be created.
      vertex_normals ([vector, ...], optional) list of 3D vectors defining the vertex normals of
        the mesh. Note, for every vertex, there must be a corresponding vertex
        normal
      texture_coordinates ([[number, number], [number, number], [number, number]], ...], optional): list of 2D texture coordinates. For every
        vertex, there must be a corresponding texture coordinate
      vertex_colors ([color, ...]) a list of color values. For every vertex,
        there must be a corresponding vertex color
    Returns:
      guid: Identifier of the new object if successful
      None: on error
    Example:
      import rhinoscriptsyntax as rs
      vertices = []
      vertices.append((0.0,0.0,0.0))
      vertices.append((5.0, 0.0, 0.0))
      vertices.append((10.0, 0.0, 0.0))
      vertices.append((0.0, 5.0, 0.0))
      vertices.append((5.0, 5.0, 0.0))
      vertices.append((10.0, 5.0, 0.0))
      vertices.append((0.0, 10.0, 0.0))
      vertices.append((5.0, 10.0, 0.0))
      vertices.append((10.0, 10.0, 0.0))
      faceVertices = []
      faceVertices.append((0,1,4,4))
      faceVertices.append((2,4,1,1))
      faceVertices.append((0,4,3,3))
      faceVertices.append((2,5,4,4))
      faceVertices.append((3,4,6,6))
      faceVertices.append((5,8,4,4))
      faceVertices.append((6,4,7,7))
      faceVertices.append((8,7,4,4))
      rs.AddMesh( vertices, faceVertices )
    See Also:
      MeshFaces
      MeshFaceVertices
      MeshVertexNormals
      MeshVertices
    """
    mesh = Rhino.Geometry.Mesh()
    for a, b, c in vertices: mesh.Vertices.Add(a, b, c)
    for face in face_vertices:
        if len(face)<4:
            mesh.Faces.AddFace(face[0], face[1], face[2])
        else:
            mesh.Faces.AddFace(face[0], face[1], face[2], face[3])
    if vertex_normals:
        count = len(vertex_normals)
        normals = System.Array.CreateInstance(Rhino.Geometry.Vector3f, count)
        for i, normal in enumerate(vertex_normals):
            normals[i] = Rhino.Geometry.Vector3f(normal[0], normal[1], normal[2])
        mesh.Normals.SetNormals(normals)
    if texture_coordinates:
        count = len(texture_coordinates)
        tcs = System.Array.CreateInstance(Rhino.Geometry.Point2f, count)
        for i, tc in enumerate(texture_coordinates):
            tcs[i] = Rhino.Geometry.Point2f(tc[0], tc[1])
        mesh.TextureCoordinates.SetTextureCoordinates(tcs)
    if vertex_colors:
        count = len(vertex_colors)
        colors = System.Array.CreateInstance(System.Drawing.Color, count)
        for i, color in enumerate(vertex_colors):
            colors[i] = rhutil.coercecolor(color)
        mesh.VertexColors.SetColors(colors)
    rc = scriptcontext.doc.Objects.AddMesh(mesh)
    if rc==System.Guid.Empty: raise Exception("unable to add mesh to document")
    scriptcontext.doc.Views.Redraw()
    return rc

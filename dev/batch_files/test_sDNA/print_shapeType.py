import shapefile
with shapefile.Reader('t5sDNA') as r:
	print(r.shapeType)
import shapefile
with shapefile.Reader('t5sDNA') as r:
	logger.debug(r.shapeType)
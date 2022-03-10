ipy create_random_grid_network.py
ipy -u "C:\Program Files (x86)\sDNA\bin\sdnaprepare.py" -i test_random_grid.shp -o t5_prepped.shp
ipy -u "C:\Program Files (x86)\sDNA\bin\sdnaintegral.py" -i test_random_grid.shp -o t5sDNA.shp
ipy print_shapeType.py
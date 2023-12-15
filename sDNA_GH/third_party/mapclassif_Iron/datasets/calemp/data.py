from os.path import abspath, dirname, join



def load():


    # last column
    # return df["emp/sq km"]

    filepath = join(dirname(abspath(__file__)), "calempdensity.csv")

    with open(filepath, 'rt') as f:
        
        lines = iter(f)

        # skip header line
        next(lines)

        for line in lines:
            emp_density = line.rpartition(',')[2]
            
            yield float(emp_density)



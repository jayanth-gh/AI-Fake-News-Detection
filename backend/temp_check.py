import os
try:
    import pandas as pd
    import sklearn
    print('pandas', pd.__version__, 'sklearn', sklearn.__version__)
except Exception as e:
    print('imports failed', e)
print('cwd', os.getcwd())
print('Fake.csv exists', os.path.exists('data/News _dataset/Fake.csv'))
print('True.csv exists', os.path.exists('data/News _dataset/True.csv'))
try:
    import matplotlib
    print('matplotlib', matplotlib.__version__)
except Exception as e:
    print('matplotlib import failed', e)

import pandas as pd

def insert_rows_safely(dataframe, row_number, rows):
    assert len(rows) > 0

    delta = 0.9 / len(rows)
    for idx in range(len(rows)):
        dataframe.loc[row_number + delta * idx + 0.05] = rows[idx]

    dataframe.sort_index(inplace=True)
    dataframe.index = [*range(dataframe.shape[0])]

    return dataframe

df = pd.DataFrame( [ [*range(n, n+5)] for n in range(0, 35, 5) ])
rows = [ [*range(n, n+5)] for n in range(100, 135, 5) ]

id_org = id(df)
df1 = insert_rows_safely(df, -3, rows)
print( id_org, id(df1) )
pass
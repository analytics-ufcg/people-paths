#Libraries

#Python Libs
import sys
import os
import glob
import traceback
from datetime import datetime
import time

#Data Analysis Libs
import pandas as pd
import numpy as np

#Constants
MIN_NUM_ARGS = 7

FREQS_ODMAT_SUFFIX = '_freqs_od_matrix.csv'
NORMALIZED_ODMAT_SUFFIX = '_norm_od_matrix.csv'


#Functions
def printUsage():
    print("Usage: " + sys.argv[0] + " <trips_filepath> <prefix> <origin_col> <dest_col> <id_col> <output_folderpath>")

#Main
if __name__ == "__main__":
    if len(sys.argv) < MIN_NUM_ARGS:
        print("Error: Wrong Usage!")
        printUsage()
        sys.exit(1)

trips_filepath = sys.argv[1]
prefix = sys.argv[2]
origin_col = sys.argv[3]
dest_col = sys.argv[4]
id_col = sys.argv[5]
output_folderpath = sys.argv[6]


trips_data = pd.read_csv(trips_filepath)

od_matrix_df = trips_data.groupby([origin_col,dest_col]).agg({id_col:'count'}).reset_index() \
                                            .rename(index=str, columns={id_col:aggregation_col})
od_matrix_freqs = od_matrix_df.pivot(index=origin_col,columns=dest_col,values=aggregation_col)

od_matrix_freqs.to_csv(output_folderpath + prefix + FREQS_ODMAT_SUFFIX)

od_matrix_norm_freqs = od_matrix_freqs/od_matrix_freqs.values.sum()

od_matrix_norm_freqs.to_csv(output_folderpath + prefix + NORMALIZED_ODMAT_SUFFIX)






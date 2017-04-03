from __future__ import print_function

import sys
from operator import add
from csv import reader
from pyspark import SparkContext


if __name__ == "__main__":
    sc = SparkContext()
    lines = sc.textFile(sys.argv[1], 1)
    lines = lines.mapPartitions(lambda x: reader(x))
    
    header = lines.first() #extract header
    data = lines.filter(lambda x: x != header) 
#update column number
    col_num=0
    
    
    def assign_types(rows, col_num):
#creates rdd with key as col name, values {data_type,semantic_type,valid_ind}
        try:
            value = int(rows[col_num])
            data_type = 'INT'
        except ValueError:
            data_type = 'OTHER' 
        
        if len(str(rows[col_num])) == 9:
             semantic_type = 'COMPLAINT NUMBER'
             valid_ind = 'VALID'
        else:
             semantic_type = 'UNKONWN'
             valid_ind = 'INVALID/OUTLIER'
        return (header[col_num],(rows[col_num],data_type,semantic_type,valid_ind))            
             
    output = data.map(lambda x: assign_types(x, col_num))
    output.saveAsTextFile('type_%s.out' %(header[col_num]))
    
    #aggregate summary stats
    data_type = output.map(lambda x: ('data_type, %s' %(x[1][1]),1)).reduceByKey(add)
    semantic_type = output.map(lambda x: ('semantic_type, %s' %(x[1][2]),1)).reduceByKey(add)
    valid_ind = output.map(lambda x: ('valid_ind, %s' %(x[1][3]),1)).reduceByKey(add)
    summary = sc.union([data_type, semantic_type, valid_ind]).sortByKey()
    summary.saveAsTextFile('summary_%s.out' %(header[col_num]))
    


    sc.stop()

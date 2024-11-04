arry1 = ["n","o", '1', ':', '56.64','mm',':',"18.8",'mm',':','19.3','kp']


if "1" in arry1 :
    dataindex = arry1.index("mm")
    print(dataindex)
    print(arry1[dataindex-1])
    print(arry1[dataindex+2])
from datetime import datetime
import psycopg2, os, re

def initdb():
    # Menghubungkan ke database
    mydb = psycopg2.connect(
        host=os.environ['DB'].split(" ")[0],
        user=os.environ['DB'].split(" ")[2],
        password=os.environ['DB'].split(" ")[3],
        database=os.environ['DB'].split(" ")[4],
        port=os.environ['DB'].split(" ")[1]
    )
    return mydb

def GetEquipID(srn):
    # Mendapatkan ID peralatan dari tabel lookup
    mydb = initdb()
    mycursor = mydb.cursor()
    
    sql = "SELECT equipid FROM srnlookup WHERE srn = '"+str(srn)+"'"
    mycursor.execute(sql)
    
    try:
        equipid = mycursor.fetchall()[0][0]
    except:
        equipid = 'N/A'
    
    return equipid

def logdata(tabledest, key):
    # Melakukan logging data
    mydb = initdb()
    mycursor = mydb.cursor()
    
    val = (tabledest, key)
    sql = "INSERT INTO datalog (equiptable, key) VALUES (%s, %s)"
    mycursor.execute(sql, val)
    mydb.commit()
    
    return

def SendData(cols, val, tabledest):
    # Mengirim data ke database
    mydb = initdb()
    mycursor = mydb.cursor()
    
    sql = "INSERT INTO "+tabledest+" "+cols+" returning id"
    val = list((re.sub('[^ -~]+','',str(x)) for x in val))
    val = tuple([x for x in val if x != '' and x != ' '])
    mycursor.execute(sql, val)
    mydb.commit()
    print(val)
    
    out = mycursor.fetchone()[0] 
    mydb.close()
    
    logdata(tabledest, out)
    
    return out

def ParseSPBHeader(serial, deviceid):
    # Parsing data header dari timbangan Sartorius
    serial = serial.split("\n")[1:-1]

    date = serial[0][:11]
    time = serial[0][-5:]
    srn = serial[3].replace("SerNo.    ","")
    bac = serial[4][-8:]
    apc = serial[5][-8:]
    equipid = GetEquipID(srn)
    
    cols = """("equipid", "date", "time", "bac", "apc") VALUES (%s, %s, %s, %s, %s)"""
    val = (equipid, date, time, bac, apc)
    tabledest = "spb_cycles"
    send = SendData(cols, val, tabledest)
    
    # Mengirim data ke tabel staging
    stgcols = """(datatable, "key", "date", "time", equipid, data, deviceid) VALUES (%s, %s, %s, %s, %s, %s, %s)"""
    staging = (tabledest, send, val[1], val[2], val[0], "Sartorius PBE Weighing", deviceid)
    SendData(stgcols, staging, "staginginfo")
    print(send)
    
    return send

def ParseSPBProcess(serial, weighingid, deviceid):
    # Parsing data proses dari timbangan Sartorius
    serial = serial.split("\n")[:-1]
    count = int(len(serial)/3)

    for x in range(0, count):
        date = serial[x*3][:11]
        time = serial[x*3][-9:]
        weight = float(serial[(x*3)+1].replace("G","").replace("+","").replace("g","").strip())
        val = (weighingid, date, time, weight)
        print(val)
        
        cols = """("weighing_id", "date", "time", "weight") VALUES (%s, %s, %s, %s)"""
        tabledest = "spb_process"
        SendData(cols, val, tabledest)
    
    return val

# -*- coding: UTF-8 -*-
import getopt, datetime, time, sys, os.
from cookData import DBcall, readData_hash, is_match


def intro(json):
    datahash = readData_json(json)
    keys = tbl[0].split("\t")
    for r in tbl[1:]:  # 
        if is_match('A_S', idata):
            DBcall('A_S').updateDatapull(idata)
        else:
            DBcall('A_S').loadData([data])

def instances(json):
    datahash = readData_json(json)
    keys = tbl[0].split("\t")
    for r in tbl[1:]:  # 
        if is_match('A_S', idata):
            DBcall('A_S').updateDatapull(idata)
        else:
            DBcall('A_S').loadData([data])

def main(argv):
    pid = os.getpid()
    try:
        opts, arg = getopt.getopt(argv, "t:", ["type="])
    except getopt.GetoptError:
        sys.exit(2)
    for opt, arg in opts:          
        if opt in ("-t", "--type") and arg == "i":
            intro('../json/Initial_load_A_S.json')
        else:
            points('../json/Load_A_S_I.json')

if __name__ == '__main__':
    main(sys.argv[1:])

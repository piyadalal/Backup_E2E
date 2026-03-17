


import sys, getopt
import StormtestRunnerWebClient  # @UnresolvedImport
from PostgresDB import WebReportingDB  # @UnresolvedImport
from pprint import pprint


def usage():
    print ('-StormtestRunner.py -u <user name> -s <script> -d <comma separated dutids> [-a "arguments"]')
    sys.exit(2)


def processArgs(argv):
    userName = None
    script = None
    dutids = None

    try:
        opts, args = getopt.getopt(argv, "hu:s:d:a:")
    except getopt.GetoptError as err:
        usage()

    if len(argv) == 0:
        usage()

    pargs = None
    for opt, arg in opts:
        # print "opt=%s arg=%s" % (opt,arg)
        if opt == '-h':
            usage()
        elif opt == '-u':
            userName = arg
        elif opt == '-s':
            script = arg
        elif opt == '-d':
            dutids = arg
        elif opt == '-a':
            pargs = arg.replace("+", "-")

    main(userName, script, dutids, pargs)


def checkSlots(dutids):
    retStr = ""
    db = WebReportingDB()
    rc = db.connect()
    if not rc:
        return retStr

    stwc = StormtestRunnerWebClient.StormtestRunnerWebClient(None, None)
    dutArray = dutids.split(",")
    for dutID in dutArray:
        # print dutID
        sqlcmd = "select * from dut where dut_id = %s" % (dutID)
        dbRowlist = db.getDataDict(sqlcmd)
        # pprint(dbRowlist)
        slotID = dbRowlist[0]['name']
        server = dbRowlist[0]['server']
        if server.startswith("8"):
            slotID = int(dbRowlist[0]['name'])
        if not isinstance(slotID, int):
            # pprint(dbRowlist[0])
            slotID = dbRowlist[0]['slot']
        slotInfo = stwc.getSlotIDstatus(slotID)
        slotStaus = slotInfo[0]
        if slotStaus == 1:
            print ("%s reserved" % (slotID))
            continue
        if len(retStr) == 0:
            retStr = "%s" % (dutID)
        else:
            retStr = "%s,%s" % (retStr, dutID)

    return retStr


def main(userName, script, dutids, pargs):
    url = "http://tech-hv16-1"
    port = "8001"
    testing = False
    if testing:
        dutids = "3318,3319"
        userName = "molo01"
        script = "tech/python/mbi/joe_test_script.py"

    dutids = checkSlots(dutids)
    if len(dutids) == 0:
        return

    # print "args: [%s]" % (pargs)
    stwc = StormtestRunnerWebClient.StormtestRunnerWebClient(url, int(port))
    stwc.run(userName, script, dutids, pargs)


def testFunc():
    dutids = "12432"
    dutids = checkSlots(dutids)
    print ("dutids: %s" % (dutids))


def testArgs():
    sys.argv.append("-u")
    sys.argv.append("molo01")
    sys.argv.append("-s")
    sys.argv.append("python3_scripts/basic/stb_checkHardware.py")
    sys.argv.append("-d")
    sys.argv.append("12432")


if __name__ == '__main__':
    # testArgs()
    # testFunc()
    processArgs(sys.argv[1:])

# coding = utf-8
# script owner & author: You Zhang;

from optparse import OptionParser
import re,sys

#wait for extend
def traceLog(info):
    print info

    #---------func des---------------#
    #    generate the option and help
    # params : none
    # out:  (options, args)
    #---------end---------------#
def makeOptions():
    #dataStruct : option => help;
    errorFlag = 0
    optionsDict = {
        "startTime"  :"set the start time to calculate in the record File\neg: 2014-05-30 07:34:19",
        "endTime"    :"set the end time to calculate in the record File\neg: 2014-05-30 07:24:11",
        "recordFile" :"set the record file you want to calculate,please input the absolute path\neg: D:\\event_DL_eNB66.txt",
        "highestRate":"set the max threshold to abandon the data\neg: 20000000",
        "lowestRate" :"set the min threshold to abandon the data\type(parser.parse_args()[0])neg: 0",
        "direction"  :"set the upload or download\ndl --> calculate the download data\nul --> calculate the upload data",
        "interval"   :"set the interval time(seconds) to calculate the data\neg: 60",
        "offset"     :"set the data item you want to ignore\neg: 2parser.parse_args() --> abandon the first 2 items and the last 2 items"
    }
    parser = OptionParser()
    for optionName in optionsDict.keys():
        option = "--" + optionName
        parser.add_option(option,dest = optionName,help = optionsDict[optionName])

    (options,args) = parser.parse_args()
    return (options,args)

def processOptions(options):
    errorFlag = 0
    if( options.lowestRate == None ):
        traceLog("Error:lowestRate cannot be None,input eg: --lowestRate 0")
        errorFlag = 1
    if( options.highestRate == None ):
        traceLog("Error:highestRate cannot be None,input eg: --highestRate 200000000")
        errorFlag = 1
    if( options.direction == None ):
        traceLog("Error:direction cannot be None,input eg:--direction dl")
        errorFlag = 1
    if( options.startTime == None ):
        traceLog("Error:start time cannot be None,input eg:--startTime 2014-05-30 07:24:11.319")
        errorFlag = 1
    if( options.endTime == None ):
        traceLog("Error:end time cannot be None,input eg:--endTime 2014-05-30 07:24:11.319")
        errorFlag = 1
    if( options.interval == None ):
        traceLog("Error:interval cannot be None,input eg:--interval 60")
        errorFlag = 1
    if( options.recordFile == None ):
        traceLog("Error:recordFile cannot be None,input eg: --recordFile event_DL_eNB66.txt")
        errorFlag = 1
    if( options.offset == None ):
        options.offset = 0
    if( errorFlag ):
        sys.exit(1)

#---------class des---------------
# it is a data trace machine to calculate the maxRate minRate averageRate in the time you set.
# options,args
# out:  maxRate minRate averageRate
#---------end--------------------
class DataTracer(object):

    def __init__(self,options,args):
        self.initConfig()
        self.startTime = options.startTime
        self.endTime = options.endTime
        self.recordFile = options.recordFile
        self.direction = options.direction.lower()
        self.interval = int(options.interval)
        self.offset = int(options.offset)
        self.highestRate = int(options.highestRate)
        self.lowestRate = int(options.lowestRate)

        self.args = args
        self.startTimePatten = None
        self.endTimePatten = None
        self.dataSum = 0
        self.timeSum = 0
        self.averageRate = 0

    def initConfig(self):
        #this config may changed by different version of netMeter log file
        self.perOffset = 69              # 69 char to locate per line


    #---------func des---------------
    #    generate the patten of date
    # params : (options,args)
    # out:  startDatePatten,endDatePatten
    #---------end--------------------
    def changeTimeFormat(self):
        STYear = self.startTime[0:4]
        STMonth = self.startTime[5:7]
        STDay = self.startTime[8:10]
        ETYear = self.endTime[0:4]
        ETMonth = self.endTime[5:7]
        ETDay = self.endTime[8:10]
        STFormat = ''.join([STMonth,'/',STDay,'/',STYear,"   ",self.args[0][0:5]])
        ETFormat = ''.join([ETMonth,'/',ETDay,'/',ETYear,"   ",self.args[1][0:5]])
        return STFormat,ETFormat


    #---------func des---------------
    # 1.match the upload data or download data
    # 2.calculate the max min average
    # params :
    # out:  max min average
    #---------end--------------------
    def process(self):
        try:
            with open(self.recordFile) as file:
                lines = file.read()
                intervalNetMeter = self.getRecordFileProp(lines)
                if( self.interval != intervalNetMeter):
                    traceLog("fail to process because interval you set is not matched with intervalNetMeter:{0}".format(intervalNetMeter))
                    sys.exit(1)

                (startPos,endPos) = self.localStartEndPos(lines)
                ratePerInterval = self.getRate(lines,startPos)
                rateList = [ratePerInterval]
                self.maxRate = ratePerInterval
                self.minRate = ratePerInterval
                while( startPos <= endPos):
                    self.calResult(ratePerInterval)
                    startPos = startPos + self.perOffset
                    ratePerInterval = self.getRate(lines,startPos)
                    rateList.append(ratePerInterval)
                for rate in rateList:
                    traceLog(rate)
                try:
                    self.averageRate = self.dataSum * 10  / self.timeSum
                except ZeroDivisionError:
                    self.averageRate = 0
                    traceLog("none of the data matched the standard so the time is 0")
        except IOError:
            traceLog("can not open the record file,please check the property of the file")
            sys.exit(1)

     #---------func des---------------
     # local the start position of the data
     # params : lines
     # out:  (startPos,endPos)
     #---------end--------------------
    # -1 => fail to find the position of time
    def localStartEndPos(self,lines):
        startPos = -1
        endPos = -1
        startTime,endTime = self.changeTimeFormat()
        startPos = lines.index(startTime) + self.perOffset * self.offset
        endPos = lines.index(endTime) - self.perOffset * self.offset
        if( startPos == -1 or endPos == -1 ):
            traceLog("fail to find the position of time")
            sys.exit(1)
        elif( startPos > endPos ):
            traceLog("Error: end time must be later than the start time")
            sys.exit(1)
        return (startPos,endPos)

     #---------func des---------------
     #  get the upload data
     # params : lines,startPos
     # out:  dataUL or dataDL
     #---------end--------------------
    def getRate(self,lines,startPos):
        matchCase = "\d{2}/\d{2}/\d{4}   \d{2}:\d{2}:\d{2}\s+(\d+)\s+(\d+)"
        patten = re.compile(matchCase)
        if( self.direction == "dl" ):
            matchedItem = patten.match(lines,startPos)
            dataDL = int(matchedItem.group(1))
            if( dataDL < self.highestRate and dataDL > self.lowestRate ):
                return dataDL
            else:
                return -1
        elif( self.direction == "ul" ):
            matchedItem = patten.match(lines,startPos)
            dataUL = int(matchedItem.group(2))
            if( dataUL < self.highestRate and dataUL > self.lowestRate ):
                return dataUL
            else:
                return -1
        else:
            traceLog("Error:your option of direction has error,eg: dl ul")
            sys.exit(1)

     #---------func des---------------
     # calculate the max min sum
     # params : ratePerInterval
     # out:  max min sum
     #---------end--------------------
    def calResult(self,ratePerInterval):
        if( ratePerInterval != -1 ):
            self.dataSum += ratePerInterval
            self.timeSum += self.interval
            if( ratePerInterval > self.maxRate ):
                self.maxRate = ratePerInterval
            if( ratePerInterval < self.minRate ):
                self.minRate = ratePerInterval
        else:
            traceLog("ratePerInterval is not in the range [highestRate:lowestRate]")

     #---------func des---------------
     #  get record file property: interval info & ip info
     # params : lines
     # out:  max min sum
     #---------end--------------------

    def getRecordFileProp(self,lines):
        matchedCase = "Interval:  (\d+)"
        pos = lines.index("Interval")
        patten = re.compile(matchedCase)
        intervalNetMeter = int(patten.match(lines,pos).group(1))
        return intervalNetMeter

if __name__ == "__main__":
    (options,args) = makeOptions()
    processOptions(options)
    myDataTracer = DataTracer(options,args)
    myDataTracer.process()
    print '\n{0} {1} ----- {2} {3}\n'.format(options.startTime,args[0],options.endTime,args[1])
    print 'max:{0} min:{1} average: {2}'.format(myDataTracer.maxRate,myDataTracer.minRate,myDataTracer.averageRate)




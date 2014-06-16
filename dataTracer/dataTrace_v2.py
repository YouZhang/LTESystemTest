# coding = utf-8
# script owner & author: You Zhang;

from optparse import OptionParser
import re

# global vars & hard code things

    #---------func des---------------#
    #    generate the option and help
    # params : none
    # out:  (options, args)
    #---------end---------------#
def makeOptions():
    #dataStruct : option => help;
    optionsDict = {
        "startTime"  :"set the start time to calculate in the record File\neg: 2014-05-30 07:34:19",
        "endTime"    :"set the end time to calculate in the record File\neg: 2014-05-30 07:24:11",
        "recordFile" :"set the record file you want to calculate,please input the absolute path\neg: D:\\event_DL_eNB66.txt",
        "highestRate":"set the max threshold to abandon the data\neg: 20000000",
        "lowestRate" :"set the min threshold to abandon the data\neg: 0",
        "direction"  :"set the upload or download\ndl --> calculate the download data\nul --> calculate the upload data",
        "interval"   :"set the interval time(seconds) to calculate the data\neg: 60",
        "offset"     :"set the data item you want to ignore\neg: 2 --> abandon the first 2 items and the last 2 items"
    }
    parser = OptionParser()
    for optionName in optionsDict.keys():
        option = "--" + optionName
        parser.add_option(option,dest = optionName,help = optionsDict[optionName])

    (options,args) = parser.parse_args()

    return (options,args)


#---------class des---------------
# it is a data trace machine to calculate the maxRate minRate averageRate in the time you set.
# options,args
# out:  maxRate minRate averageRate
#---------end--------------------
class DataTracer(object):

    # __options = None
    # __args = None
    # __perOffset = None
    # __DLDataStartPos = None
    # __DLDataEndPos = None
    # __ULDataStartPos = None
    # __ULDataEndPos = None

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
        self.pattenGen()

    def initConfig(self):
        #this config may changed by different version of netMeter log file
        self.perOffset = 69              # 70 char to locate per line
        self.DLDataStartPos = 21         # 21 char to locate Download data start position
        self.DLDataEndPos = 38           # 38 char to locate Download data end position
        self.ULDataStartPos = 39         # 38 char to locate upload data start position
        self.ULDataEndPos = 53           # 53 char to locate upload data end position


    #---------func des---------------
    #    generate the patten of date
    # params : (options,args)
    # out:  startDatePatten,endDatePatten
    #---------end--------------------
    def pattenGen(self):
        STYear = self.startTime[0:4]
        STMonth = self.startTime[5:7]
        STDay = self.startTime[8:10]
        ETYear = self.endTime[0:4]
        ETMonth = self.endTime[5:7]
        ETDay = self.endTime[8:10]
        STFormat = ''.join([STMonth,'/',STDay,'/',STYear,"   ",self.args[0][0:5]])
        ETFormat = ''.join([ETMonth,'/',ETDay,'/',ETYear,"   ",self.args[1][0:5]])
        self.startTimePatten = re.compile(STFormat)
        self.endTimePatten = re.compile(ETFormat)


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
                (startPos,endPos) = self.localStartEndPos(lines)
                ratePerInterval = self.getRate(lines,startPos)
                self.maxRate = ratePerInterval
                self.minRate = ratePerInterval
                while( startPos <= endPos):
                    self.calResult(ratePerInterval)
                    startPos = startPos + self.perOffset * self.interval / 60
                    ratePerInterval = self.getRate(lines,startPos)
                try:
                    self.averageRate = self.dataSum * 10  / self.timeSum
                except ZeroDivisionError:
                    self.averageRate = 0
                    traceLog("none of the data matched the standard so the time is 0")
        except IOError:
            traceLog("can not open the record file,please check the property of the file")
            exit(1)

     #---------func des---------------
     # local the start position of the data
     # params : lines
     # out:  (startPos,endPos)
     #---------end--------------------
    # -1 => fail to find the position of time
    def localStartEndPos(self,lines):
        startPos = -1
        endPos = -1
        STMatched = self.startTimePatten.finditer(lines)
        ETMatched = self.endTimePatten.finditer(lines)

        for item in STMatched:
            startPos = item.span()[0] +  self.perOffset * self.offset
        for item in ETMatched:
            endPos = item.span()[0] -  self.perOffset * self.offset
        if( startPos == -1 or endPos == -1 ):
            traceLog("fail to find the position of time")
            exit(1)
        return (startPos,endPos)

     #---------func des---------------
     #  get the upload data
     # params : lines,startPos
     # out:  dataUL or dataDL
     #---------end--------------------
    def getRate(self,lines,startPos):
        if( self.direction == "dl" ):
            dataDL = int(lines[startPos + self.DLDataStartPos:startPos + self.DLDataEndPos])
            if( dataDL < self.highestRate and dataDL > self.lowestRate ):
                return dataDL
            else:
                return -1
        elif( self.direction == "ul" ):
            dataUL = int(lines[startPos + self.ULDataStartPos:startPos + self.ULDataEndPos])
            if( dataUL < self.highestRate and dataUL > self.lowestRate ):
                return dataUL
            else:
                return -1
        else:
            traceLog("Error:your option of direction has error,eg: dl ul")
            exit(1)


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


def traceLog(info):
    print info


if __name__ == "__main__":
    (options,args) = makeOptions()
    myDataTracer = DataTracer(options,args)
    myDataTracer.process()
    print '\n{0} {1} ----- {2} {3}\n'.format(options.startTime,args[0],options.endTime,args[1])
    print 'max:{0} min:{1} average: {2}'.format(myDataTracer.maxRate,myDataTracer.minRate,myDataTracer.averageRate)
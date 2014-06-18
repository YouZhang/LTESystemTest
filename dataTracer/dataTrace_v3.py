# coding = utf-8
# script owner & author: You Zhang;

from argparse import ArgumentParser
import re,sys

#wait for extend
def traceLog(info):
    print info

    #---------func des---------------#
    #    generate the option and help
    # params : none
    # out:  options
    #---------end---------------#
def makeOptions():
    #dataStruct : option => help;
    optionsDict = {
        "recordFile" :"set the record file you want to calculate,please input the absolute path\neg: D:\\event_DL_eNB66.txt",
        "highestRate":"set the max threshold to abandon the data\neg: 20000000",
        "lowestRate" :"set the min threshold to abandon the data\type(parser.parse_args()[0])neg: 0",
        "direction"  :"set the upload or download\ndl --> calculate the download data\nul --> calculate the upload data",
        "interval"   :"set the interval time(seconds) to calculate the data\neg: 60",
        "offset"     :"set the data item you want to ignore\neg: 2 --> abandon the first 2 items and the last 2 items"
    }
    parser = ArgumentParser()
    parser.add_argument("-startTime",dest = "startTime",nargs="+",help = "set the start time to calculate in the record File\neg: 2014-05-30 07:34:19")
    parser.add_argument("-endTime",dest = "endTime",nargs="+",help = "set the end time to calculate in the record File\neg: 2014-05-30 07:24:11",)
    for optionName in optionsDict.keys():
        option = "-" + optionName
        parser.add_argument(option,dest = optionName,help = optionsDict[optionName])

    options = parser.parse_args()
    return options

def processOptions(options):
    errorFlag = 0
    if( options.lowestRate == None ):
        traceLog("Error:lowestRate cannot be None,input eg: -lowestRate 0")
        errorFlag = 1
    if( options.highestRate == None ):
        traceLog("Error:highestRate cannot be None,input eg: -highestRate 200000000")
        errorFlag = 1
    if( options.direction == None ):
        traceLog("Error:direction cannot be None,input eg:-direction dl")
        errorFlag = 1
    if( options.startTime == None ):
        traceLog("Error:start time cannot be None,input eg:-startTime 2014-05-30 07:24:11.319")
        errorFlag = 1
    if( options.endTime == None ):
        traceLog("Error:end time cannot be None,input eg:-endTime 2014-05-30 07:24:11.319")
        errorFlag = 1
    if( options.interval == None ):
        traceLog("Error:interval cannot be None,input eg:-interval 60")
        errorFlag = 1
    if( options.recordFile == None ):
        traceLog("Error:recordFile cannot be None,input eg: -recordFile event_DL_eNB66.txt")
        errorFlag = 1
    if( options.offset == None ):
        options.offset = 0
    if( errorFlag ):
        sys.exit(1)

#---------class des---------------
# it is a data trace machine to calculate the maxRate minRate averageRate in the time you set.
# options
# out:  maxRate minRate averageRate
#---------end--------------------
class DataTracer(object):

    def __init__(self,options):
        self.initConfig()
        self.startTime = options.startTime
        self.endTime = options.endTime
        self.recordFile = options.recordFile
        self.direction = options.direction.lower()
        self.interval = int(options.interval)
        self.offset = int(options.offset)
        self.highestRate = int(options.highestRate)
        self.lowestRate = int(options.lowestRate)

        # self.args = args
        self.startTimePatten = None
        self.endTimePatten = None
        self.maxRate = -1
        self.minRate = self.highestRate
        self.dataSum = 0
        self.timeSum = 0
        self.averageRate = 0

    def initConfig(self):
        #this config may changed by different version of netMeter log file
        self.perOffset = 69              # 69 char to locate per line
        self.fileHeaderOffset = 236  # 9 lines per header

    #---------func des---------------
    #    generate the patten of date
    # params : (options,args)
    # out:  startDatePatten,endDatePatten
    #---------end--------------------
    def changeTimeFormat(self):
        STYear = self.startTime[0][0:4]
        STMonth = self.startTime[0][5:7]
        STDay = self.startTime[0][8:10]
        ETYear = self.endTime[0][0:4]
        ETMonth = self.endTime[0][5:7]
        ETDay = self.endTime[0][8:10]
        STFormat = ''.join([STMonth,'/',STDay,'/',STYear,"   ",self.startTime[1][0:5]])
        ETFormat = ''.join([ETMonth,'/',ETDay,'/',ETYear,"   ",self.endTime[1][0:5]])
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
                    traceLog("Error:fail to process because interval you set is not matched with intervalNetMeter:{0}".format(intervalNetMeter))
                    sys.exit(1)

                (startPos,endPos) = self.localStartEndPos(lines)
                ratePerInterval = self.getRate(lines,startPos)
                rateList = [ratePerInterval]
                while( startPos <= endPos):
                    self.calResult(ratePerInterval)
                    startPos = startPos + self.perOffset
                    ratePerInterval = self.getRate(lines,startPos)
                    if( ratePerInterval == -2 ):
                        startPos += self.fileHeaderOffset
                    else:
                        rateList.append(ratePerInterval)
                if( self.minRate == self.highestRate ):
                    self.minRate = -1
                for rate in rateList:
                    traceLog(rate)
                try:
                    self.averageRate = self.dataSum * 60  / self.timeSum
                except ZeroDivisionError:
                    self.averageRate = 0
                    traceLog("Error:none of the data matched the standard so the time is 0")
        except IOError:
            traceLog("Error:can not open the record file,please check the property of the file")
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
        try:
            startPos = lines.index(startTime) + self.perOffset * self.offset
            endPos = lines.index(endTime) - self.perOffset * self.offset
            if( startPos == -1 or endPos == -1 ):
                traceLog("Warning:fail to find the position of time,please check the time you input")
                sys.exit(1)
            elif( startPos > endPos ):
                traceLog("Error: end time must be later than the start time")
                sys.exit(1)
        except:
            traceLog("Warning:failed to locate the time in the NetMeter log file,please check the NetMeter Log")
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
        if( self.direction == "dl" or self.direction == "ul" ):
            try:
                matchedItem = patten.match(lines,startPos)
                dataRate = int(matchedItem.group(1))
                if( dataRate < self.highestRate and dataRate > self.lowestRate ):
                    return dataRate
                else:
                    return -1
            except AttributeError:
                return -2
        else:
            traceLog("Error:your option of direction has error,eg: dl ul")
            sys.exit(1)

     #---------func des---------------
     # calculate the max min sum
     # params : ratePerInterval
     # out:  max min sum
     #---------end--------------------
    def calResult(self,ratePerInterval):
        if( ratePerInterval > 0 ):
            self.dataSum += ratePerInterval
            self.timeSum += self.interval
            if( ratePerInterval > self.maxRate ):
                self.maxRate = ratePerInterval
            if( ratePerInterval < self.minRate ):
                self.minRate = ratePerInterval
        else:
            traceLog("Info:ratePerInterval is not in the range [highestRate:lowestRate]")

     #---------func des---------------
     #  get record file property: interval info & ip info
     # params : lines
     # out:  max min sum
     #---------end--------------------

    def getRecordFileProp(self,lines):
        matchedCase = "Interval:  (\d+)"
        try:
            pos = lines.index("Interval")
            patten = re.compile(matchedCase)
            intervalNetMeter = int(patten.match(lines,pos).group(1))
        except:
            traceLog("Error:failed to locate the NetMeter Interval,the program will set it by default:60")
            intervalNetMeter = 60
        return intervalNetMeter

if __name__ == "__main__":
    options = makeOptions()
    processOptions(options)
    myDataTracer = DataTracer(options)
    myDataTracer.process()
    print '\n{0} {1} ----- {2} {3}\n'.format(options.startTime[0],options.startTime[1],options.endTime[0],options.endTime[1])
    print 'max:{0} min:{1} average: {2}'.format(myDataTracer.maxRate,myDataTracer.minRate,myDataTracer.averageRate)

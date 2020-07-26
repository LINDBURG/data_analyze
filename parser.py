import json
import os
import time
import datetime
import requests

class OutputClass:

    def __init__(self):
        self.mode = 0


    def ReadData(self, inputDir, outputDir):
        os.chdir(inputDir)
        fileNames = os.listdir(inputDir)
        self.server = inputDir[inputDir.rfind('/')+1:]

        no = 0
        jsonOutput = []
        sizFileNames = len(fileNames)
        for fileName in fileNames:
            no += 1
            print('[{0:03d}/{1}]\t'.format(no, sizFileNames) + fileName + ': Start...', end='')

            with open(fileName, 'rt') as fr:
                i = 0
                j = 1
                self.jsonDataTemp = ''
                for line in fr:
                    jsonData = self.ParseJSON(fileName, line)
                    if jsonData != '':
                        if i > 0:
                            jsonOutput.append(self.jsonDataTemp)
                        i += 1
                        self.jsonDataTemp = jsonData
                
                    if i%3000000 == 0:
                        with open(outputDir + fileName + '_' + str(j) + '.json', 'wt') as fw:
                            fw.write(json.dumps(jsonOutput, indent=2))
                            print('Done', end='')
                            jsonOutput = []
                            j += 1

                with open(outputDir + fileName + '.json', 'wt') as fw:
                    fw.write(json.dumps(jsonOutput, indent=2))
                    print('Done')
                    jsonOutput = []


    def GetTimeStamp(self, date):
        if self.mode == 3:
            tokens = date[:-5].split('.')
            date = date[-4:] + tokens[0]
            return time.mktime(datetime.datetime.strptime(date, '%Y %b %d %H:%M:%S').timetuple()) + float('.' + tokens[1])
        else:
            return time.mktime(datetime.datetime.strptime(date, '%d/%b/%Y:%H:%M:%S').timetuple())


    def GetParseParamsData(self, uri):
        params = []
        tokens = uri.split('&')
        for token in tokens:
            var = token.split('=')
            if len(var) > 1:
                params.append({'name': var[0], 'value': var[1]})

        return params, len(params)


    def ParseJSON(self, fname, line):
        tname = fname[:fname.find('_log')]
        if 'access' in fname:
            self.mode = 1
            return self.AccessLogParser(line, tname)
        elif 'request' in fname:
            self.mode = 2
            return self.RequestLogParser(line, tname)
        elif 'error' in fname:
            self.mode = 3
            return self.ErrorLogParser(line, tname)


    def RequestLogParser(self, line, tname):
        try:
            index = 27
            jsonData = {'Server':self.server, 'type':tname, 'rHost':'-', 'SSLVer':'-', 'Cipher':'-', 'TimeStamp':0, 'TimeZ':'-', 'Date':'-', 'Method':'-',
            'URI':'-', 'EXT':'-', 'Count':0, 'Params':[], 'Ver':'-', 'Bytes':0}

            # Date Parsing
            date = line[1:index].split()
            jsonData['TimeStamp'] = self.GetTimeStamp(date[0])
            jsonData['TimeZ'] = date[1]
            jsonData['Date'] = datetime.datetime.fromtimestamp(jsonData['TimeStamp']).isoformat()

            # rHost Parsing
            index += 2
            jsonData['rHost'] = line[index:index+9]

            # TLS Version Parsing
            index += 10
            idxCipher = line[index:].find(' ')
            jsonData['SSLVer'] = line[index:index+idxCipher]

            # Cipher Parsing
            index = index + idxCipher + 1
            idxReq = line[index:].find(' ')
            jsonData['Cipher'] = line[index:index+idxReq]

            # URI Parsing
            index = index + idxReq + 2
            idxBytes = line[index:].rfind('"')
            req = line[index:index+idxBytes].split()
            if len(req) > 2:
                jsonData['Method'] = req[0]
                uri = req[1].find('?')
                if uri == -1:
                    uri = req[1]
                else:
                    jsonData['Params'], jsonData['Count'] = self.GetParseParamsData(req[1][uri+1:])
                    uri = req[1][:uri]
                    
                jsonData['URI'] = uri

                fname = uri[uri.rfind('/')+1:]
                if len(fname) > 0:
                    ext = fname.rfind('.')
                    if ext == -1:
                        jsonData['EXT'] = 'index'
                    else:    
                        ext = fname[ext+1:]
                        if len(ext) > 0:
                            jsonData['EXT'] = ext
                else:
                    jsonData['EXT'] = 'index'
                    
                jsonData['Ver'] = req[2]

            index += 2
            if line[index+idxBytes] == '-':
                jsonData['Bytes'] = 0
            else:
                jsonData['Bytes'] = int(line[index+idxBytes:-1])
            return jsonData

        except:
            print('Error\n# Request Log: ' + line)
            print('jsonData: ' + json.dumps(jsonData))
            exit()


    def ErrorLogParser(self, line, tname):
        try:
            if line[0] == '[':
                index = 4
                jsonData = {'Server':self.server, 'type':tname, 'TimeStamp':0, 'Date':'-', 'Module':'-', 'Level':'-', 'PID':0, 'TID':0, 'rHost':'-', 'rPort':0,
                'MSG':{}, 'Referer':'-'}

                # Date Parsing
                idxLogLevel = line.find(']')
                jsonData['TimeStamp'] = self.GetTimeStamp(line[index:idxLogLevel])
                jsonData['Date'] = datetime.datetime.fromtimestamp(jsonData['TimeStamp']).isoformat()

                # Module:Level Parsing
                index = idxLogLevel + 3
                idxPidTid = line[index:].find(']')

                loglevel = line[index:index+idxPidTid].split(':')
                jsonData['Module'] = loglevel[0]
                jsonData['Level'] = loglevel[1]

                # PID & TID Parsing
                index = index + idxPidTid + 3
                idxMSG = line[index:].find(']') 

                ids = line[index:index+idxMSG].split(':')
                jsonData['PID'] = int(ids[0][4:])
                if len(ids) > 1:
                    jsonData['TID'] = int(ids[1][4:])

                # Client Parsing
                index = index + idxMSG + 2
                if line[index] == '[':
                    idxMSG = line[index:].find(']')
                    client = line[index+1:index+idxMSG].split(':')
                    jsonData['rHost'] = client[0].split(' ')[1]
                    jsonData['rPort'] = int(client[1])
                    index = index + idxMSG + 2
                
                # MSG Parsing
                idxReferer = line.rfind('referer: ')
                msg = line[index:idxReferer].split(':')
                jsonData['MSG'][msg[0]] = []
                count = len(msg)
                for i in range(1, count):
                    jsonData['MSG'][msg[0]].append(msg[i][1:])

                # Referer Parsing index = 8
                if idxReferer == -1:
                    return jsonData

                jsonData['Referer'] = line[idxReferer+8:]
                return jsonData

            else:
                msg = line.split(':')
                if msg[0] not in self.jsonDataTemp['MSG'].keys():
                    self.jsonDataTemp['MSG'][msg[0]] = []
                count = len(msg)
                for i in range(1, count):
                    self.jsonDataTemp['MSG'][msg[0]].append(msg[i][1:])
                return ''

        except:
            print('Error\n#\'s Error Log: ' + line)
            print('jsonData: ' + json.dumps(jsonData))
            exit()

    
    def AccessLogParser(self, line, tname):
        try:
            index = 9
            jsonData = {'Server':self.server, 'type':tname, 'rHost':'-', 'XFF':'-', 'Ident':'-', 'Auth':'-', 'TimeStamp':0, 'TimeZ':'-', 'Date':'-', 'Method':'-',
            'URI':'-', 'EXT':'-', 'Count':0, 'Params':[], 'Ver':'-', 'Status':0, 'Bytes':0, 'Referer':'-', 'UserAgent':'-'}

            # rHost Parsing
            jsonData['rHost'] = line[0:index]
            
            # Slice before Date
            index += 1
            idxDate = line[index:].find('[')
            tokens = line[index:index+idxDate-1]

            # Auth Parsing
            idxAuth = tokens.rfind(' ')
            jsonData['Auth'] = tokens[idxAuth+1:]
            tokens = tokens[:idxAuth]

            # Ident & XFF Parsing
            idxIdent = tokens.rfind(' ')
            if idxIdent == -1:
                jsonData['Ident'] = tokens[0:]
            else:
                jsonData['Ident'] = tokens[idxIdent+1:]
                jsonData['XFF'] = tokens[0:idxIdent]                        

            # Date Parsing
            index = index + idxDate + 1
            idxReq = line[index:].find(']')
            date = line[index:index+idxReq].split()
            jsonData['TimeStamp'] = self.GetTimeStamp(date[0])
            jsonData['TimeZ'] = date[1]
            jsonData['Date'] = datetime.datetime.fromtimestamp(jsonData['TimeStamp']).isoformat()

            # Request Parsing
            idxReq = index + idxReq + 3
            i = idxReq
            while True:
                idxStatus = line[i:].find('" ')
                if line[i+idxStatus+2] >= '0' and line[i+idxStatus+2] <= '9':
                    break
                else:
                    i = i + idxStatus + 2

            req = line[idxReq:i+idxStatus].split()
            if len(req) > 2:
                jsonData['Method'] = req[0]
                uri = req[1].find('?')
                if uri == -1:
                    uri = req[1]
                else:
                    jsonData['Params'], jsonData['Count'] = self.GetParseParamsData(req[1][uri+1:])
                    uri = req[1][:uri]
                    
                jsonData['URI'] = uri

                fname = uri[uri.rfind('/')+1:]
                if len(fname) > 0:
                    ext = fname.rfind('.')
                    if ext == -1:
                        jsonData['EXT'] = 'index'
                    else:    
                        ext = fname[ext+1:]
                        if len(ext) > 0:
                            jsonData['EXT'] = ext
                else:
                    jsonData['EXT'] = 'index'
                    
                jsonData['Ver'] = req[2]

            # Status & Bytes Parsing
            index = i + idxStatus + 2
            idxReferer = line[index:].find('"')
            if idxReferer == -1:
                tokens = line[index:idxReferer].split()
            else:
                tokens = line[index:index+idxReferer].split()
            jsonData['Status'] = int(tokens[0])
            if len(tokens) > 1:
                if tokens[1] == '-':
                    jsonData['Bytes'] = 0
                else:
                    jsonData['Bytes'] = int(tokens[1])

            # Reffer
            if idxReferer == -1:
                return jsonData

            index = index + idxReferer + 1
            if line[index] == '-':
                idxUA = index + 4
                jsonData['Referer'] = line[index]
            else:
                idxUA = line[index:].find('"')
                jsonData['Referer'] = line[index:index+idxUA]
                idxUA = index + idxUA + 2

            # User-Agent
            jsonData['UserAgent'] = line[idxUA:-2]
            return jsonData
            
        except:
            print('Error\n# Access Log: ' + line)
            print('jsonData: ' + json.dumps(jsonData))
            exit()


if __name__ == "__main__":
    dirData = '/Web Log/weblog'
    dirOutput = '/Web Log/parse'

    output = OutputClass()
    output.ReadData(dirData, dirOutput)
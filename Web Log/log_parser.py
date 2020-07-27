import json
import os
import time
import datetime
import requests

class OutputClass:

    def __init__(self, path):
        self.mode = 0
        self.path = path


    def ReadData(self, inputDir, outputDir):
        os.chdir(inputDir)
        fileNames = os.listdir(inputDir)
        self.server = inputDir[inputDir.rfind('/')+1:]

        if not os.path.exists(outputDir):
            os.makedirs(outputDir)
        with open(outputDir + 'error.txt', 'w') as fw:
            fw.write(str(datetime.datetime.now()) +'\n')

        no = 0
        sizFileNames = len(fileNames)
        for fileName in fileNames:
            no += 1
            print('[{0:03d}/{1}]\t'.format(no, sizFileNames) + fileName + ': Start...')

            with open(fileName, 'rt', encoding='UTF8') as fr:
                i = 0
                j = 1
                self.get = []
                self.post = []
                self.put = []
                self.head = []
                self.delete = []
                self.options = []

                try:
                    for line in fr:
                        urlData = self.ParseURL(fileName, line)
                        if urlData != '':
                            #추출 후 바로 리퀘스트 전송
                            self.sendRequest(urlData)
                except:
                    with open(outputDir + 'error.txt', 'a') as fw:
                        fw.write('Request_error: ' + fileName + '\n' + line + '\n')

                    '''if urlData != '':
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
                    jsonOutput = []'''

    def saveRequest(self, url):
        if self.mode == 1:
            self.get.append(url)
        elif self.mode == 2:
            requests.post(url)
        elif self.mode == 3:
            requests.put(url)
        elif self.mode == 4:
            requests.head(url)
        elif self.mode == 5:
            requests.delete(url)
        elif self.mode == 6:
            requests.options(url)

    def sendRequest(self, url):
        if self.mode == 1:
            requests.get(url)
        elif self.mode == 2:
            requests.post(url, data = {})
        elif self.mode == 3:
            requests.put(url)
        elif self.mode == 4:
            requests.head(url)
        elif self.mode == 5:
            requests.delete(url)
        elif self.mode == 6:
            requests.options(url)

    def ParseURL(self, fname, line):
        if 'access' in fname:
            return self.AccessLogParser(line, fname)
    
    def AccessLogParser(self, line, fname):
        try:
            index = line.find('"') + 1

            if index == 0:
                return ''
            elif line[index:index+3] == 'GET':
                self.mode = 1
                index += 4
            elif line[index:index+4] == 'POST':
                self.mode = 2
                index += 5
            elif line[index:index+3] == 'PUT':
                self.mode = 3
                index += 4
            elif line[index:index+4] == 'HEAD':
                self.mode = 4
                index += 5
            elif line[index:index+6] == 'DELETE':
                self.mode = 5
                index += 7
            elif line[index:index+7] == 'OPTIONS':
                self.mode = 6
                index += 8
            else:
                return ''

            url_end = line[index:].find(' ')
            url = line[index:index + url_end]

            if url[0] == '/' or url[0] == '\\':
                return self.path + url
            else:
                return url
                
            
        except:
            with open(outputDir + 'error.txt', 'a') as fw:
                fw.write('Parse_error: ' + fileName + '\n' + line + '\n')


if __name__ == "__main__":
    dirData = os.path.dirname(os.path.abspath(__file__)) + '/weblog'
    dirOutput = os.path.dirname(os.path.abspath(__file__)) + '/parse/'
    #패킷 리플레이를 원하는 주소를 입력(http 포함)
    baseURL = "http://127.0.0.1:5000"

    output = OutputClass(baseURL)
    output.ReadData(dirData, dirOutput)
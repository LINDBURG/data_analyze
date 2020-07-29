import json
import os
import time
import datetime
import requests
import numpy as np

class OutputClass:

    def __init__(self, path):
        self.mode = 0
        self.path = path


    def ReadData(self, inputDir, errorDir):
        os.chdir(inputDir)
        fileNames = os.listdir(inputDir)
        self.server = inputDir[inputDir.rfind('/')+1:]

        if not os.path.exists(errorDir):
            os.makedirs(errorDir)
        
        dt = datetime.datetime.now()
        self.errorFile = errorDir + 'error_sender_' + dt.strftime("%m%d_%H%M") + '.txt'
        f = open(self.errorFile, 'w')
        f.close()

        no = 0
        sizFileNames = len(fileNames)
        sendType = ['get', 'post', 'put', 'head', 'delete', 'options']
        for fileName in fileNames:
            no += 1
            print('[{0:03d}/{1}]\t'.format(no, sizFileNames) + fileName + ': Start...')

            with np.load(inputDir + fileName) as fr:

                try:
                    for i in range(len(sendType)):
                        self.mode = i + 1
                        for urlData in fr[sendType[i]]:
                            urlData = self.path + urlData
                            self.sendRequest(urlData)

                except:
                    with open(self.errorFile, 'a') as fw:
                        fw.write(fileName + '\n' + urlData + '\n')

                    

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


if __name__ == "__main__":
    dirData = os.path.dirname(os.path.abspath(__file__)) + '/parse/'
    errorOut = os.path.dirname(os.path.abspath(__file__)) + '/error/'
    #패킷 리플레이를 원하는 주소를 입력(http 포함)
    baseURL = "http://127.0.0.1:5000"

    output = OutputClass(baseURL)
    output.ReadData(dirData, errorOut)
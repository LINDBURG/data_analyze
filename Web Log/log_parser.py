import json
import os
import time
import datetime
import requests
import numpy as np

class OutputClass:

    def __init__(self):
        self.mode = 0


    def ReadData(self, inputDir, outputDir, errorDir):
        os.chdir(inputDir)
        fileNames = os.listdir(inputDir)
        self.server = inputDir[inputDir.rfind('/')+1:]

        if not os.path.exists(outputDir):
            os.makedirs(outputDir)
        if not os.path.exists(errorDir):
            os.makedirs(errorDir)
        
        dt = datetime.datetime.now()
        self.errorFile = errorDir + 'error_parser_' + dt.strftime("%m%d_%H%M") + '.txt'
        f = open(self.errorFile, 'w')
        f.close()

        no = 0
        sizFileNames = len(fileNames)
        for fileName in fileNames:
            no += 1
            print('[{0:03d}/{1}]\t'.format(no, sizFileNames) + fileName + ': Start...')

            with open(fileName, 'rt', encoding='UTF8') as fr:
                #i = 0
                #j = 1
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
                            #배열에 저장하여 sender에서 사용
                            self.saveRequest(urlData)
                except:
                    with open(self.errorFile, 'a') as fw:
                        fw.write(fileName + '\n' + line + '\n')

            if 'access' in fileName:
                np.savez(outputDir + fileName, get=self.get, post=self.post, put=self.put, head=self.head, delete=self.delete, options=self.options)

    def saveRequest(self, url):
        if self.mode == 1:
            self.get.append(url)
        elif self.mode == 2:
            self.post.append(url)
        elif self.mode == 3:
            self.put.append(url)
        elif self.mode == 4:
            self.head.append(url)
        elif self.mode == 5:
            self.delete.append(url)
        elif self.mode == 6:
            self.options.append(url)

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

            if url[0] == '/':
                return url
            elif url[:4] == 'http':
                #외부 사이트 접속 주소
                #return url
                #외부 사이트 주소 무시
                return ''
            else:
                return ''
                
            
        except:
            with open(self.errorFile, 'a') as fw:
                fw.write(fileName + '\n' + line + '\n')



if __name__ == "__main__":
    dirData = os.path.dirname(os.path.abspath(__file__)) + '/weblog'
    dirOutput = os.path.dirname(os.path.abspath(__file__)) + '/parse/'
    errorOut = os.path.dirname(os.path.abspath(__file__)) + '/error/'

    output = OutputClass()
    output.ReadData(dirData, dirOutput, errorOut)
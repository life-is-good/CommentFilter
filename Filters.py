# -*- coding: utf-8 -*- 
import xlwt
import xlrd
import codecs
from xlutils.copy import copy
import os
path = os.getcwd()

#读取excel处理成要用的格式
def get_excel_data(filepath):
    comment = []
    table_data = xlrd.open_workbook(filepath)
    table = table_data.sheet_by_index(0)
    col_comment = table.col_values(0)
    for c in col_comment:
        comment.append((c,[""]))
    return comment

#读取某些关键字
def get_txt_data(filepath):
    fileHandler = open(filepath)
    data = fileHandler.read()
    if data[:3] == codecs.BOM_UTF8:
        data = data[3:]
    if data[-1] == '\n':
        data = data[:-1]
    _data = data.decode('utf-8').split('\n')
    data = []
    for word in _data:
        if word != u'':
            data.append(word)
    return data

#Filter类(评论)：对评论进行过滤
class Filter:    
    def __init__(self,comment):
        self.comment = comment
    
    #keywords_filter方法：利用关键词进行过滤
    def keywords_filter(self):
        keyword = []
        kw_path = path+"\keywords"
        for kw_file in os.listdir(kw_path):
            keyword.extend(get_txt_data(os.path.join(kw_path, kw_file)))
    
        for i in range(len(self.comment)):
            flag = 0#测试是否存到有关键字的列表里面
            for word in keyword:
                if word in self.comment[i][0]:
                    flag = 1
                    self.comment[i][1].append("1")
                    break
            if flag == 0 and self.comment[i][0]:
                self.comment[i][1].append("0")
        #保存成excel
        self.save_excel_data(2,"afterfilter","filtercommentme")      
        print "keyword filter done"

    #sentiment_filter方法：使用情感词进行过滤
    def sentiment_filter(self):
        sentimentword = []
        sw_path = path+"\sentiment"
        for sw_file in os.listdir(sw_path):
            sentimentword.extend(get_txt_data(os.path.join(sw_path, sw_file)))
     
        for i in range(len(self.comment)):
            flag = 0
            for word in sentimentword:
                if word in self.comment[i][0]:
                    flag = 1
                    self.comment[i][1].append("1")
                    break
            if flag == 0 and self.comment[i][0]:
                self.comment[i][1].append("0")
        #保存成excel
        self.save_excel_data(3,"afterfilter","filtercommentme")
        print "sentiment filter done"        

    #length_filter方法：利用长度进行过滤      
    def length_filter(self):
        for i in range(len(self.comment)):
            if len(self.comment[i][0]) > 2:
                self.comment[i][1].append("1")
            else:
                self.comment[i][1].append("0")
        #保存成excel    
        self.save_excel_data(4,"afterfilter","filtercommentme")        
        print "length filter done"
        
    #save_excel_data方法：保存每一层过滤过数据    
    def save_excel_data(self,nrow,sheetname,filename):
        #判断文件是否存在
        if os.path.exists(path+"\\"+filename+".xls"):#若存在就copy一份，重新写入一些数据
            old_table = xlrd.open_workbook(path+"\\"+filename+".xls")
            new_table = copy(old_table)
            for i in range(len(self.comment)):
                new_table.get_sheet(0).write(i+1,1,self.comment[i][1]) 
                new_table.get_sheet(0).write(i+1,nrow,self.comment[i][1][-1])
        else:#若不存在就新建一个excel表然后写入数据      
            new_table = xlwt.Workbook()
            sheet = new_table.add_sheet(sheetname, cell_overwrite_ok = True)        
             
            sheet.write(0,0,u"评论")
            sheet.write(0,1,u"标签")
            sheet.write(0,2,u"关键词过滤")
            sheet.write(0,3,u"情感词过滤")
            sheet.write(0,4,u"长度过滤")
            for i in range(len(self.comment)):
                sheet.write(i+1,0,self.comment[i][0])
                sheet.write(i+1,1,self.comment[i][1])
                sheet.write(i+1,nrow,self.comment[i][1]) 
        new_table.save(path+"\\"+filename+".xls")
        print "save "+filename+".xls done"

if __name__ == "__main__":
    comment = get_excel_data(path+"\\me.xls")
    
    filter = Filter(comment)
    filter.keywords_filter()
    filter.sentiment_filter()
    filter.length_filter()
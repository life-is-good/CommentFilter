# -*- coding: utf-8 -*-
from pyltp import NamedEntityRecognizer,SementicRoleLabeller,Segmentor,Postagger,Parser
from bs4 import BeautifulSoup
import os
import re
import urllib2
import jieba.posseg
path = os.getcwd()

def get_txt_data(filepath):
    f = open(filepath,'r')
    data = ""
    for line in f.readlines():
        data = data + line
    return data

class Plots:    
    def __init__(self):
        self.plot = "" #要识别的句子
        self.words = [] #句子的分词
        self.postags = [] #分词后词的标签
        self.ner = []  #实体识别之后的标签
        self.entity = [] #每一句选出的实体
        self.result = [] #所有的实体集合
    
    #爬取剧情简介
    def get_plot(self,name):
        print "正在获取基本信息，请等待。。。"
        url = "https://www.baidu.com/s?wd="
        #获取百度搜索的页面
        req = urllib2.Request(url+name)
        req.add_header('Referer','www.baidu.com')
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1')
        html = urllib2.urlopen(req).read()
        bsobj = BeautifulSoup(html,'html.parser')
        href = bsobj.find("a",{"class":"c-gap-right-small op-se-listen-recommend"}).get("href")
        #跳到新百度百科的链接里面
        print "获取信息的链接：",href
        req = urllib2.Request(href)
        html = urllib2.urlopen(req).read()
        bsobj = BeautifulSoup(html,'html.parser')
        ul = bsobj.find("ul",{"class":"dramaSerialList"})
        dl_list = ul.find_all("dl")
        plot = []
        for dl in dl_list:
            for d in dl.find_all("dd"):
                plot.append(d.getText().strip("\n"))
        f = open("keywords/"+u"演员"+".txt","a")
        actorlist = bsobj.find_all("li",{"class":"listItem"})
        cut = u"饰|简介|配音|,|，|/"
        for l in actorlist:
            for i in re.split(cut,l.getText().strip()):
                f.write(i.strip()+"\n")
                                
        stufflist = bsobj.find_all("td",{"class":"list-value"})
        for td in stufflist:
            for t in td.getText().strip().split("、"):
                f.write(t+"\n")
        f.close()  
        print "基本信息获取完毕，开始识别命名实体！"
        for p in plot:
            self.plot = p.encode("utf8")
            #分别对每一句进行实体识别
            self.entity_recognition()
        
    #jieba分词并标注词性，用来处理超长的实体
    def jieba_cut_tags(self,pendentity):
        seg = jieba.posseg.cut(pendentity)
        result = []
        for s in seg:
            if s.flag == "n" or s.flag == "nr" or s.flag == "nh" or s.flag == "ni":
                print s.word
                result.append(s.word)
        return result

    #分词        
    def cut_words(self):
        print "plot:",self.plot
        segmentor = Segmentor()  # 初始化实例
        segmentor.load('ltp_data/cws.model')  # 加载模型
        self.words = segmentor.segment(self.plot)
        print '\t'.join(self.words)
        segmentor.release()  # 释放模型
        
    #词性标注
    def tag_words(self):
        postagger = Postagger()
        postagger.load('ltp_data/pos.model')
        self.postags = postagger.postag(self.words)
        print '\t'.join(self.postags)
        #按照词性标注筛选
        for i in range(len(self.postags)):
            if "ns" in self.postags[i] or "nh" in self.postags[i] or "nt" in self.postags[i]:
                self.entity.append(self.words[i])
        postagger.release()
    
    #命名实体识别
    def name_entity(self):
        recognizer = NamedEntityRecognizer()
        recognizer.load('ltp_data/ner.model')
        self.netags = recognizer.recognize(self.words,self.postags)
        print '\t'.join(self.netags)
        #按照命名实体的标注筛选
        for i in range(len(self.netags)):
            if "Ns" in self.netags[i] or "Nh" in self.postags[i] or "Ni" in self.netags[i]:
                self.entity.append(self.words[i])
        recognizer.release()
    
    #语义角色标注
    def semantic_role_label(self):
        #依存句法分析
        parser = Parser()
        parser.load('ltp_data/parser.model')
        arcs = parser.parse(self.words, self.postags)
        parser.release()
        
        labeller = SementicRoleLabeller()
        labeller.load('ltp_data/srl')
        roles = labeller.label(self.words, self.postags, self.netags, arcs)
        
        Label_AX = []  #存放A0或者A1标签的列表
        for role in roles:
            Label_AX.extend([arg for arg in role.arguments if arg.name == "A0" or arg.name == "A1"])
        for label in Label_AX: 
            #排除一些长度异常的标签为A0或者A1的动作实施者或者动作接受者
            if label.range.end - label.range.start > 0 and label.range.end - label.range.start < 10:
                for i in range(label.range.start,label.range.end+1):
                    #将动作实施者或者动作接受者中的名词，人名，地名拿出来作为实体
                    if self.postags[i] == "n" or self.postags[i] == "ns" or self.postags[i] == "nh" or self.postags[i] == "ni":    
                        self.entity.append(self.words[i])
                    else:
                        pass
            else:
                pass     
        labeller.release()
        
    #筛选需要的实体
    def filter_entity(self):
        #长度过长的实体再进行切割筛选
        temporaryentity = [] #临时列表
        for en in self.entity:
            if len(en) >= 12:
                temporaryentity.extend(self.jieba_cut_tags(en))
            else:
                temporaryentity.append(en)
        self.entity = temporaryentity
        
        print "=========ENTITY============"
        for en in self.entity:
            #只选择长度符合的实体
            if len(en) >= 6:#输出长度符合的，以后要删除
                print "good:",en
            if len(en.strip().strip("。.，,！!？?")) < 6:
                print "bad:",en
                self.entity.remove(en)
        #将本次的结果保存到最终的结果中
        self.result.extend(self.entity)
        #每句识别完之后就清空实体列表，以便下一次使用
        self.entity = []

    #入口
    def entity_recognition(self):
        self.cut_words()
        self.tag_words()
        self.name_entity()
        self.semantic_role_label()
        self.filter_entity()
    
    #保存实体
    def save_entity(self):
        #对最终实体列表进行去重
        self.result = set(self.result)
        #识别出来的实体保存到文件
        f = open("keywords/NameEntityMe.txt","w")
        print "开始保存"
        for en in self.result:
            if len(en.strip().strip("。.，,！!？?")) >= 6:
                f.write(en.strip("。.，,！!？?")+"\n")
        f.close()
        print "保存完毕"

if __name__ == "__main__":
    name = u"放弃我抓紧我"
    p = Plots()
    p.get_plot(name)            
    p.save_entity()

import xml.sax as sx
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords 
from nltk.stem import PorterStemmer
import re
import os
import sys
import time
import gc
xml_filename = 'enwiki-latest-pages-articles26.xml-p42567204p42663461'
xml_filename1 = 'test_data.xml'
index_filename = 'inverted_index.txt'
id_title_filename = 'id_title_mapping.txt'
regex_category = r"\[\[category:(.*?)\]\]"
regex_link = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
stop_words = set(stopwords.words('english')) 
stem_dictionary = {}
arguments = sys.argv[1:]

# alpha = 'a'
# cap_alpha = 'A'
# test_list = []
# for i in range(0,26):
#     test_list.append(alpha)
#     test_list.append(cap_alpha)
#     alpha = chr(ord(alpha) + 1)
#     cap_alpha = chr(ord(cap_alpha) + 1)
    

class WikiXmlHandler(sx.handler.ContentHandler):
    def __init__(self):
        sx.handler.ContentHandler.__init__(self)
        self._buffer = None
        self._values = {}
        self._current_tag = None
        self._pages = []
        self._id_title_map = {}
        self._title_id_map = {}
        self._title_to_terms = {}
        self._id_buffer = ''
        self._id_flag = False
        self._field_query = {}
        self._preprocessed_text = {}
        self._inverted_index = {}
        self._whole_text = []
        self._title_inverted_index = {}


    def characters(self, content):
        if self._current_tag:
            self._buffer.append(content)

    def startElement(self, name, attrs):
        if name == 'title' :
            self._current_tag = name
            self._buffer = []
            self._id_flag = True #to add only id corresponding to the title and not other id's which are redundant

        elif name == 'id' or name == 'text':
            self._current_tag = name
            self._buffer = []

    def endElement(self, name):
        # if name == self._current_tag and name != 'id':
        
        if name == 'title':
            self._values[name] = ' '.join(self._buffer)

        elif name == 'text':
             text_content = ' '.join(self._buffer)
             self._values[name] = text_content.casefold()

        elif name == 'id' and self._id_flag == True:
            self._values[name] = ' '.join(self._buffer)
            self._id_title_map[self._values['id']] = self._values['title']
            self._values['title'] = self._values['title'].casefold() 
            self._title_id_map[self._values['title']] = self._values['id']

            self._id_flag = False

        elif name == 'page':
            self._pages.append((self._values['title'], self._values['text']))

    def tokenize(self, tmp_str, document_id, key_name):
        words = []
        tmp_str = re.sub(r'[^\x00-\x7F]+',' ', tmp_str)
        # nltk.download('punkt')
        # tokens = word_tokenize(tmp_str)
        tokens = tmp_str.split()

        # remove all tokens that are not alphanumeric
        ps = PorterStemmer()

        for word in tokens:
            if word.isalnum() and word not in stop_words:
                if word in stem_dictionary:
                    temp_word = stem_dictionary[word] 
                else:
                    temp_word = ps.stem(word) 
                    stem_dictionary[word] = temp_word
                
                if len(temp_word) < 3:
                    continue
                if temp_word not in self._inverted_index:
                    self._inverted_index[temp_word] = {}
                if document_id not in self._inverted_index[temp_word]:
                    self._inverted_index[temp_word][document_id] = {}
                if key_name not in self._inverted_index[temp_word][document_id]: 
                    self._inverted_index[temp_word][document_id][key_name] = 0
                self._inverted_index[temp_word][document_id][key_name] += 1
                if key_name == 't':
                    if temp_word not in self._title_inverted_index: 
                        self._title_inverted_index[temp_word] = {}
                    if document_id not in self._title_inverted_index[temp_word]:
                        self._title_inverted_index[temp_word][document_id] = 0
                    self._title_inverted_index[temp_word][document_id] += 1
                words.append(temp_word)
        # make is word.isalnum(), if number is necessary to be handled
        return words

    def data_preprocessing(self):
         # before tokenizing the text extract the category
        
        for tup in self._pages:
            
            title = tup[0]
            text = tup[1]
            # text = text.encode(encoding = 'UTF-8')
            
            document_id = self._title_id_map[title]
            # print(" ACTUAL TEXT : ",text)
            # print("===========================================================================")

            #extracting fields------------------------------------------

            #Remove all http links
            links = re.findall(regex_link, tup[1])     
            for link in links:
                text = text.replace(link,"")

            # print(" text after removing links : ",text)
            # print("-----------------------------------------------------------------")
            
            #Extract and replace category
            matches = re.finditer(regex_category, text, re.MULTILINE | re.DOTALL)
            category_name = ''
            tok_category = []
            for matchNum, match in enumerate(matches):
                for groupNum in range(0, len(match.groups())):
                    category = match.group(1)
                    text = text.replace(match.group(0),'')
                    if '|' in category:
                        category_name = category.split('|')
                        # considering the data after pipe in category as the bobdy text data only :
                        temp_txt = category_name[1:]
                        # print(" gadhi wala temp text : ",temp_txt)
                        for j in temp_txt:
                            text += " "+ j

                        category_name = category_name[0]
                        
                    else:
                        category_name = category
                    cat = handler.tokenize(category_name, document_id, 'c')    # 'c' is for category
                    tok_category.append(cat)

            # print(" text after removing category : ",text)
            # print("-----------------------------------------------------------------")
            # print(" tokenized category : ",tok_category)
            # print("=================================================================================")            
            

            #tokenize Title
            tok_title = self.tokenize(title, document_id, 't') # 't' is for title

            # print(" tokenized title : ",tok_title)
            # print("=================================================================================")    

            #Remove #Redirect
            text = text.replace("#redirect","")

            # print(" text after removing #redirect : ",text)
            # print("=================================================================================")    

            # Extract and remove infobox
            text, infobox_list =  handler.extract_infobox(text)
            parameters = infobox_list.split("\n")
            parameters = parameters[1:]
            tok_infobox = []
            for value in parameters:
                temp = value.split("=")
                if(len(temp)>1):
                    tok_infobox += self.tokenize(temp[1], document_id,'i') # 'i' is for infobox

            
            # print(" text after removing infobox : ",text)
            # print("-----------------------------------------------------------------")
            # print(" tokenized infobox : ",tok_infobox)
            # print("=================================================================================")    


            #Extract and remove References
            ref_list =  re.findall(regEx['ref1'], text)
            tok_ref = []
            for ref in ref_list:
                text, ext_ref = handler.extract_references(ref, text)
                tok_ref += self.tokenize(ext_ref, document_id,'r') # 'e' is for external reference
            
            # print(" text after removing references : ",text)
            # print("-----------------------------------------------------------------")
            # print(" tokenized references : ",tok_ref)
            # print("=================================================================================")    

            #Extract and remove External Links
            external_link_text = re.findall(regEx['ext1'], tup[1])
            tok_extlink = []
            for ext in external_link_text:
                ext_link = handler.extract_external_link(ext)
                text = text.replace("external links","")
                text = text.replace(ext,"")
                tok_extlink += self.tokenize(ext_link, document_id,'l') # 'l' is for external links

            
            # print(" text after removing ext links : ",text)
            # print("-----------------------------------------------------------------")
            # print(" tokenized category : ",tok_extlink)
            # print("=================================================================================")    


            tok_bodytxt = self.tokenize(text, document_id,'b') # 'b' is for body text


            # print(" tokenized bodytext : ",tok_bodytxt)
            # print("=================================================================================")    

    def extract_infobox(self,txt):
        count = 0
        temp_string = ""
        i = 0
        flag = 0
        while i<len(txt):
            if( txt[i] == '{' and i+1 < len(txt) ):
                if(i+9<len(txt) and txt[i+2:i+9].casefold() == "infobox"):
                    i += 9
                    count += 2
                    flag = 1
                elif flag == 1:
                    count += 1
                    # 
            if(txt[i] == '}' and flag==1):
                count -= 1
            if(count > 0):
                temp_string += txt[i]
            else:
                flag = 0
            i +=1 
        # print(" temp_string : ",temp_string)
        txt = txt.replace(temp_string,"")
        txt = txt.replace("{{infobox}","")
        # print(" replace ",txt)
        return txt, temp_string

    def extract_references(self,txt, whole_text):
        count = 0
        temp_string = ""
        i = 0
        while i<len(txt):
            if( txt[i] == '{' and i+1 <= len(txt)-1 ):
                count += 1
            if(txt[i] == '}' and i+1 <= len(txt)-1 ):
                count -= 1
                if count==0 and i+1<=len(txt)-1 and txt[i+1] == "\n" and i+2 < len(txt) and txt[i+2]!="{":
                    break
            if count > 0:
                temp_string += txt[i]
            i +=1 
        whole_text = whole_text.replace("==references==","")
        whole_text = whole_text.replace(temp_string+"}","")
        return whole_text,temp_string

    def extract_external_link(self,txt):
        count = 0
        temp_string = ""
        i = 0
        while i<len(txt):
            if( txt[i] == '{' and i+1 < len(txt)-1 ):
                count += 1
            if(txt[i] == '}' and i+1 < len(txt)-1 ):
                count -= 1
            if count > 0:
                temp_string += txt[i]
            i +=1 
        # print(" temp ",temp_string)
        return temp_string

    
    
        # def fetch_docs():
    #     pass



regEx = {}
# regEx['ibox'] = re.compile(r"\{\{Infobox.*", flags=re.IGNORECASE | re.DOTALL)
regEx['links'] = re.compile(r"(www|http:|https:)+[^\s]+[\w]", flags=re.IGNORECASE | re.DOTALL)
regEx['ref1'] = re.compile(r"(== ?References.*)[ \n]\{\{", flags=re.IGNORECASE | re.DOTALL)
regEx['ext1'] = re.compile(r"(== ?External links.*)\n", flags=re.IGNORECASE | re.DOTALL)
regEx['body_pat'] = re.compile(r"== ?References.*", flags=re.DOTALL)

parser = sx.make_parser()
parser.setFeature(sx.handler.feature_namespaces, 0)
handler = WikiXmlHandler()
parser.setContentHandler(handler)
# current_directory_path = os.getcwd()
data_file_path = arguments[0]
parser.parse(data_file_path)

if arguments[1][-1] != "/":
    folder_path = arguments[1] + "/"
else:
    folder_path = arguments[1]
index_file_path = folder_path + index_filename
idtitle_file_path = folder_path +id_title_filename

# Creating the Index and storing to the file
gc.disable()
start1 = time.time()
handler.data_preprocessing()
# print(handler._inverted_index)
f = open(index_file_path,"w")
f2 = open(idtitle_file_path,"w")
for key,val in sorted(handler._inverted_index.items()):
    # s =str(key.encode('utf-8'))+"="
    key += "-"
    for k,v in sorted(val.items()):
        key += str(k) + ":"
        for k1,v1 in v.items():
            key = key + str(k1) + str(v1) + "#"
        key = key[:-1]+","
    key = key[:-1]+"\n"
    f.write(key)
for key,value in handler._id_title_map.items():
    f2.write(key+"->"+value+"\n")

f.close()
f2.close()
end1 = time.time()
gc.enable()

print(" PREPROCESSING + INDEX CREATION TIME : ",end1 - start1)

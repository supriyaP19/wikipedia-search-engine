import xml.sax as sx
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords 
from nltk.stem import PorterStemmer
import re
import time

regex = r"\[\[category:(.*?)\]\]"
stop_words = set(stopwords.words('english')) 

class WikiXmlHandler(sx.handler.ContentHandler):
    def _init_(self):
        sx.handler.ContentHandler._init_(self)
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


    def characters(self, content):
        if self._current_tag:
            self._buffer.append(content.casefold())

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
            self._values[name] = ' '.join(self._buffer)



           

        elif name == 'id' and self._id_flag == True:
            self._values[name] = ' '.join(self._buffer)
            self._id_title_map[self._values['id']] = self._values['title']
            self._title_id_map[self._values['title']] = self._values['id']
            self._id_flag = False

        elif name == 'page':
            self._pages.append((self._values['title'], self._values['text']))
    

    def tokenize(self, tmp_str):
        words = []
        # nltk.download('punkt')
        tokens = word_tokenize(tmp_str)
        # remove all tokens that are not alphanumeric
        ps = PorterStemmer()
        words = [ps.stem(word) for word in tokens if word not in stop_words and word.isalnum()]
        # print(tmp_str," : ",words)
        return words

    def data_preprocessing(self):
         # before tokenizing the text extract the category
        
        for tup in self._pages:
            title = tup[0]
            text = tup[1]
            print(text)
            matches = re.finditer(regex, text, re.MULTILINE | re.DOTALL)
            category_name = ''
            for matchNum, match in enumerate(matches):
                for groupNum in range(0, len(match.groups())):
                    category = match.group(1)
                    if '|' in category:
                        category_name = category.split('|')
                        category_name = category_name[0]
                    else:
                        category_name = category
            tok_category = self.tokenize(category_name)
            text=text.replace(regex,'')
            print(text)

            tok_title = self.tokenize(title)

            data = text
            data = data.replace("#redirect","")
            tok_text = self.tokenize(data)
            # print(" tokenized text : ",tok_text)
            temp_list = [tok_title,tok_category,tok_text]
            id = self._title_id_map[title]
            self._preprocessed_text[id] = tuple(temp_list)



    def resolve_redirects(self, map_of_title_text):
        for tup in  map_of_title_text:
            if tup[1][0] == '#':
                pass

    def index_creation(self):
        for key in self._preprocessed_text:
            tup = self._preprocessed_text[key]
            index = 0
            temp_dict = {}
            for item_list in tup:
                for item in item_list:
                    if item not in temp_dict:
                        temp_dict[item] = 1
                    else:
                        temp_dict[item] += 1
                for key2 in temp_dict:
                    if key2 not in self._inverted_index:
                        self._inverted_index[key2] = {}
                    self._inverted_index[key2][key] = {}
                    if index == 0:
                        self._inverted_index[key2][key]['t'] = temp_dict[key2]
                    elif index == 1:
                        self._inverted_index[key2][key]['c'] = temp_dict[key2]
                    elif index == 2:
                        self._inverted_index[key2][key]['b'] = temp_dict[key2]
            
            index += 1



    
    def fieldQuery(self):

        for tup in self._pages:
            
            # print(" inside field query \n")
            title = tup[0]
            text = tup[1]
            text_hash = hash(text)

            # storing title in field query 
            if 'Title' not in self._field_query:
                self._field_query['Title'] = {}
            if title not in self._field_query['Title']:
                self._field_query['Title'][title] = []
            self._field_query['Title'][title].append(self._title_id_map[title])

            # storing the TEXT HASH in the field query
            if 'BodyText' not in self._field_query:
                self._field_query['BodyText'] = {}
            if text_hash not in self._field_query['BodyText']:
                self._field_query['BodyText'][text_hash] = []
            self._field_query['BodyText'][text_hash].append(self._title_id_map[title])

            # storing the page id which this catagory belongs
            print(" text : ",text)
            matches = re.finditer(regex, text, re.MULTILINE | re.DOTALL)
            for matchNum, match in enumerate(matches):
                for groupNum in range(0, len(match.groups())):
                    category = match.group(1)
                    print("cat : ",category)
                    if '|' in category:
                        category_name = category.split('|')
                        category_name = category_name[0]
                    else:
                        category_name = category
                    print(category_name)
                    if 'Category' not in self._field_query:
                        self._field_query['Category'] = {}
                    if category_name not in self._field_query['Category']:
                        self._field_query['Category'][category_name] = [] 
                    self._field_query['Category'][category_name].append(self._title_id_map[title]) 

                


    # def fetch_docs():
    #     pass


parser = sx.make_parser()
parser.setFeature(sx.handler.feature_namespaces, 0)
handler = WikiXmlHandler()
parser.setContentHandler(handler)
# parser.parse('enwiki-latest-pages-articles26.xml-p42567204p42663461')
parser.parse('test_data.xml')
# handler.fieldQuery()
# print(handler._field_query)

start1 = time.time()
handler.data_preprocessing()
end1 = time.time()
print(" PREPROCESSING TIME : ",end1 - start1)


# print(" PROCESSED STIRNG : ",handler._preprocessed_text)
# print("PAGE : ",handler._pages)
# print("VALUES : ",handler._values)
# print("MAP : ",handler._id_title_map)
# print("MAP 2: ",handler._title_id_map)
# print("MAP 3: ",handler._title_to_terms)
# print("MAP 4: ",handler._field_query)

start = time.time()
handler.index_creation()
end = time.time()
print(end-start)
# print(" INVERTED INDEX  : ",handler._inverted_index)


# parser.parse(root_path + filename)
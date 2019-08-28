
# coding: utf-8

# In[1104]:


from lxml import etree as ET
from Stemmer import Stemmer as PyStemmer
import string
import re
import time
import sys


# In[1105]:


from collections import defaultdict


# In[1106]:


ps = PyStemmer('porter')


# In[1107]:


stops={}

with open('stopwords.txt','r') as file:
    words = file.read().split('\n')
    for i in words:
        w = ps.stemWord(i) 
        if w:stops[w]=1


# In[1108]:


def cleanTag(element):
    start_tag= element.rfind('}')+1
    return element[start_tag:]



# In[1110]:


def camel_case_split(identifier):
    matches = re.finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', identifier)
    return [m.group(0) for m in matches]


# In[1111]:


def parseXML(wikixml, regEx):
    # create element tree object
    tree = ET.iterparse(wikixml, events=("start", "end"))
    
    globalIndex = defaultdict(list)
    pages = []
    page_tags = {}
    for action, element in tree:
       
        element.tag = cleanTag(element.tag)
        
        if element.tag == "id":
            element.tag = cleanTag(element.getparent().tag) + '-' + element.tag
        #print(action + "," + element.tag)
        page_tags[element.tag] = element.text
        
        if element.tag == "page" and action == "end":
            globalIndex = get_fields(page_tags, globalIndex, regEx)
            page_tags = {}
            
    return globalIndex
    


# In[1112]:


def tokenize(text, localIndex, field_dict):
    global stops, ps
    # split into words
    tokens = re.split('[^A-Za-z]', text)
    # split Camelcase
    temp_token = []
    for w in tokens:
        temp_token += camel_case_split(w)
        
    for w in temp_token:
        # convert to lower case
        w = w.lower()
        # remove remaining tokens that are not alphabetic and filter out stop words
        if w in stops or len(w) < 2:
            continue
        # stemming of words
        stemmed_word = ps.stemWord(w)
        #insert in the index dictionary
        field_dict = insert_in_dict(stemmed_word, field_dict)
        localIndex[stemmed_word] = True
    return localIndex, field_dict


# In[1113]:


def tokenizeTitle(text, title_dict, localIndex):
    localIndex, title_dict = tokenize(text, localIndex, title_dict)
    return title_dict, localIndex


# In[1114]:


def insert_in_dict(final_word, dictionary):
    dictionary[final_word] += 1
    return dictionary


# In[1115]:


def extract_infobox(page_text, info_dict, localIndex, regEx):
    infobox_text = re.findall(regEx['ibox1'], page_text)
    for info in infobox_text:
        localIndex, info_dict = tokenize(info, localIndex, info_dict)
    page_text = re.sub(regEx['ibox2'], "", page_text)
    return page_text, info_dict, localIndex


# In[1116]:


def extract_references(page_text, ref_dict, localIndex, regEx):
    references_text = re.findall(regEx['ref1'], page_text)
    for ref in references_text:
        localIndex, ref_dict = tokenize(ref, localIndex, ref_dict)
#     page_text = re.sub(r"== ?References ?==.*\n(== ?External)", "== External", 
#                        page_text, flags=re.IGNORECASE | re.DOTALL)
    return ref_dict, localIndex


# In[1117]:


def extract_links(page_text, external_dict, localIndex, regEx):
    external_link_text = re.findall(regEx['ext1'], page_text)
    for link in external_link_text:
        localIndex, external_dict = tokenize(link, localIndex, external_dict)
#     page_text = re.sub(r"== ?External links ?==.*?\n\n(\[\[)", "[[", 
#                        page_text, flags=re.IGNORECASE | re.DOTALL)
    return external_dict, localIndex


# In[1118]:


def extract_category(page_text, category_dict, localIndex, regEx):
    category_text = re.findall(regEx['cat1'], page_text)
    for cat in category_text:
        localIndex, category_dict = tokenize(cat, localIndex, category_dict)
    #page_text = re.sub(r"\[\[Category.*?\]\]", "", page_text)
    return category_dict, localIndex


# In[1119]:


def extract_body(page_text, regEx):
    #page_text = re.sub(regEx[ibox2], "", page_text, flags=re.DOTALL)
    page_text = re.sub(regEx['body_pat'],"", page_text)
    #page_text = re.sub(regEx['css'], "", page_text)
    return page_text


# In[1120]:


def tokenizeText(page_text, info_dict, category_dict, external_dict, ref_dict, body_dict, localIndex, regEx):
    # extract categories from inside the text
    # Classes are body, infobox, categories, external-links, references
    
    page_text, info_dict, localIndex = extract_infobox(page_text, info_dict, localIndex, regEx)
        
    ref_dict, localIndex = extract_references(page_text, ref_dict, localIndex, regEx)
    
    external_dict, localIndex = extract_links(page_text, external_dict, localIndex, regEx)
    
    category_dict, localIndex = extract_category(page_text, category_dict, localIndex, regEx)
    # extract body, everything else besides the above defined classes consists of body
    body = extract_body(page_text, regEx)

    localIndex, body_dict = tokenize(body, localIndex, body_dict)
    
    return info_dict, category_dict, external_dict, ref_dict, body_dict, localIndex


# In[1121]:


def insert_global_dict(page_id, title_dict, info_dict, category_dict, external_dict, ref_dict, body_dict, localIndex, globalIndex):
    #d$ - t$ i$ c$ e$ r$ b$
    for key in localIndex:
        if len(key) > 2 :
            if key in globalIndex:
                globalIndex[key].append([page_id, title_dict[key], info_dict[key], category_dict[key], external_dict[key], 
                                     ref_dict[key], body_dict[key]])
            else:
                globalIndex[key] = [[page_id, title_dict[key], info_dict[key], category_dict[key], external_dict[key], 
                                     ref_dict[key], body_dict[key]]]
    return globalIndex


# In[1122]:


def get_fields(page, globalIndex, regEx):
    localIndex = defaultdict(bool)
    title_dict = defaultdict(int)
    info_dict = defaultdict(int)
    category_dict = defaultdict(int)
    external_dict = defaultdict(int)
    ref_dict = defaultdict(int)
    body_dict = defaultdict(int)
    
    title_dict, localIndex = tokenizeTitle(page['title'], title_dict, localIndex)
    
    info_dict, category_dict, external_dict, ref_dict, body_dict, localIndex = tokenizeText(page['text'], info_dict, category_dict, external_dict, ref_dict, body_dict, localIndex, regEx)
    
    globalIndex = insert_global_dict(page['page-id'], title_dict, info_dict, category_dict, external_dict, ref_dict, body_dict, localIndex, globalIndex)
    
    return globalIndex


# In[1123]:


def writeFieldCount(flist, fp):
    fp.write("d" + str(flist[0]))
    if flist[1]:
        fp.write("t" + str(flist[1]))
    if flist[2]:
        fp.write("i" + str(flist[2]))
    if flist[3]:
        fp.write("c" + str(flist[3]))
    if flist[4]:
        fp.write("e" + str(flist[4]))
    if flist[5]:
        fp.write("r" + str(flist[5]))
    if flist[6]:
        fp.write("b" + str(flist[6]))
    return fp 


# In[1124]:


def writeFile(globalIndex, out):
    with open(out, "w") as fp:
        for w in sorted(globalIndex):
            fp.write(str(w) + ":")
            fieldCount = globalIndex[w]
            for i in fieldCount:
                fp = writeFieldCount(i,fp)
                fp.write("|")
            fp.write("\n")
                


# In[1125]:


if __name__ == "__main__":
    s=time.time()
    regEx = {}
    regEx['ibox1'] = re.compile(r"\{\{(infobox .*)?\n\}\}$", flags=re.IGNORECASE | re.DOTALL)
    regEx['ibox2'] = re.compile(r"\{\{Infobox .*?\n\}\}", flags=re.DOTALL)

    regEx['ref1'] = re.compile(r"(== ?References.*)\n== ?External", flags=re.IGNORECASE | re.DOTALL)

    regEx['ext1'] = re.compile(r"== ?(External links ?==.*)\n\n\[\[", flags=re.IGNORECASE | re.DOTALL)

    regEx['cat1'] = re.compile(r"\[\[(Category:.*)?\]\]", flags=re.IGNORECASE)

    regEx['body_pat'] = re.compile(r"== ?References.*", flags=re.DOTALL)
    #regEx['css'] = re.compile(r"\[\[[Ff]?ile(.?)\]\]|{\|(.?)\|}|{{[Vv]?[Cc]ite:(.?)}}|\<(.?)\>|={3,}", flags=re.DOTALL)
    input_file = sys.argv[1]
    globalIndex = parseXML(input_file, regEx)
    output_file = sys.argv[2]
    writeFile(globalIndex, output_file)
    print(time.time()-s)
    print(len(globalIndex))
    


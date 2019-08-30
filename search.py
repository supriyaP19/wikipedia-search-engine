import xml.sax as sx
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords 
from nltk.stem import PorterStemmer
import re
import sys
import time
import gc
import os
# import create_index as CI
index_filename = "inverted_index.txt"
id_title_filename = "id_title_mapping.txt"
current_directory_path = os.getcwd()
stop_words = set(stopwords.words('english')) 
arguments = sys.argv[1:]

id_title_map = {}
inverted_index = {}
path_to_index_folder = arguments[0]
path_to_input_query_file = arguments[1]
path_to_output_file = arguments[2]


# Fetching the id-title dictionary
try : 
    
    f = open(path_to_index_folder+"/"+id_title_filename,"r")
    print(" making id title map ")
    line = f.readline()
    while line:
        temp = line.split("->")
        doc_id = temp[0]
        title = temp[1]
        id_title_map[doc_id] = title
        line = f.readline()
    f.close()
except:
    print("Can't find the Title and Document ID Mapping File. (id_title_mapping.txt).")
    print("Re - run the program when the file is in the same folder.")
    sys.exit(1)

try:
    print(" creating index----")
    f = open(path_to_index_folder+"/"+index_filename,"r")
    line = f.readline()
    while line:
        temp = line.split("-")
        term = temp[0]
        # print(term)
        posting_list_string = temp[1]
        inverted_index[term] = posting_list_string
        line = f.readline()
except:
    print("Can't find the index file in 'index' Folder.")
    print("Re - run the program when the file is in the same folder.")
    sys.exit(1)


def tokenize(tmp_str):
    words = []
    print(" inside tokenize")
    # nltk.download('punkt')
    # tokens = word_tokenize(tmp_str)
    # print(" str to tokenize : ",tmp_str)
    tmp_str = re.sub(r'[^\x00-\x7F]+',' ', tmp_str)
    tokens = tmp_str.split()
    print(" tokens : ",tokens)
    # remove all tokens that are not alphanumeric
    ps = PorterStemmer()

    for word in tokens:
        print(" 1 ")
        if word not in stop_words and word.isalpha():
            print(" 2 ")
            temp_word = ps.stem(word)
            if len(temp_word) < 3:
                continue
            words.append(temp_word)
    # make is word.isalnum(), if number is necessary to be handled
    print("words : ",words)
    return words

def print_result(set_intersection_result):
    print(" Result size ",len(set_intersection_result))
    print("=======================================================")
    for doc_id in set_intersection_result:
        print(id_title_map[doc_id])
    print("=======================================================")

def queryField(words_in_query):
    print(" inside field query processing")
    categories = words_in_query.split()
    print(" query : ",categories)
    temp_cat_docid = {}

    #       Creating term-cat dictionary as follows :
    #  for eg the query is -  t:gandhi b:arjun i:gandhi c:gandhi r:gandhi
    #  we need to create -> { gandhi : [t,i,c,r], arjun : [b] }
    temp_term_cat = {}
    for x in categories:
        category_term = x.split(":") 
        print(" catagory term : ",category_term)
        category = category_term[0][0] # took the first letter of the full name of the category following the rule already used to create the index
        print(" category short form : ", category)
        term = category_term[1]
        print(" term came to be : ",term)
        tokenized_term = tokenize(term)
        print(" after tokenization : ",tokenized_term[0])
        print("3")
        if tokenized_term[0] in inverted_index:
            print("4")
            if tokenized_term[0] not in temp_term_cat:
                print("5")
                temp_term_cat[tokenized_term[0]] = []
            temp_term_cat[tokenized_term[0]].append(category)
            print(temp_term_cat)

    #       Creating dic of sets
    #   for the above query and from the created dictionary temp_term_cat -> t:gandhi b:arjun i:gandhi c:gandhi r:gandhi
    #   we need to create -> {t:{d1:4}, i:{d1:5,d2:4}, c:{d2:3}, r:{d2:3}, b:{d2:7}}, if the index was { gandhi-d1:t4#i5, d2:c3#r3    arjun-d2:b7#c5}
    
    result_dic = {}
    for term in temp_term_cat:
        posting_list_string = inverted_index[term]
        doc_catfreq_list = posting_list_string.split(",")
        for catfreq in doc_catfreq_list:
            temp = catfreq.split(":")
            doc_id = temp[0]
            print(" doc_id : ",doc_id)
            cat_list = temp[1]
            if '\n' in cat_list:
                cat_list = cat_list[:-1]
            cats = cat_list.split("#")
            print(" cats : ",cats)
            for cat in cats:
                cat_name = cat[0]
              
                freq = int(cat[1:])
                if cat_name in temp_term_cat[term]:
                    if cat_name not in temp_cat_docid: 
                        temp_cat_docid[cat_name] = {}
                    temp_cat_docid[cat_name][doc_id] = freq
                    if doc_id not in result_dic:
                        result_dic[doc_id] = 0
                    result_dic[doc_id] += freq

    
    # print(result_dic)
    result_dic = sorted(result_dic.items(), reverse=True, key = lambda x : x[1]) # Sort the docs in the order of their frequency
    print(result_dic)
    print("--------------------- Top 10 results")
    i = 0
    
    for key in result_dic:
        if i >= 10:
            break
        print(id_title_map[key[0]])
        f2.write(id_title_map[key[0]])
        i += 1
    f2.write("\n")

def queryNormal(words_in_query):
    # print(" inside normal query processing")
    tokenized_words = tokenize(words_in_query)
    # print(" tokenized query : ",tokenized_words)
    word_doc_freq = {}
    i = 0
    dic_of_docid_freq = {}
    for word in tokenized_words:
        word_doc_freq[word] = {}
        if word in inverted_index:
            # Parse the posting list string
            id_freq_mapping = inverted_index[word].split(",")
            for items in id_freq_mapping:
                # weighted_freq = 0
                temp = items.split(":")
                doc_id = temp[0]
                fields = temp[1]
                if '\n' in fields:
                    fields = fields[:-1]
                field = fields.split("#")
                freq = 0
                for f in field:
                    freq += int(f[1:])
                dic_of_docid_freq[doc_id] = freq
    print(dic_of_docid_freq)
    dic_of_docid_freq = sorted(dic_of_docid_freq.items(), reverse=True, key = lambda x : x[1]) # Sort the docs in the order of their frequency
    print(dic_of_docid_freq)
    print("--------------------- Top 10 results")
    i = 0
    for key in dic_of_docid_freq:
        if i >= 10:
            break
        print(id_title_map[key[0]])
        f2.write(id_title_map[key[0]])
        i += 1
    f2.write("\n")

        

    # Printing Titles in result
    # print_result(final_set_of_docid)
                

print(" query file to open :",path_to_input_query_file)
f = open(path_to_input_query_file)
f2 = open(path_to_output_file,"w+")
line = f.readline()
while line:
    print(" inside while line ---")
    print("LINE : ",line)
    query = line
    start = time.time()
    queryType = ""
    if ":" in query:
        queryType = "Field"
    else:
        queryType = "Normal"

    if queryType == "Normal":
        queryNormal(query)
        
    else:
        queryField(query)
    stop = time.time()
    print(queryType+" Query Took ",stop-start," seconds.")
    line = f.readline()
f2.close()
f.close()
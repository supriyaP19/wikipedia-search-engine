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

id_title_map = {}
inverted_index = {}
# Fetching the id-title dictionary
try : 
    
    f = open(current_directory_path+"/index/"+id_title_filename,"r")
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
    f = open(current_directory_path+"/index/"+index_filename,"r")
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
    #   we need to create -> {t:(d1), i:(d1,d2), c:(d2), r:(d2), b:(d2)}, if the index was { gandhi-d1:t4#i5, d2:c3#r3    arjun-d2:b7#c5}
    for term in temp_term_cat:
        posting_list_string = inverted_index[term]
        doc_catfreq_list = posting_list_string.split(",")
        for catfreq in doc_catfreq_list:
            temp = catfreq.split(":")
            doc_id = temp[0]
            print(" doc_id : ",doc_id)
            cats = temp[1].split("#")
            print(" cats : ",cats)
            for cat in cats:
                cat_name = cat[0]
                if cat_name in temp_term_cat[term]:
                    if cat_name not in temp_cat_docid: 
                        temp_cat_docid[cat_name] = set()
                    temp_cat_docid[cat_name].add(doc_id)
    
    #   Get the Intersection of all the sets
    set_intersection_result = set()
    i = 0
    for key in temp_cat_docid:
        if i==0:
            set_intersection_result = temp_cat_docid[key]
        else:
            t = set_intersection_result.intersection(temp_cat_docid[key])
            if len(t) == 0:
                set_intersection_result = set_intersection_result.union(temp_cat_docid[key])
            else:
                set_intersection_result = t
        i+=1
        
    # Printing the titles in result
    print_result(set_intersection_result)
                

def queryNormal(words_in_query):
    print(" inside normal query processing")
    tokenized_words = tokenize(words_in_query)
    # print(" tokenized query : ",tokenized_words)
    word_doc_freq = {}
    final_set_of_docid = set()
    i = 0
    for word in tokenized_words:
        word_doc_freq[word] = {}
        if word in inverted_index:
            # Parse the posting list string
            id_freq_mapping = inverted_index[word].split(",")
            set_of_docid = set()
            for items in id_freq_mapping:
                # weighted_freq = 0
                temp = items.split(":")
                doc_id = temp[0]
                fields = temp[1]
                
                set_of_docid.add(doc_id)
                # print(set_of_docid)
                
                # to be checked for page ranking
                # for field in fields:
                #     field_type = field[0]
                #     term_freq = field[1:]
                #     if field_type == 't':
                #         weighted_freq += int(term_freq)*1000
                #     if field_type == 'c' or field_type == 'l' or field_type == 'i' or field_type == 'r':
                #         weighted_freq += int(term_freq)*50
                #     if field_type == 'b':
                #         weighted_freq += int(term_freq)
                # word_doc_freq[word][doc_id] = weighted_freq
            if i == 0:
                final_set_of_docid = set_of_docid
            if i>0:
                final_set_of_docid = final_set_of_docid.intersection(set_of_docid)
            # print(final_set_of_docid)
            i += 1

    # Printing Titles in result
    print_result(final_set_of_docid)
                



while True:
    print(" inside while true ---")
    query = input("Enter your query: ")
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
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
    # print(" tokens : ",tokens)
    # remove all tokens that are not alphanumeric
    ps = PorterStemmer()

    for word in tokens:
        # print(" 1 ")
        if word not in stop_words and word.isalpha():
            # print(" 2 ")
            temp_word = ps.stem(word)
            if len(temp_word) < 3:
                continue
            words.append(temp_word)
    # make is word.isalnum(), if number is necessary to be handled
    # print("words : ",words)
    return words

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
    print("  Result ============================================"+str(len(final_set_of_docid)))
    for doc_id in final_set_of_docid:
        # print(" id : ",doc_id)
        print(id_title_map[doc_id])
                



while True:
    print(" inside while true ---")
    query = input("Enter your query: ")
    start = time.time()
    queryType = ""
    if ":" in query:
        queryType = "Field"
    else:
        queryType = "Normal"
    # queryWords = query.split()
    if queryType == "Normal":
        try:
            print(" right ")
            queryNormal(query)
            stop = time.time()
            print("Query Took ",stop-start," seconds.")
        except:
            print("Some Error Occurred! Try Again")
    else:
        try:
            queryField(queryWords)
            stop = timeit.default_timer()
            print("Query Took ",stop-start," seconds.")
        except:
            print("Some Error Occurred! Try Again")
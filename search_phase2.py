# python3 /home/supriya19/Desktop/sem3/IRE/phase_2/chunk_files /home/supriya19/Desktop/sem3/IRE/phase_2/sampleQueriesAndResults/queryfile /home/supriya19/Desktop/sem3/IRE/phase_2/output/out
import xml.sax as sx
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords 
from nltk.stem import PorterStemmer
import re
import sys
import time
import gc
import math
import os
index_filename = "inverted_index.txt"
id_title_filename = "id_title_mapping.txt"
current_directory_path = os.getcwd()
stop_words = set(stopwords.words('english')) 
arguments = sys.argv[1:]

id_title_map = {}
inverted_index = {}
secondary_index = {}
secondary_index_idtitle = {}
path_to_index_folder = arguments[0]
path_to_input_query_file = arguments[1]
path_to_output_file = arguments[2]
total_docs = 28694
score = {}

# Fetching the id-title secondary dictionary
try:
    print(" creating id-title secondary index----")
    f = open(path_to_index_folder+"/secondary_index_idtitle","r")
    line = f.readline()[:-1]
    while line:
        temp = line.split(":")
        range = temp[0]
        file_name = temp[1]
        secondary_index_idtitle[range] = file_name
        line = f.readline()[:-1]
except:
    print("Can't find the seocndary index file in 'index' Folder.")
    print("Re - run the program when the file is in the same folder.")
    sys.exit(1)

# Fetching the term-posting list secondary dictionary
# try:
# print(" creating secondary index----",path_to_index_folder+"/secondary_index")
f = open(path_to_index_folder+"/secondary_index","r")
line = f.readline()[:-1]
while line:
    temp = line.split(":")
    # print(temp)
    range = temp[0]
    file_name = temp[1]
    secondary_index[range] = file_name
    line = f.readline()[:-1]
# except:
#     print("Can't find the seocndary index file in 'index' Folder.")
#     print("Re - run the program when the file is in the same folder.")
#     sys.exit(1)


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
        if word not in stop_words and word.isalpha():
            if len(word) < 200:
                temp_word = ps.stem(word)
                if len(temp_word) < 3:
                    continue
                words.append(temp_word)
    # make is word.isalnum(), if number is necessary to be handled
    # print("words : ",words)
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
    # print(" query : ",categories)
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
            # print(" doc_id : ",doc_id)
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
        # print(id_title_map[key[0]])
        f2.write(id_title_map[key[0]])
        i += 1
    f2.write("\n")

def file_to_word(tokenized_unique_words):
    f_t_w = {}
    # print(secondary_index)
    lst = list(secondary_index.keys())
    done = []
    for l in lst:
        temp = l.split("-")
        lower_limit = temp[0]
        upper_limit = temp[1]
        for word in tokenized_unique_words:
            if word > lower_limit and word < upper_limit:
                if word not in f_t_w:
                    f_t_w[secondary_index[l]] = []
                f_t_w[secondary_index[l]].append(word)

    return f_t_w    


def return_posting_list(file_path, list_of_wrds):
    result = {}
    f = open(file_path,'r')
    inverted_idx ={}
    line = f.readline()
    while line:
        temp = line.split("-")
        term = temp[0]
        posting = temp[1]
        if term in list_of_wrds:
            result[term] = posting 
        line = f.readline()
    return result

def return_doc_freq(file_name, doc_id):
    # print("FILELNAME : ",file_name)
    f = open(file_name,'r')
    # print(file_name)
    line = f.readline()[:-1]
    freq = 0
    title = ''
    while line:
        temp = line.split("->")
        # print(temp[0])
        did = "".join(temp[0].split())
        # print(" did : ",did)
        if int(did) == doc_id :
            title_freq = temp[1]
            title = title_freq.split("|")[0] 
            freq = title_freq.split("|")[1]
            break
        line = f.readline()
    return title,freq

def return_title(score_of_docs):
    for keys in secondary_index_idtitle:
        lower_limit = int(keys.split("-")[0])
        upper_limit = int(keys.split("-")[1])
        # print(score_of_docs)
        for doc_id in score_of_docs:
            # print(doc_id) # this is doc id
            if type(score_of_docs[doc_id]) != str:
                if int(doc_id) > lower_limit and int(doc_id) < upper_limit:
                    title,freq = return_doc_freq(secondary_index_idtitle[keys], int(doc_id))
                    score_of_docs[doc_id] = title
    return score_of_docs



def calculate_tfidf(dict, tokenized_unique_words, query_length):
    global score
    for term in dict:
        posting_list = dict[term] 
        docs = posting_list.split(",")
        doc_containing_token = len(docs)
        idf = math.log((float(total_docs)/doc_containing_token))
        for doc in docs :
            doc_id = int(doc.split(":")[0])
            t = doc.split(":")[1]
            cats = t.split("#")
            freq = 0
            file_name = ''
            for cat in cats:
                freq += int(cat[1:])
            for keys in secondary_index_idtitle:
                temp = keys.split("-")
                lower_limit = int(temp[0])
                upper_limit = int(temp[1])
                if doc_id > lower_limit and doc_id < upper_limit:
                    # print(" doc condition satisfied ")
                    # print(lower_limit,">", doc_id,">", upper_limit)
                    # print(" keys : ",keys)
                    # print(" secondary_index_idtitle map : ",secondary_index_idtitle)
                    file_name = secondary_index_idtitle[keys]
                    # print(" filename : ", file_name)
                    break
            title,doc_freq = return_doc_freq(file_name, doc_id)
            tf = float(freq)/int(doc_freq)
            Wt_d = tf*idf
            Wt_q = float(tokenized_unique_words[term]) * idf
            cosine_similarity = Wt_d*Wt_q  # Cosine similarity between query and doc
            score[doc_id] = cosine_similarity

def queryNormal(words_in_query):
    global score
    print(" inside normal query processing")
    tokenized_words = tokenize(words_in_query)
    query_length = len(tokenized_words)
    print(" tokenized query : ",tokenized_words)
    i = 0
    tokenized_unique_words = {}
    for wrd in tokenized_words:
        if wrd not in tokenized_unique_words:
            tokenized_unique_words[wrd] = 0
        tokenized_unique_words[wrd] += 1
    f_t_w = file_to_word(tokenized_unique_words)
    for file_path in f_t_w:
        words_in_this_file = f_t_w[file_path]
        dicts = return_posting_list(file_path, words_in_this_file) #dictionary containing posting lists of the words of the query that belong to this file 
        # print(" SCORE : ",score)
        calculate_tfidf(dicts, tokenized_unique_words, query_length) # Calculating the cosine similarity between query and doc by doing dot product to rank docs
    # print("SCORE : ",score)
    score = sorted(score.items(), key=lambda kv: kv[1])
    score = dict(score)
    # print(score)
    
    ranked_docs = return_title(score)
    print("--------------------- Top 12 results")
    i = 0
    all_titles = list(ranked_docs.values())
    for k in reversed(all_titles):
        if i >= 12:
            break
        print(k)
        f2.write(k+"\n")
        i += 1
    f2.write("\n")

        

    # Printing Titles in result
    # print_result(final_set_of_docid)
                

# print(" query file to open :",path_to_input_query_file)
print(" inside main")
f = open(path_to_input_query_file,'r')
f2 = open(path_to_output_file,"w+")
line = f.readline()
while line:
    score = {}
    # print(" inside while line ---")
    # print("LINE : ",line)
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
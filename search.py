#!/usr/bin/python3
import re
import nltk
import sys
import getopt
from nltk.stem.porter import *
import ast
import math

def usage():
    print("usage: " + sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results")

def run_search(dict_file, postings_file, queries_file, results_file):
    """
    using the given dictionary file and postings file,
    perform searching on the given queries file and output the results to a file
    """
    print('running search on the queries...')
    f2 = open(results_file, "w")
    with open("alldocIDs.txt") as f:
        all_docIDs = f.readlines() # get list of all docIDs
    
    dictionary = {}
    
    with open(dict_file) as f:
        dictionary = f.read() # load dictionary into memory
        dictionary = ast.literal_eval(dictionary) # parse the file into a python dictionary

    # open queries file and process each query
    with open(queries_file) as f1:
        lines = f1.readlines()

        for line in lines:
            doc_scores = {}
            docIDs = []

            query_score = query_weight(line, len(all_docIDs), dictionary)
            print(query_score)
            # for docID in all_docIDs:
            #     doc_scores[docID] = doc_weight(line, docID, dict_file, postings_file)

            # for docID, doc_score in doc_scores.items():
            #     docIDs.append((docID, ))

            # get list of docIDs sorted by cosine similarity
            line = ""

            # for docID in docIDs:
            #     line += str(docID[0]) + " "
            
            line.strip()
            line += "\n"

            f2.write(line) # write the result of each query into the results-file
            
    f2.close()
    
def get_postings_list(term, dict_file, postings_file):
    # returns list of docIDs
    postings = ""
    num = 0

    with open(dict_file) as f:
        dictionary = f.read() # load dictionary into memory
        dictionary = ast.literal_eval(dictionary) # parse the file into a python dictionary
        stemmer = PorterStemmer()
        term = stemmer.stem(term.lower()) # normalize the term to be consistent with the dictionary
    
    if term not in dictionary:
        return [] 

    byte_location = dictionary[term][0] # move to beginning of postings list of that term

    with open(postings_file) as f:
        f.seek(byte_location)
        char = f.read(1) # skip the "[" character
        char = f.read(1) # read first postings list char

        while char != "]":
            if char == "(":
                num += 1
            postings += char
            char = f.read(1)
    
    if num > 1:
        postings_list = list(ast.literal_eval(postings))
    else:
        postings_list = [tuple(ast.literal_eval(postings))] # need to use different logic to process postings lists with only one entry

    return postings_list

def query_weight(query, collection_size, dictionary):
    # returns weighting score for queries
    weight = 0

    for term in query.split():
        tf = 1 + math.log(query.count(term), 10)
        if term in dictionary:
            idf = math.log(collection_size/dictionary[term][1], 10)
        else:
            idf = 0

        weight += tf * idf
    
    # perform cosine normalization
    # print(weight)
    return weight

def doc_weight(query, docID, dictionary, postings):
    # returns weighting score for document
    weight = 0
    term_frequency = 0

    for term in query:
        postings_list = get_postings_list(term, dictionary, postings)
        for posting in postings_list:
            if posting[0] == docID:
                term_frequency = posting[1]
        
        if term_frequency > 0:
            tf = 1 + math.log(term_frequency, 10)
        else:
            tf = 0

        weight += tf
    
    # perform cosine normalization 
    return weight

def cosine_similarity(query, document):
    # returns the cosine similarity between the document and query
    pass

dictionary_file = postings_file = file_of_queries = output_file_of_results = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'd:p:q:o:')
except getopt.GetoptError:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == '-d':
        dictionary_file  = a
    elif o == '-p':
        postings_file = a
    elif o == '-q':
        file_of_queries = a
    elif o == '-o':
        file_of_output = a
    else:
        assert False, "unhandled option"

if dictionary_file == None or postings_file == None or file_of_queries == None or file_of_output == None :
    usage()
    sys.exit(2)

run_search(dictionary_file, postings_file, file_of_queries, file_of_output)

#!/usr/bin/python3
import re
import nltk
import sys
import getopt

def usage():
    print("usage: " + sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results")

# TODO: Revise the processing for search.py based on new formats of dictionary.txt and postings.txt

def run_search(dict_file, postings_file, queries_file, results_file):
    """
    using the given dictionary file and postings file,
    perform searching on the given queries file and output the results to a file
    """
    print('running search on the queries...')
    f2 = open(results_file,"w")
    with open("alldocIDs.txt") as f:
        full_postings_list = f.readlines() # get list of all docIDs for processing "NOT" queries

    # open queries file and process each query
    with open(queries_file) as f1:
        lines = f1.readlines()

        for line in lines:
            postfix_exp = create_postfix_exp(line)
            docIDs = evaluate_exp(postfix_exp, dict_file, postings_file, full_postings_list)
            line = ""

            for docID in docIDs:
                line += str(docID[0]) + " "
            
            line.strip()
            line += "\n"

            f2.write(line) # write the result of each query into the results-file
            
    f2.close()
    
def get_postings_list(term, dict_file, postings_file,):
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

def create_postfix_exp(query):
    # use shunting-yard algorithm to turn in-fix query into a post-fix query
    operators = ["AND", "NOT", "OR"]
    op_precedence = {"OR": 0, "AND": 1, "NOT": 2} # order of precedence is NOT, then AND, then OR
    buffer = []
    op_stack = []
    tokens = re.findall("AND|OR|NOT|\(|\)|\w+", query) # tokenize the query, i.e. get all words and operators
    
    for token in tokens:
        if token == "OR" or token == "AND" or token == "NOT":
            while len(op_stack) != 0 and op_stack[-1] in operators and op_precedence[op_stack[-1]] > op_precedence[token]:  
                buffer.append(op_stack.pop())
            op_stack.append(token)
        elif token == "(":
            op_stack.append(token)
        elif token == ")":
            while op_stack[-1] != "(":
                buffer.append(op_stack.pop())
            op_stack.pop() # pop ( character
        else:
            buffer.append(token)
        
    while len(op_stack) != 0:
        buffer.append(op_stack.pop())
    
    print(buffer)
    return buffer

def evaluate_exp(query, dict_file, postings_file, full_postings_list):
    # given a post-fix query as a list, use a stack to evaluate the query
    # returns string containing the resulting docIDs
    operators = ["AND", "NOT", "OR"]
    stack = []

    for token in query:
        if token not in operators:
            stack.append(get_postings_list(token, dict_file, postings_file))
        elif token == "NOT":
            stack.append(logical_not(stack.pop(), full_postings_list))
        elif token == "AND":
            postings_one = stack.pop()
            postings_two = stack.pop()
            stack.append(logical_and(postings_one, postings_two))
        else:
            postings_one = stack.pop()
            postings_two = stack.pop()
            stack.append(logical_or(postings_one, postings_two))

    return stack[0]

def logical_and(postings_one, postings_two):
    # returns the merged postings lists using the and operator

    result = []
    p1 = 0
    p2 = 0

    while p1 != len(postings_one) and p2 != len(postings_two):
        if postings_one[p1][0] == postings_two[p2][0]:
            result.append((postings_one[p1][0], None))
            p1 += 1
            p2 += 1
        elif postings_one[p1][0] < postings_two[p2][0]:
            if postings_one[p1][1] != None and postings_one[postings_one[p1][1]][0] <= postings_two[p2][0]:
                while postings_one[p1][1] != None and postings_one[postings_one[p1][1]][0] <= postings_two[p2][0]:
                    p1 = postings_one[p1][1]
            else:
                p1 += 1
        elif postings_two[p2][0] < postings_one[p1][0]:
            if postings_two[p2][1] != None and postings_two[postings_two[p2][1]][0] <= postings_one[p1][0]:
                while postings_two[p2][1] != None and postings_two[postings_two[p2][1]][0] <= postings_one[p1][0]:
                    p2 = postings_two[p2][1]
            else:
                p2 += 1

    return result

def logical_or(postings_one, postings_two):
    # returns the merged postings lists using the or operator

    result = []
    p1 = 0
    p2 = 0

    while p1 != len(postings_one) and p2 != len(postings_two):
        if postings_one[p1][0] < postings_two[p2][0]:
            result.append((postings_one[p1][0], None))
            p1 += 1
        elif postings_one[p1][0] == postings_two[p2][0]:
            result.append((postings_one[p1][0], None))
            p1 += 1
            p2 += 1
        else:
            result.append((postings_two[p2][0], None))
            p2 += 1

    if p1 != len(postings_one):
        for posting in postings_one[p1:]:
            result.append((posting[0], None))
    
    if p2 != len(postings_two):
        for posting in postings_two[p2:]:
            result.append((posting[0], None))

    return result

def logical_not(postings_list, full_postings_list):
    # returns the merged postings lists using the not operator

    result = []
    p1 = 0
    p2 = 0

    while p1 != len(postings_list) and p2 != len(full_postings_list):
        if postings_list[p1][0] != int(full_postings_list[p2]):
            result.append((int(full_postings_list[p2]), None))
            p2 += 1
        else:
            p1 += 1
            p2 += 1
    
    for docID in full_postings_list[p2:]:
        result.append((int(docID), None))

    return result

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

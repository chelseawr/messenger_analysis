import json
import glob
import sys
import datetime
import os
#import plotly.express as px
from collections import namedtuple, defaultdict

def get_menu_choice(user_name):

    print('''
     \nFacebook Data Parser

    Welcome {}!
    1: Word count
    2: Most common words, individually
    3: Most common words, combined
    4: All of the above
    0: quit\n '''.format(user_name))
    
    choice = 99

    while choice not in range(0,5):
        try:
            choice = int(input("Please choose an option:  "))
            if choice not in range(0,5):
                print(" \nInvalid option")
        except ValueError:
                print("Please choose a menu item by integer")
    if choice == 0:
        print('Goodbye {}!'.format(user_name))
        sys.exit()

    return choice
   
def file_to_list(file_name):
    result = []
    file = open(file_name,"r")
    # get rid of common whitespace,  \n, etc
    file = [x.strip() for x in file]     
    for line in file:
        result.append(line)
    return result

def get_name_input():
    prompt = "Who would you like to search for:  "
    while True:
        #try:
        orig_input = input(prompt).replace(" ","")
        if orig_input == 0:
            sys.exit()
        elif orig_input.isalpha():
            return str(orig_input).lower()
            
        else:
            print("Input must be a string")
        #except ValueError:
         #   print("Input must be a string")
          #  continue

def get_matchlist(guest_name):
    matchlist = []
    path = os.getcwd() + '\\messages\\inbox\\*{}*_*'.format(guest_name)
    for name in glob.glob(path):
        name_index = name.find(guest_name)    
        if(name_index != -1):  
            name += '\\message_1.json'
            with open(name) as file:
                data = json.loads(file.read())
                match_name = recursive_lookup('title',data)  

                # eliminates many conversations w/ multiple parties
                # TODO - eliminate multi party conversations via participant info in json       
                if (len(match_name) <= 20):
                    matchlist.append(match_name)

    return sorted(set(matchlist))

def get_int_input():
    while True:
        choice = input("Please choose an option:  ")
        if choice.isdigit():
            return int(choice)
        else: 
            print("-- Error! -- Input must be an integer menu choice.")

def print_matchlist_menu(matchlist):
    for i in range(0, len(matchlist)):
        print('    {}: {}'.format(i+1, matchlist[i]))
    print("    0: quit\n")
    
    
def get_user_name():
    file = open(os.getcwd() + '\\messages\\autofill_information.json',"r")
    data = json.loads(file.read())
    file.close()   
    for d_info in data.values():
        for key in d_info:
            # TODO save email here for report option
            if key == 'FULL_NAME':
                return d_info[key][0]

# finds key k in dict d, returns value of k
def recursive_lookup(k, d):
    if k in d:
        return d[k]
    for v in d.values():
        if isinstance(v, dict):
            return recursive_lookup(k, v)
    return None

def get_word_count(user_name, match_name, path):
    hour_count = defaultdict(int)
    month_count = defaultdict(int)
    day_count = defaultdict(int)
    day_name_count = defaultdict(int)
    my_message_count = 0
    other_message_count = 0
    last_date = None
    first_date = None

    for name in glob.glob(path):
        with open(name) as json_file:
            data = json.load(json_file)
            for message in data["messages"]:
                date = datetime.datetime.fromtimestamp(message['timestamp_ms']/1000.0)
                month = date.strftime('%Y-%m')
                day = date.strftime('%Y-%m-%d')
                day_name = date.strftime('%A')
                hour = date.time().hour
            
                # Increment message counts
                hour_count[hour] += 1 
                day_name_count[day_name] += 1 
                day_count[day] += 1
                month_count[month] += 1

                 # Determine start and last dates of messages 
                if (first_date and first_date > date) or not first_date:
                    first_date = date 
                if (last_date and last_date < date) or not last_date:
                    last_date = date 

                if(message["sender_name"] == user_name):
                    my_message_count += 1

                if(message["sender_name"] == match_name):
                    other_message_count += 1

     # Get the number of days the messages span over
    num_days = (last_date - first_date).days
    print('starting on',first_date.strftime("%A %B %d %Y"))
   # print(first_date.strftime("%I:%M %p"))
    #print('over {} days'.format(num_days))

    max_month = max(month_count, key=lambda key: month_count[key])
    max_month_count = month_count.get(max_month)

    max_day = max(day_count, key=lambda key: day_count[key])
    max_day_count = day_count.get(max_day)
    print('Highest month:\n{} with {} messsages'.format(max_month, max_month_count))
    print('Highest day:\n{} with {} messsages'.format(max_day, max_day_count))
 
  #  fig = px.line(month_count)
  #  fig.show()

    print(" \n{}'s message count: {}".format(user_name,str(my_message_count )))
    print("{}'s message count: {}".format(match_name,str(other_message_count )))

def get_common_words(path,indiv):
    dict_of_all_words = {}
    
    # TODO - wrap in try   
    # builds list of words to ignore
    common_word_list = file_to_list("common_words.txt")

    for name in glob.glob(path):
        with open(name) as json_file:
            data = json.load(json_file)
            for message in data["messages"]:
                if indiv == 0:
                    try: # avoid non-text messages
                        list_of_words = message["content"].split(" ") 
                            #itterate through the words in the message
                        for word in list_of_words:
                            if word.lower() not in common_word_list and word.isalpha():  
                                # if the word in the message is already in the dict
                                if word in dict_of_all_words: 
                                    dict_of_all_words[word] += 1 
                                else:
                                    dict_of_all_words[word.lower()] = 1 #if the word does not exist, add it!            
                    except:
                        pass
                else:
                    print('calculated per person')

    sorted_words_by_frequency = sorted(dict_of_all_words, key = dict_of_all_words.get, reverse = True)
    print(" \nMost common words sent: " + str(sorted_words_by_frequency[:50])) #print the top 10

while True:
        

    TODO = ''' 
        finish individual top words
        save other party name from message thread
        message[type] filter + counter
        from mm/dd/yy to mm/dd/yy
        create setup.py to allow pip install w/o repo
        add option for 1:* or 1:1 chats
        add option for how many top words to show

        if name only matches 1 item, dont ask
        refactor menus to reuse code - https://stackoverflow.com/a/19964792
        '''
    

    user_name = get_user_name()

    choice = get_menu_choice(user_name)

    name_match_input = get_name_input()
    matchlist = get_matchlist(name_match_input)

    print_matchlist_menu(matchlist)
    match_choice = get_int_input()
    if match_choice == 0:
        print('Goodbye {}!'.format(user_name))
        sys.exit()
    else: match_name = matchlist[match_choice-1]

    path = os.getcwd() + '\\messages\\inbox\\{}_*\\message_*'.format(match_name.replace(" ","").lower())

    if choice == 1: 
        get_word_count(user_name,match_name,path)
    elif choice == 2:
        print('most common words individually between {} and {}'.format(user_name,match_name))
        indiv = 1
        print('---------in progress----------\n')
    elif choice == 3:
        print('most common words between {} and {}'.format(user_name,match_name))
        indiv = 0
        get_common_words(path,indiv)
    elif choice == 4:
        print('all of the above')
        indiv = 0
        get_common_words(path,indiv)
        get_word_count(user_name,match_name,path)

    
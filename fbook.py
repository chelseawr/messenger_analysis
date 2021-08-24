from __future__ import print_function, unicode_literals
import json
import glob
import sys
import datetime
import os
import time
import plotly.express as px
from pprint import pprint
from collections import namedtuple, defaultdict
from PyInquirer import prompt, Separator

def file_to_list(file_name):
    result = []
    file = open(file_name,"r")

    # get rid of common whitespace,  \n, etc
    file = [x.strip() for x in file]     
    for line in file:
        result.append(line)
    return result

# search for provided input name in inbox
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
                
    matchlist = sorted(set(matchlist))
    matchlist.append('Quit')
    return matchlist

def print_matchlist_menu(matchlist):
    for i in range(0, len(matchlist)):
        print('    {}: {}'.format(i+1, matchlist[i]))
    print("    0: quit\n")
   
def get_autofill(value):
    file = open(os.getcwd() + '\\messages\\autofill_information.json',"r")
    data = json.loads(file.read())
    file.close()   
    for d_info in data.values():
        for key in d_info:
            # TODO save email here for report option
            if key == value:
                return d_info[key][0]


# finds key k in dict d, returns value of k
def recursive_lookup(k, d):
    if k in d:
        return d[k]
    for v in d.values():
        if isinstance(v, dict):
            return recursive_lookup(k, v)
    return None

def analyze_name(user_name, match_name, path):
    timestamp = time.perf_counter()
    hour_count = defaultdict(int)
    month_count = defaultdict(int)
    day_count = defaultdict(int)
    day_name_count = defaultdict(int)
    friends_list = defaultdict(str)
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
  #  print('From {} to {}'.format(first_date.strftime("%A %B %d %Y"),last_date.strftime("%A %B %d %Y")))

  #  print('over {} days'.format(num_days))
 

    print(" \n{}'s message count: {}".format(user_name,str(my_message_count )))
    print("{}'s message count: {}".format(match_name,str(other_message_count )))

    print('Processed data in {0:.2f} seconds.'.format(time.perf_counter() - timestamp))

    return hour_count, month_count, day_count, day_name_count

def show_hourly_graph(hour_count):
    xdata_hourly = ['{0}:00'.format(i) for i in range(24)]
    
def show_monthly_graph(month_count):
    max_month = max(month_count, key=lambda key: month_count[key])
    max_month_count = month_count.get(max_month)
    print('Highest month:\n{} with {} messsages'.format(max_month, max_month_count))

        # monthly count bar graph 
    month_vals = list(month_count.values())
    month_dates = list(month_count.keys())
    the_dict = {'dates':month_dates, 'y_vals':month_vals}
    #fig = px.bar(the_dict, x='dates', y='y_vals')
    #fig.show()

def show_daily_graph(day_count):
    xdata_day_name = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

    max_day = max(day_count, key=lambda key: day_count[key])
    max_day_count = day_count.get(max_day)
    print('Highest day:\n{} with {} messsages'.format(max_day, max_day_count))

def get_common_words(path):
    dict_of_all_words = {}
    
    # TODO - wrap in try   
    # builds list of words to ignore
    common_word_list = file_to_list("common_words.txt")

    for name in glob.glob(path):
        with open(name) as json_file:
            data = json.load(json_file)
            for message in data["messages"]:
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
        

    sorted_words_by_frequency = sorted(dict_of_all_words, key = dict_of_all_words.get, reverse = True)
    print(" \nMost common words sent: " + str(sorted_words_by_frequency[:50])) #print the top 10
  #  pprint(sorted_words_by_frequency[:50])

def is_input_valid(value):
    if value.isalpha() and value is not 0:
        return True
    else: return False

def search_filter(value):
    return value.replace(" ","").lower()

menus = [
    {
        'type': 'checkbox',
        'name': 'menu_opt',
        'message': 'Pick a menu option(s)',
        'choices': [
            {
                'name':  'Monthly word count',
                'checked': True
            },
            {
                'name': 'Daily word count'
            },
            {
                'name': 'Hourly word count'
            },
            {
                'name': 'Day of week word count'
            },
            {
                'name': 'Most common words'
            }
            ]
    },
    {
        'type': 'confirm',
        'name': 'show_graphs',
        'message': 'Show graph',
        'default': False
    },
    {
        'type': 'input',
        'name': 'name_input',
        'message':'Who would you like to search for?',
        'validate': is_input_valid,
        'filter': search_filter
    }

]

user_name = get_autofill('FULL_NAME')
first_name = get_autofill('FIRST_NAME')
header = '╔════════════════════╗'
footer = '╚════════════════════╝'
print('\n\t{}\n\t Facebook Data Parser\n\t Welcome {}!\n\t{}'.format(header,first_name,footer))

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
        '''

    print('\n')
    ans = prompt(menus)
    print('\tans',ans)
    search_val = ans.get('name_input')
    menu_choice = ans.get('menu_opt')
    graph_bool = ans.get('show_graphs')

  #  who menu
    choose_name_menu = {
        'type': 'list',
        'name': 'name_opt',
        'message': 'Choose a name:',
        'choices': get_matchlist(search_val)
    }
    
    # get name choice
    match_ans = prompt(choose_name_menu)
    match_name = match_ans.get('name_opt')

    path = os.getcwd() + '\\messages\\inbox\\{}_*\\message_*'.format(match_name.replace(" ","").lower())
    
    if 'Quit' in menu_choice:
        print('Goodbye {}!'.format(user_name))
        sys.exit()

    if 'Most common words' in menu_choice:
        print('most common words  between {} and {}'.format(user_name,match_name))
        get_common_words(path)
    if 'Monthly word count' or 'Hourly word count' or 'Daily word count' in menu_choice: 
        hour_count, month_count, day_count, day_name_count = analyze_name(user_name,match_name,path)

        if graph_bool:
            if 'Monthly word count' in menu_choice: show_monthly_graph(month_count)
            if 'Hourly word count' in menu_choice: show_hourly_graph(hour_count)
            if 'Daily word count' in menu_choice: show_daily_graph(day_count)
        #if menu_choice == 'Day of week word count':



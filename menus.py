
def is_input_valid(value):
    if value.isalpha() and value is not 0:
        return True
    else: return False

def search_filter(value):
    return value.replace(" ","").lower()


graph_menu = {
        'type': 'confirm',
        'name': 'show_graphs',
        'message': 'Show graph',
        'default': False
    }

name_menu = {
        'type': 'input',
        'name': 'name_input',
        'message':'Who would you like to search for?',
        'validate': is_input_valid,
        'filter': search_filter
    }

entry_menu =  {
        'type': 'list',
        'name': 'menu_opt',
        'message': 'Pick a menu option(s)',
        'choices': [
            {
                'name':  'Monthly word count',
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
            },
            {
                'name': 'Quit'
            }
            ]
    }
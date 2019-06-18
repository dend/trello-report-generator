import urllib.request
import json
import os
import sys
import string
from datetime import datetime
import time
import argparse

access_key = ''
access_token = ''
tracking_board = ''
completed_list_name = ''
next_week_list_name = ''
blocked_list_name = ''

parser = argparse.ArgumentParser(description='Trello Report Generator')

subparsers = parser.add_subparsers(dest="commands_parser")
make_parser = subparsers.add_parser('make')

make_parser.add_argument('--access-key', metavar='K', type=str,
                   help='Trello access key.')
make_parser.add_argument('--access-token', type=str, metavar='T',
                   help='Trello access token.')
make_parser.add_argument('--work-board', type=str, metavar='W',
                   help='Name of the board that contains cards used for the report.')
make_parser.add_argument('--completed-list', type=str, metavar='C',
                   help='Name of the list of completed items.')
make_parser.add_argument('--next-list', type=str, metavar='N',
                   help='Name of the list of items slated for next week.')
make_parser.add_argument('--blocked-list', type=str, metavar='B',
                   help='Name of the list of items that one is blocked on.')

args = parser.parse_args()

def perform_request(qualified_url):
    data = []

    try:
        request = urllib.request.Request(qualified_url)
        response = urllib.request.urlopen(request)

        data = json.loads(response.read().decode('utf-8'))
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
    except:
        print('Something is wrong...')
    
    return data

def get_boards(access_key, access_token):
    url = string.Template('https://api.trello.com/1/members/me/boards?key=$user_key&token=$user_token')
    qualified_url = url.substitute(user_key=access_key, user_token=access_token)
    
    boards_data = perform_request(qualified_url)
    
    return boards_data

def get_lists(board_id, access_key, access_token):
    url = string.Template('https://api.trello.com/1/boards/$user_board_id/lists?key=$user_key&token=$user_token')
    qualified_url = url.substitute(user_key=access_key, user_token=access_token, user_board_id=board_id)

    list_data = perform_request(qualified_url)

    return list_data

def get_list_cards(list_id, access_key, access_token):
    url = string.Template('https://api.trello.com/1/lists/$user_list_id/cards?key=$user_key&token=$user_token')
    qualified_url = url.substitute(user_key=access_key, user_token=access_token, user_list_id=list_id)

    card_data = perform_request(qualified_url)

    return card_data

def get_card_comments(card_id, access_key, access_token):
    url = string.Template('https://api.trello.com/1/cards/$user_card_id/actions?key=$user_key&token=$user_token&fields=all')
    qualified_url = url.substitute(user_key=access_key, user_token=access_token, user_card_id=card_id)

    card_data = perform_request(qualified_url)

    relevant_data = [x for x in card_data if x['type'] == 'commentCard']

    return relevant_data

def generate_section_report(section_name, section_subheading, card_set):
    section_template = ''
    baseline_template = ''

    with open('reportgen/section_template.md', 'r') as template_file:
        section_template = template_file.read()
    
    if section_template:
        formalized_template = string.Template(section_template)
        baseline_template = formalized_template.substitute(custom_section_name=section_name, custom_section_subheading=section_subheading) + '\n\n'
        if card_set:
            for card in card_set:
                card_field = '- **' + card['name'] + '**. ' + card['desc'] + '\n'
                individual_card_data = get_card_comments(card['id'], access_key, access_token)
                if individual_card_data:
                    for card_comment in individual_card_data:
                        card_field += '    - ' + card_comment['data']['text'] + '\n'

                baseline_template += card_field
        
    return baseline_template


def generate_report(completed_section, planned_section, blocked_section):
    with open('reportgen/report_template.md', 'r') as template_file:
        report_template = template_file.read()

    if report_template:
        formalized_template = string.Template(report_template)
        baseline_template = formalized_template.substitute(report_name='DenDeli Weekly Report', report_description='Produced on: **' + str(datetime.now().date()) + "**") + '\n\n'

        baseline_template += completed_section + '\n\n'
        baseline_template += blocked_section + '\n\n'
        baseline_template += planned_section

        with open('report_' + time.strftime("%Y%m%d-%H%M%S") + '.md', 'w') as report_file:
            report_file.write(baseline_template)

if (args.commands_parser == 'make'):
    if (args.access_key is not None) and (args.access_token is not None) and (args.work_board is not None) and (args.completed_list is not None) and (args.next_list is not None) and (args.blocked_list is not None):
        access_key = args.access_key
        access_token = args.access_token
        tracking_board = args.work_board
        completed_list_name = args.completed_list
        next_week_list_name = args.next_list
        blocked_list_name = args.blocked_list

    else:
        print('Required parameters missing.')
        os._exit(0)
else:
    print('Could not understand command.')
    os._exit(0)

boards = get_boards(access_key, access_token)

target_board = [x for x in boards if x['name'] == tracking_board]
if not target_board:
    print('Could not find work board.')
    os._exit(0)

lists = get_lists(target_board[0]["id"], access_key, access_token)
if not lists:
    print('No lists to work with.')
    os._exit(0)

target_list = [x for x in lists if x['name'] == completed_list_name]
if not target_list:
    print('Could not find completed list.')
    os._exit(0)

completed_cards = get_list_cards(target_list[0]['id'], access_key, access_token)
completed_section = ''
completed_relevant_cards = []

for card in completed_cards:
    due_date = datetime.strptime(card['due'], '%Y-%m-%dT%H:%M:%S.000Z')
    
    if due_date.date() <= datetime.now().date(): # Card is due later.
        completed_relevant_cards.append(card)

completed_section = generate_section_report('Progress', 'Things done this week', completed_relevant_cards)

target_list = [x for x in lists if x['name'] == next_week_list_name]
if not target_list:
    print('Could not find next week list.')
    os._exit(0)

next_week_cards = get_list_cards(target_list[0]['id'], access_key, access_token)
next_week_section = ''
next_week_relevant_cards = []

for card in next_week_cards:
    due_date = datetime.strptime(card['due'], '%Y-%m-%dT%H:%M:%S.000Z')

    if due_date.date() > datetime.now().date():
        next_week_relevant_cards.append(card)
if next_week_relevant_cards:
    next_week_section = generate_section_report('Planned', 'Things planned for next week', next_week_relevant_cards)

target_list = [x for x in lists if x['name'] == blocked_list_name]
if not target_list:
    print('Could not find blocked list.')
    os._exit(0)

blocked_cards = get_list_cards(target_list[0]['id'], access_key, access_token)
blocked_section = ''

blocked_section = generate_section_report('Problems', 'Items that I am blocked on.', blocked_cards)

generate_report(completed_section, next_week_section, blocked_section)
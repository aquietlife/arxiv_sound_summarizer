import datetime
from dotenv import load_dotenv, find_dotenv
import json
import ollama
import os
import requests
from tqdm import tqdm
import xmltodict

print("let's go :D")

load_dotenv(find_dotenv())

# get data from arxiv api 
# https://gist.github.com/jozefg/c2542f51a0b9b3f6efe528fcec90e334

url = 'http://export.arxiv.org/api/query?search_query=cat:cs.SD&sortBy=submittedDate&sortOrder=descending&max_results=50'
response = requests.get(url)
xml_data = response.text  # data.read().decode('utf-8')
print(xml_data)

# convert xml to json
dict_data = xmltodict.parse(xml_data)
json_data = json.dumps(dict_data)
print(json_data)

# get entries from the past 4 days
today = datetime.date.today()
entries = []
for entry in dict_data['feed']['entry']:
    date = datetime.datetime.strptime(entry['published'], '%Y-%m-%dT%H:%M:%SZ').date()
    if (today - date).days <= 4: # <= to be inclusive in case we miss something posted late on the 4th day
        entries.append(entry)
print(entries)

# print entries
for e in entries:
    print(e['title'] + ': ' + e['published'])
    print(e['summary']) 
    print('----')

print(len(entries)) 

# use ollama / mistral to get a summary of all the papers in entries
# trying with generate / prompt instead of chat
# https://ollama.com/
# https://github.com/ollama/ollama
# https://github.com/ollama/ollama-python
# https://wandb.ai/byyoung3/ml-news/reports/How-to-Run-Mistral-7B-on-an-M1-Mac-With-Ollama--Vmlldzo2MTg4MjA0

class Summary:
    def __init__(self, title, summary, generated_summary_sentence, link):
        self.title = title
        self.summary = summary
        self.generated_summary_sentence = generated_summary_sentence
        self.link = link

summaries = []

for e in tqdm(entries):
    response = ollama.generate(model='mistral', 
                           prompt='Please generate a one sentence summary of the following article description: ' + e['summary'] ,
            )
    
    s = Summary(
        title = e['title'].replace('\n', ''), # remove newlines from titles
        summary = e['summary'],
        generated_summary_sentence = response['response'],
        link = e['link'][0]['@href']
    )    

    summaries.append(s)

for s in summaries:
    print(s.title)
    print(s.generated_summary_sentence)
    print(s.link)
    print('----')

DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL')

print("shipping to discord")

for s in summaries:
    data = {
        "content" : '**' + s.title + '**' + '\n\n' + s.generated_summary_sentence + '\n\n' + s.link
    }
    requests.post(DISCORD_WEBHOOK_URL, data=data)

print("done! :)")
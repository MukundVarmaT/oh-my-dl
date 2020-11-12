import pickle
import feedparser
import re
from datetime import datetime
import numpy as np
from collections import Counter
import requests
from bs4 import BeautifulSoup
from typing import Dict, List
import json

FG_COLOR = {
    "red" : "\x1b[31m",
    "green" : "\x1b[92m",
    "yellow" : "\x1b[33m",
    "end" : "\033[0m"
}
BG_COLOR = {
    "red" : "\x1b[41m",
    "green" : "\x1b[42m",
    "yellow" : "\x1b[43m",
    "end" : "\033[0m"
}

# save as pickle file
def save_pickle(file_path, x):
    with open(file_path, 'wb') as handle:
        pickle.dump(x, handle, protocol=pickle.HIGHEST_PROTOCOL)

# load pickle file
def load_pickle(file_path):
    with open(file_path, 'rb') as handle:
        data = pickle.load(handle)
    return data

def encode_feedparser_dict(d):
    if isinstance(d, feedparser.FeedParserDict) or isinstance(d, dict):
        j = {}
        for k in d.keys():
            j[k] = encode_feedparser_dict(d[k])
        return j
    elif isinstance(d, list):
        l = []
        for k in d:
            l.append(encode_feedparser_dict(k))
        return l
    else:
        return d

# remove latex formatting and tags
def rem_tex_fmt(text):
    text = text.replace("\n", " ").replace("\r", "")
    text = re.sub(r"\s+"," ",text)
    text = text.replace(r"\textit{","")
    text = text.replace(r"\textbf{","")
    text = text.replace(r"\emf{","")
    text = text.replace("}","")
    text = text.replace("\\", "")
    return text

# convert datetime in string to format
def convert_to_datetime(date):
    date = date.split("T")[0]
    date = datetime.strptime(date, '%Y-%m-%d').date()
    return date

def parse_arxiv_url(url):
  id = url.rsplit("/",1)[1]
  url = f"https://arxiv.org/pdf/{id.split('v')[0]}"
  return url

# embeddings
MAX_BATCH_SIZE = 16
URL = "https://model-apis.semanticscholar.org/specter/v1/invoke"
def split_chunks(paper_list, chunk_size=MAX_BATCH_SIZE):
    for i in range(0, len(paper_list), chunk_size):
        yield paper_list[i : i + chunk_size]

def filter_abstract(abstract):
    abstract = re.sub(r'^https?:\/\/.*[\r\n]*', '[LINK]', abstract, flags=re.MULTILINE)
    abstract = re.sub(r"[\(\[].*?[\)\]]", "", abstract)
    abstract = re.sub(r"[\$].*?[\$]", "[EQN]", abstract)
    abstract = " ".join(abstract.split())
    return abstract

def embed(papers):
    embeddings: Dict[str, List[float]] = {}
    for chunk in split_chunks(papers):
        response = requests.post(URL, json=chunk)
        if response.status_code != 200:
            return None
        for paper in response.json()["preds"]:
            embeddings[paper["paper_id"]] = paper["embedding"]
    # convert dict to array
    embeddings = list(dict(sorted(embeddings.items())).values()) # sorting for sanity sakes
    embeddings = [np.array(e).reshape((1,-1)) for e in embeddings]
    return embeddings

def softmax(x):
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum()

def get_recent_trending():
    URL = 'https://paperswithcode.com/'
    page = requests.get(URL)
    content = BeautifulSoup(page.content, 'html.parser')
    titles = []
    for c in content.find_all('h1')[1:]:
        titles.append(c.text)
    return titles

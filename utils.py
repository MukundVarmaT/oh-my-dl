import pickle
import feedparser
from datetime import datetime
import re
import requests
from bs4 import BeautifulSoup

# download 
def download(url, path):
    response = requests.get(url, stream=True, verify=False)
    total_size = int(response.headers.get('content-length', 0))
    chunk_size = 1024 * 1024
    i = 0
    with open(path, "wb") as handle:
        for data in response.iter_content(chunk_size=chunk_size):
            progress_bar(i/total_size, status="downloading data...")
            handle.write(data)
            i+=chunk_size
        progress_bar(1)
        

# simple progress bar without tqdm :P
def progress_bar(progress = 0, status = "", bar_len = 20):
    status = status.ljust(30)
    if progress == 1:
        status = "{}\r\n".format("Done...".ljust(30))
    block = int(round(bar_len*progress))
    text = "\rProgress: [{}] {}% {}".format( "#"*block + "-"*(bar_len-block), round(progress*100,2), status)
    print(text, end="")

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

# parse arxiv url of format https://arxiv.org/abs/1904.07399v3 --> https://arxiv.org/pdf/1904.07399
def parse_arxiv_url(url):
  id = url.rsplit("/",1)[1]
  url = f"https://arxiv.org/pdf/{id.split('v')[0]}"
  return url

# filter abstract containing repository links, equations.
def filter_abstract(abstract):
    abstract = re.sub(r'^https?:\/\/.*[\r\n]*', '[LINK]', abstract, flags=re.MULTILINE)
    abstract = re.sub(r"[\(\[].*?[\)\]]", "", abstract)
    abstract = re.sub(r"[\$].*?[\$]", "[EQN]", abstract)
    abstract = " ".join(abstract.split())
    return abstract

# retrieve relevant urls from abstract
def extract_url(abstract):
    url = re.findall(r"\b((?:https?://)?(?:(?:www\.)?(?:[\da-z\.-]+)\.(?:[a-z]{2,6})|(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)|(?:(?:[0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,7}:|(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}|(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}|(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}|(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:(?:(?::[0-9a-fA-F]{1,4}){1,6})|:(?:(?::[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(?::[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(?:ffff(?::0{1,4}){0,1}:){0,1}(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])|(?:[0-9a-fA-F]{1,4}:){1,4}:(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])))(?::[0-9]{1,4}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])?(?:/[\w\.-]*)*/?)\b", abstract) 
    url = [u for u in url if "github" in u]
    if len(url)!=0:
        return ", ".join(url)
    else:
        return ""

# get recent trending from papers with code
def get_recent_trending():
    URL = 'https://paperswithcode.com/'
    page = requests.get(URL)
    content = BeautifulSoup(page.content, 'html.parser')
    titles = []
    for c in content.find_all('h1')[1:]:
        titles.append(c.text)
    return titles
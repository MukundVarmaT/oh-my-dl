import argparse
import utils
import warnings
import urllib
import time
import feedparser
import numpy as np
from rank_bm25 import BM25Okapi
import math
import os
from wordcloud import WordCloud
from PIL import Image
from config import *
warnings.filterwarnings("ignore")

try:
    WIDTH, HEIGHT = ((os.popen("xrandr | grep '*'").read()).split()[0]).split("x")
    WIDTH = int(WIDTH)
    HEIGHT = int(HEIGHT)
except:
    WIDTH = 1920
    HEIGHT = 1080

def update():
    try:
        db = utils.load_pickle(DB_PATH)
        last_update = sorted(db['date'])[-1]
    except:
        utils.download(DB_URL, DB_PATH)
        db = utils.load_pickle(DB_PATH)
        last_update = sorted(db['date'])[-1]

    # query arxiv api
    n_added = 0
    indx = 0

    while indx<MAX_ITER:
        
        url = BASE_URL + QUERY_FMT.format(DEF_QUERY, indx, RESULTS_PER_ITER)
        try:
            with urllib.request.urlopen(url, timeout=5.0) as url:
                response = url.read()
        except TimeoutError:
            continue
        response = feedparser.parse(response)

        for entry in response.entries:
            e = utils.encode_feedparser_dict(entry)
            paper_url = utils.parse_arxiv_url(e["link"])
            date = e["published"]
            date = utils.convert_to_datetime(date)

            # content already in database
            if paper_url in db["url"]:
                if date <= last_update:
                    indx = MAX_ITER
                    break
                else:
                    continue
            
            # retrieve and clean some text
            title = e["title"]
            title = utils.rem_tex_fmt(title)
            authors = ", ".join(f"{n['name']}" for n in e["authors"])
            abstract = e["summary"]
            abstract = utils.rem_tex_fmt(abstract)
            other_urls = utils.extract_url(abstract)
            journal = e["arxiv_journal_ref"] if "arxiv_journal_ref" in e else ""
            journal = utils.rem_tex_fmt(journal)

            db["date"].append(date)
            db["url"].append(paper_url)
            db["title"].append(title)
            db["authors"].append(authors)
            db["abstract"].append(abstract)
            db["journal"].append(journal)
            db["other_urls"].append(other_urls)
            n_added += 1

        if len(response.entries) == 0:
            utils.progress_bar(indx/MAX_ITER, status="API not responding. retrying...") 
        if indx == MAX_ITER:
            utils.progress_bar(1) 
        else:
            indx += 100
            utils.progress_bar(indx/MAX_ITER, status=f"Fetching papers from {date}...") 
        time.sleep(WAIT_TIME)
    print(f"{n_added} papers added to database")

    if True:
        indx = list(np.argsort(db["date"]))
        db["date"] = list(np.array(db["date"])[indx])
        db["url"] = list(np.array(db["url"])[indx])
        db["title"] = list(np.array(db["title"])[indx])
        db["authors"] = list(np.array(db["authors"])[indx])
        db["abstract"] = list(np.array(db["abstract"])[indx])
        db["journal"] = list(np.array(db["journal"])[indx])
        db["other_urls"] = list(np.array(db["other_urls"])[indx])
        utils.save_pickle(DB_PATH, db)

        tkn_corpus = []
        for indx in range(len(db["url"])):
            title = db["title"][indx].lower()
            abstract = utils.filter_abstract(db["abstract"][indx].lower())
            tkn_corpus.append((title + " " + abstract).split(" "))
        bm25 = BM25Okapi(tkn_corpus)
        utils.save_pickle(CACHE_BM25, bm25)

def search_query(query):
    try:
        db = utils.load_pickle(DB_PATH)
        bm25 = utils.load_pickle(CACHE_BM25)
    except:
        raise Exception("Cached files not found. Run update command!")
    
    query = query.lower().split(";")
    n_per_query = math.ceil(MAX_FOUND/len(query))
    titles = []
    weights = []
    for q in query:
        top_ind = bm25.get_top_n(q.split(" "), list(range(len(db["url"]))), n_per_query)
        for ind in top_ind:
            titles.append(f"{db['title'][ind]} ({ind})")
        weights.extend([_ for _ in range(n_per_query, 0, -1)])  
    set_wallpaper(dict(zip(titles, weights)))  

def set_wallpaper(data):
    wordcloud = WordCloud(
        background_color=BACKGROUND,
        width=WIDTH - 2*MARGIN,
        height=HEIGHT - 2*MARGIN,
        min_font_size=MIN_FONT_SIZE,
        prefer_horizontal=0.7
    ).generate_from_frequencies(data)
    wordcloud.to_file(WORDCLOUD_PATH)
    background = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    wordcloud = Image.open(WORDCLOUD_PATH, "r").convert("RGB")
    background.paste(wordcloud, (MARGIN, MARGIN))
    background.save(WORDCLOUD_PATH)
    os.system(f"gsettings set org.gnome.desktop.background picture-uri file://{WORDCLOUD_PATH}")

def get_info(id):
    try:
        db = utils.load_pickle(DB_PATH)
    except:
        raise Exception("Cached files not found. Run update command!")
    if id < len(db["url"]):
        print(f"Date: {db['date'][id]}, Paper URL: {db['url'][id]}, Other URLs: {db['other_urls'][id]}, Journal: {db['journal'][id]}")
        print(f"Title: {db['title'][id]}")
        print(f"Authors: {db['authors'][id]}")
        print(f"{db['abstract'][id]}")
    else:
        raise Exception("Invalid ID")

def download(id):   
    try:
        db = utils.load_pickle(DB_PATH)
    except:
        raise Exception("Cached files not found. Run update command!")
    if not os.path.exists(PDF_DOWNLOAD):
        os.makedirs(PDF_DOWNLOAD)
    if id < len(db["url"]):
        utils.download(db["url"][id], os.path.join(PDF_DOWNLOAD, db["title"][id]+".pdf"))
    else:
        raise Exception("Invalid ID")

def trending():
    try:
        db = utils.load_pickle(DB_PATH)
    except:
        raise Exception("Cached files not found. Run update command!")

    recent = utils.get_recent_trending()
    titles = []
    weights = []
    for title in recent:
        try:
            ind = db["title"].index(utils.rem_tex_fmt(title))
            titles.append(f"{db['title'][ind]} ({ind})")
        except:
            continue
    weights = [_ for _ in range(len(titles), 0, -1)]
    set_wallpaper(dict(zip(titles, weights))) 

def new():
    try:
        db = utils.load_pickle(DB_PATH)
    except:
        raise Exception("Cached files not found. Run update command!")
    titles = []
    for ind in range(len(db["url"])-MAX_FOUND, len(db["url"])):
        titles.append(f"{db['title'][ind]} ({ind})")
    weights = [_ for _ in range(len(titles))]
    set_wallpaper(dict(zip(titles, weights))) 

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OH-MY-DL: command line toolkit to keep up with recent trends in DL")
    parser.add_argument("-u", "--update", action="store_true", help="Update database")
    parser.add_argument("-t", "--trending", action="store_true", help="Fetch trending")
    parser.add_argument("-n", "--new", action="store_true", help="Fetch latest")
    parser.add_argument("-q", "--query", default=None, type=str, help="Query database (semi-colon seperated) and update background")
    parser.add_argument("-i", "--info", default=None, type=int, help="Return paper info by id")
    parser.add_argument("-d", "--download", default=None, type=int, help="Download paper pdf by id")

    args = parser.parse_args()

    if args.update:
        update()
        exit()
    if args.trending:
        trending()
        exit()
    if args.new:
        new()
        exit()
        
    if args.query:
        search_query(args.query)
    elif args.info:
        get_info(args.info)
    elif args.download:
        download(args.download)
    else:
        parser.print_help()
        exit()
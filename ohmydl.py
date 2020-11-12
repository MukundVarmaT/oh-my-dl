import argparse
import utils
import urllib
import feedparser
from tqdm import tqdm
import time
import numpy as np
from datetime import datetime, timedelta
from utils import FG_COLOR, BG_COLOR
import re
from rank_bm25 import BM25Okapi
from wordcloud import WordCloud
import os
from scipy.spatial.distance import cdist
import warnings
import math
warnings.filterwarnings("ignore")

DB_PATH = "./db.pickle"
BASE_URL = "http://export.arxiv.org/api/query?"
DEF_QUERY = "cat:cs.CV+OR+cat:cs.AI+OR+cat:cs.LG+OR+cat:cs.CL+OR+cat:cs.NE+OR+cat:stat.ML"
QUERY_FMT = "search_query={}&sortBy=submittedDate&start={}&max_results={}"
MAX_ITER = 10000
MAX_DAYS = 10
RESULTS_PER_ITER = 100
WAIT_TIME = 5.0
USR_SETTINGS = "./.usr.pickle"
MAX_FOUND = 5
TKN_CORPUS = "./.tkn_corpus.pickle"
MAX_RECO = 20
BACKGROUND = "#101010"
MIN_FONT_SIZE = 8
MARGIN = 30
try:
    WIDTH, HEIGHT = ((os.popen("xrandr | grep '*'").read()).split()[0]).split("x")
    WIDTH = int(WIDTH)
    HEIGHT = int(HEIGHT)
except:
    WIDTH = 1920
    HEIGHT = 1080

def build_db():
    try:
        db = utils.load_pickle(DB_PATH)
        last_updated = sorted(db['date'])[-1]
        print(f"{FG_COLOR['green']} Existing database found. Last updated on {last_updated}{FG_COLOR['end']}\n")

    except:
        db = {
            "date": [],
            "url": [],
            "title": [],
            "authors": [],
            "abstract": [],
            "journal": [],
            "embed": [],
        }
        print(f"{FG_COLOR['yellow']} Database not found. Creating new database at {DB_PATH}{FG_COLOR['end']}\n")
        last_updated = datetime.now().date() - timedelta(days=MAX_DAYS)

    # query arxiv api
    n_added = 0
    indx = 0
    pbar = tqdm(total=MAX_ITER, bar_format="{l_bar}%s{bar}%s{r_bar}" % (FG_COLOR['yellow'],FG_COLOR['end']))

    while indx<MAX_ITER:
        
        url = BASE_URL + QUERY_FMT.format(DEF_QUERY, indx, RESULTS_PER_ITER)
        try:
            with urllib.request.urlopen(url, timeout=5.0) as url:
                response = url.read()
        except TimeoutError:
            continue
        response = feedparser.parse(response)
        emb_q = []

        for entry in response.entries:
            e = utils.encode_feedparser_dict(entry)
            paper_url = utils.parse_arxiv_url(e["link"])
            date = e["published"]
            date = utils.convert_to_datetime(date)

            # content already in database
            if paper_url in db["url"]:
                if date <= last_updated:
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
            journal = e["arxiv_journal_ref"] if "arxiv_journal_ref" in e else ""
            journal = utils.rem_tex_fmt(journal)

            # create query to retrieve embeddings
            emb_q.append({
                "paper_id": n_added,
                "title": title,
                "abstract": utils.filter_abstract(abstract)
            })

            db["date"].append(date)
            db["url"].append(paper_url)
            db["title"].append(title)
            db["authors"].append(authors)
            db["abstract"].append(abstract)
            db["journal"].append(journal)
            n_added += 1

        if len(emb_q)!=0:
            embed = utils.embed(emb_q)
            if embed is not None:
                db["embed"].extend(embed)
                emb_q = []
            else:
                pbar.set_description(f"{FG_COLOR['red']} API did not respond! Retrying{FG_COLOR['end']}")  
                continue   
        if len(response.entries) == 0:
            pbar.set_description(f"{FG_COLOR['red']} API did not respond! Retrying{FG_COLOR['end']}") 
        if indx == MAX_ITER:
            pbar.set_description(f"{FG_COLOR['green']} Database updated{FG_COLOR['end']}")
            pbar.update(len(pbar)-pbar.n)
        else:
            indx += 100
            pbar.set_description(f"{FG_COLOR['yellow']} [{n_added}/{indx}]{FG_COLOR['end']}")
            pbar.update(100)
        time.sleep(WAIT_TIME)
    pbar.close()
    print(f"{FG_COLOR['green']} {n_added} papers added to database{FG_COLOR['end']}")

    if n_added!=0:
        indx = list(np.argsort(db["date"]))
        db["date"] = list(np.array(db["date"])[indx])
        db["url"] = list(np.array(db["url"])[indx])
        db["title"] = list(np.array(db["title"])[indx])
        db["authors"] = list(np.array(db["authors"])[indx])
        db["abstract"] = list(np.array(db["abstract"])[indx])
        db["journal"] = list(np.array(db["journal"])[indx])
        db["embed"] = list(np.array(db["embed"])[indx])
        utils.save_pickle(DB_PATH, db)
    return db

def search_query():
    try:
        db = utils.load_pickle(DB_PATH)
    except:
        print(f"{FG_COLOR['red']} Database not found. {FG_COLOR['end']}\n")
        exit()
    try:
        usr = utils.load_pickle(USR_SETTINGS)
    except:
        print(f"{FG_COLOR['red']} User settings not found. {FG_COLOR['end']}\n")
        exit()
    
    tkn_corpus = []
    try:
        tkn_corpus = utils.load_pickle(TKN_CORPUS)
        assert len(tkn_corpus) == len(db["url"])
    except:
        for indx in range(len(tkn_corpus), len(db["url"]), 1):
            title = db["title"][indx].lower()
            abstract = utils.filter_abstract(db["abstract"][indx].lower())
            tkn_corpus.append((title + " " + abstract).split(" "))
        utils.save_pickle(TKN_CORPUS, tkn_corpus)
    
    bm25 = BM25Okapi(tkn_corpus)
    while True:
        query = str(input(f"\n{FG_COLOR['red']} Enter Text Query (0 to quit) >> {FG_COLOR['end']}"))
        if query == "0":
            utils.save_pickle(USR_SETTINGS, usr)
            exit()
        else:
            query = query.split(" ")
            top_ind = bm25.get_top_n(query, list(range(len(db["url"]))), MAX_FOUND)
            for i in top_ind:
                if i == top_ind[0]:
                    if len(usr["embed"])<MAX_RECO:
                        usr["embed"].append(db["embed"][i])
                        usr["weights"].append(1)
                    else:
                        sim = 1 - cdist(db["embed"][i], np.concatenate(usr["embed"], axis=0), metric="cosine")[0]
                        indx = np.argpartition(sim, -1)[-1:][0]
                        if sim[indx] > 0.7:
                            usr["embed"][indx] = (db["embed"][i] + usr["embed"][indx])/2
                            usr["weights"][indx] += 1
                        else:
                            if len(usr["temp_embed"])==0:
                                usr["temp_embed"].append(db["embed"][i])
                                usr["temp_weights"].append(1)
                            else:
                                sim = 1 - cdist(db["embed"][i], np.concatenate(usr["temp_embed"], axis=0), metric="cosine")[0]
                                indx = np.argpartition(sim, -1)[-1:][0]
                                if sim[indx] > 0.7:
                                    usr["temp_embed"][indx] = (db["embed"][i] + usr["temp_embed"][indx])/2
                                    usr["temp_weights"][indx] += 1
                                if usr["temp_weights"][indx] > min(usr["weights"]):
                                    smallest_indx = usr["weights"].index(min(usr["weights"]))
                                    usr["embed"][smallest_indx] = usr["temp_embed"][indx]
                                    usr["weights"][smallest_indx] = usr["temp_weights"][indx]
                                    usr["temp_embed"].pop(indx)
                                    usr["temp_weights"].pop(indx)

                print(f"\n{FG_COLOR['green']}{db['title'][i]} - {db['date'][i]} {db['url'][i]}{FG_COLOR['end']}")
                print(f"{FG_COLOR['yellow']}{db['abstract'][i]}{FG_COLOR['green']}")

def set_wallpaper(data):
    wordcloud = WordCloud(
        background_color=BACKGROUND,
        width=WIDTH - 2*MARGIN,
        height=HEIGHT - 2*MARGIN,
        margin=MARGIN,
        min_font_size=MIN_FONT_SIZE,
        prefer_horizontal=0.5
    ).generate_from_frequencies(data)
    wordcloud.to_file("wordcloud.png")
    os.system(f"gsettings set org.gnome.desktop.background picture-uri file://{os.path.dirname(os.path.realpath(__file__))}/wordcloud.png")

def init_user(db):
    tkn_corpus = []
    try:
        tkn_corpus = utils.load_pickle(TKN_CORPUS)
        assert len(tkn_corpus) == len(db["url"])
    except:
        for indx in range(len(tkn_corpus), len(db["url"]), 1):
            title = db["title"][indx].lower()
            abstract = utils.filter_abstract(db["abstract"][indx].lower())
            tkn_corpus.append((title + " " + abstract).split(" "))
        utils.save_pickle(TKN_CORPUS, tkn_corpus)
    bm25 = BM25Okapi(tkn_corpus)

    print(f"\n Enter topics of interests (semi-colon seperated) / leave empty")
    print(f" Example: stable training methods for gans for faster convergence, transformers for long range sequence modelling")
    print(f" IF left empty, recommendations are initialized to recent trending! ")
    
    usr_settings = str(input(f"{FG_COLOR['yellow']} >> {FG_COLOR['end']}"))
    usr = {"embed":[], "titles_now":[], "temp_embed":[], "temp_weights": []}
    if usr_settings != "":
        usr_settings = usr_settings.split(";")
        n_per_pref = MAX_RECO//len(usr_settings)
        for pref in usr_settings:
            top_ind = bm25.get_top_n(pref.split(), list(range(len(db["url"]))), n_per_pref)
            for ind in top_ind:
                usr["embed"].append(db["embed"][ind])
                usr["titles_now"].append(db["title"][ind])
        usr["weights"] = [1 for _ in range(len(usr["embed"]))]
        set_wallpaper(dict(zip(usr["titles_now"], usr["weights"])))
    else:
        recent = utils.get_recent_trending()
        for title in recent:
            try:
                indx = db["title"].index(utils.rem_tex_fmt(title))
                usr["titles_now"].append(title)
                usr["embed"].append(db["embed"][indx])
            except:
                continue
        usr["weights"] = [1 for _ in range(len(usr["embed"]))]
        set_wallpaper(dict(zip(usr["titles_now"], usr["weights"])))
    utils.save_pickle(USR_SETTINGS, usr)

def update_wall(db):
    try:
        usr = utils.load_pickle(USR_SETTINGS)
    except:
        print(f"{FG_COLOR['red']} User settings not found. {FG_COLOR['end']}\n")
        exit()
    num = [math.ceil(i*MAX_RECO) for i in utils.softmax(usr["weights"])]
    title = []
    weights = []
    temp = np.concatenate(db["embed"], axis=0)
    for i in range(len(usr["embed"])):
        sim = 1 - cdist(usr["embed"][i], temp, metric="cosine")[0]
        indx = np.argpartition(sim, -num[i])[-num[i]:]
        for ind in indx:
            title.append(db["title"][ind])
            weights.append(usr["weights"][i])
    usr["titles_now"] = title
    set_wallpaper(dict(zip(usr["titles_now"], weights)))
    utils.save_pickle(USR_SETTINGS, usr)

def get_trending():
    recent = utils.get_recent_trending()
    print(f"\n{FG_COLOR['green']} Recent Hype {FG_COLOR['end']}")
    for title in recent:
        print(f"{FG_COLOR['yellow']} {title} {FG_COLOR['end']}")

def get_links(db):
    try:
        usr = utils.load_pickle(USR_SETTINGS)
    except:
        print(f"{FG_COLOR['red']} User settings not found. {FG_COLOR['end']}\n")
        exit()
    print(f"\n{FG_COLOR['green']} Recommendations for you {FG_COLOR['end']}")
    for title in usr["titles_now"]:
        indx = db["title"].index(title)
        print(f"{FG_COLOR['red']} {title}{FG_COLOR['end']}{FG_COLOR['yellow']} - {db['url'][indx]}{FG_COLOR['end']}")

if __name__ == "__main__":

    # argument parser
    parser = argparse.ArgumentParser(description="oh-my-dl: command line toolkit to keep up with recent trends in DL")
    parser.add_argument("-s", "--setup", action="store_true", help="setup user configuration")
    parser.add_argument("-q", "--query", action="store_true", help="query the database")
    parser.add_argument("-u", "--update", action="store_true", help="update wallpaper")
    parser.add_argument("-t", "--trending", action="store_true", help="get recent trending")
    parser.add_argument("-l", "--links", action="store_true", help="get links for your recommendations")
    args = parser.parse_args()

    if args.setup:
        db = build_db()
        init_user(db)
    
    if args.query:
        search_query()

    if args.update:
        db = build_db()
        update_wall(db)
    
    if args.trending:
        get_trending()
    
    if args.links:
        db = utils.load_pickle(DB_PATH)
        get_links(db)

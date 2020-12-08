import os

"""
all the following parameters can be modified. 
seperating out ones which i think are relevant and ones which are not
"""

# required params

# path to store local database
DB_PATH = f"{os.path.dirname(os.path.realpath(__file__))}/db.pickle"
# initial db file containing papers from 2018
DB_URL = "https://www.dropbox.com/s/kpdooiuvfw507e5/db.pickle?dl=1"
# path to save wordcloud
WORDCLOUD_PATH = f"{os.path.dirname(os.path.realpath(__file__))}/wordcloud.png"
# maximum number of iterations to query arxiv api
MAX_ITER = 10000
# base arxiv URL
BASE_URL = "http://export.arxiv.org/api/query?"
QUERY_FMT = "search_query={}&sortBy=submittedDate&start={}&max_results={}"
# number of results per iteration
RESULTS_PER_ITER = 100
# wait time after every iteration to avoid overload
WAIT_TIME = 5.0
# path to BM25 file 
CACHE_BM25 = f"{os.path.dirname(os.path.realpath(__file__))}/.bm25.pickle"

# user defined parameters

# category selection (refer https://arxiv.org/help/api/user-manual#Subject%20Classifications for more details)
DEF_QUERY = "cat:cs.CV+OR+cat:cs.AI+OR+cat:cs.LG+OR+cat:cs.CL+OR+cat:cs.NE+OR+cat:stat.ML"
# max number of results to disply
MAX_FOUND = 20
# path to download pdf
PDF_DOWNLOAD = f"{os.path.dirname(os.path.realpath(__file__))}/pdfs"
# background color for wordcloud
BACKGROUND = "#101010"
# min font size for the text cloud
MIN_FONT_SIZE = 8
# margin to fit the background into screen
MARGIN = 30
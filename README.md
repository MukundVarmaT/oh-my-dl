# OH-MY-DL

Simple set of python scripts to modify your desktop background to a wordcloud of deep learning papers based on trending research or user specified query.

![](teaser.png)

**Update**

*This branch of the repository focuses on minimal, easy access and does not include the recommendation feature. While its quite fancy and useful to have such a feature, it quite computationally expensive to build embeddings, store them, etc and contradicts the "easy access to deep learning papers" idea. Incase anyone is interested you can checkout this [branch](https://github.com/MukundVarmaT/oh-my-dl/tree/with-reco).*

**Installation**

- `git clone https://github.com/MukundVarmaT/oh-my-dl.git`
- `pip3 install -r requirements.txt`

**Usage**

- `python3 oh-my-dl.py -u` (or) `python3 oh-my-dl.py --update` - fetches recent papers and updates local database. *(In the first usage, a base dataset containing papers from 2018 is downloaded and stored)*
- `python3 oh-my-dl.py -t` (or) `python3 oh-my-dl.py --trending` - Fetch latest trending deep learning papers. *(Based on number of GitHub stars per hour)* 
- `python3 oh-my-dl.py -q <blah-blah; blah-blah; ....>` (or) `python3 oh-my-dl.py --query <blah-blah; blah-blah; ....>` - query local database and update background with top fetched results. *(Each paper is indexed for retrieving info and downloads)*  For example: `python3 ohmydl.py -q "transformers for image recognition; transformers for long range sequence modelling;"`
- `python3 oh-my-dl.py -i <...>` (or) `python3 oh-my-dl.py --info <...>` - retrieve info about paper at a particular index. (authors, journal, official code base (if any), abstract)
- `python3 oh-my-dl.py -d <...>` (or) `python3 oh-my-dl.py --download <...>` - download paper at a particular index to `./pdfs/` *(indices are visible on the background)*

Since I am personally using this utility, I will try to keep it updated. Incase of feature requests and bugs, feel free to open a new issue. 

**Setting up alias**

Add `alias ohmydl="python3 <path to cloned folder>/ohmydl.py $@" ` to your `.bashrc` or `.zshrc`. After adding the alias, all commands which looked like `python3 ohmydl.py blah..blah..` will now become `ohmydl blah..blah..` and can be run from any directory. 

**Auto update using Crontab**

Schedule new job by entering `crontab -e` and add `<frequency> /usr/bin/python3 <path-to-cloned-repo>/ohmydl.py -u > /dev/null 2>&1`. For example, to update every Monday at 1 am `0 1 * * 1 /usr/bin/python3 <path-to-cloned-repo>/ohmydl.py -u > /dev/null 2>&1`.
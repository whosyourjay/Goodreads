import requests
import urllib.request
import time
import re
import calendar
from bs4 import BeautifulSoup
from multiprocessing import Pool

# TODO Grab 1e5 books for first pass sort
# /book/popular_by_date/2008/January
# /book/popular_by_date/1909
# That's 5e4 books
# No missing books found up to /book/show/45413121
# That's 5e7 books

root = "https://www.goodreads.com"
pop_str = "/book/popular_by_date/"
book_str = "/book/show/"

# TODO kill session
#s = requests.session()
#s.config['keep_alive'] = False


def parse_book(book):
    # Get page
    book_url = root + book
    book_response = requests.get(book_url)
    book_soup = BeautifulSoup(book_response.text, 'html.parser')

    # TODO get avg, num ratings
    rating_node = book_soup.select('[itemprop=ratingValue]')
    rating = float(rating_node[0].get_text())

    # Get users reviewing this book
    reviews = book_soup.select('a.user')
    users = [review['href'] for review in reviews]

    # Get users in parallel 
    p = Pool(30)  # Pool tells how many at a time
    avgs = p.map(parse_user, users)
    p.terminate()
    p.join()

    #avgs = [parse_user(user) for user in users]
    avgs = [avg for avg in avgs if avg != None]
    user_avg = sum(avgs)/len(avgs)

    return (rating, user_avg)

def parse_page(list_url):
    print(list_url)
    # Get page
    list_response = requests.get(list_url)
    list_soup = BeautifulSoup(list_response.text, 'html.parser')

    # Get links
    link_nodes = list_soup.select('.bookTitle')
    links = [link['href'][len(book_str):] for link in link_nodes]

    # Get rating info
    # Dangerous this way since it should be aligned with links
    rate_nodes = list_soup.select('.minirating')
    rates = [0]*len(link_nodes)
    for pos, rate in enumerate(rate_nodes):
        text = rate.get_text().replace(',', '').split('rating')
        stars = re.findall("\d+\.\d+", text[0])
        votes = re.findall("\d+", text[1])
        rates[pos] = (float(stars[0]), int(votes[0]))
    
    # Save to file in case we crash
    with open('books.csv', 'a+') as f:
        for pos in range(len(links)):
            stars, votes = rates[pos]
            link = links[pos]
            f.write("%f,%d,%s" % (stars, votes, link) + '\n')

lists = [root + pop_str + str(year) for year in range(1909, 2020)]
# Get books in parallel
p = Pool(30)  # Pool tells how many at a time
avgs = p.map(parse_page, lists)
p.terminate()
p.join()

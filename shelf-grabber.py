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
    reviews = book_soup.select('.user')
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

def parse_list(list_url):
    print(list_url)
    # Get page
    list_response = requests.get(list_url)
    list_soup = BeautifulSoup(list_response.text, 'html.parser')

    # Get links
    link_nodes = list_soup.select('.bookTitle')
    links = [link['href'][len(book_str):] for link in link_nodes]

    # Get rating info
    # Dangerous this way since it should be aligned with links
    rate_nodes = list_soup.select('.greyText')
    rate_nodes = [node for node in rate_nodes if node.get_text().find('avg') > 0]

    rates = [0]*len(link_nodes)
    for pos, rate in enumerate(rate_nodes):
        text = rate.get_text().replace(',', '').split('—')
        stars = re.findall("\d+\.\d+", text[0])
        votes = re.findall("\d+", text[1])
        rates[pos] = (float(stars[0]), int(votes[0]))
    
    # Save to file in case we crash
    with open('books.csv', 'a+') as f:
        for pos in range(len(links)):
            stars, votes = rates[pos]
            link = links[pos]
            # Don't want to save all 2e7 books
            if stars > 4.3 and votes > 20:
                f.write("%f,%d,%s" % (stars, votes, link) + '\n')

def parse_page(page_url):
    print(page_url)
    # Get page
    list_response = requests.get(page_url)
    list_soup = BeautifulSoup(list_response.text, 'html.parser')

    # Get links
    link_nodes = list_soup.select('a')
    links = [link['href'] for link in link_nodes]
    print(len(links))
    print(links)

    page_str = "?page="
    for link in links:
        for page in range(1, 6):
            parse_list(root + link + page_str + str(page))

lists = []
with open('shelves', 'r') as shelves:
    page_str = "?page="
    for line in shelves:
        #for page in range(1, 26):
        page = 1
        lists.append(line.strip() + page_str + str(page))
#for page in lists:
#    parse_list(page)
# Get books in parallel
p = Pool(30)  # Pool tells how many at a time
avgs = p.map(parse_list, lists)
p.terminate()
p.join()

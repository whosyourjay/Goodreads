import requests
import urllib.request
import time
import re
import collections
from bs4 import BeautifulSoup
from multiprocessing import Pool

Book = collections.namedtuple('Book', ['stars', 'votes', 'user_avg', 'user_count'])

books = {}
scores = {}
with open('books.csv', 'r') as book_csv:
    for line in book_csv:
        stars, votes, name = line.strip().split(',')
        books[name] = (float(stars), int(votes))
print(len(books))

# Our model is (5 - stars)/(5 - user_avg) is the true score.
# However, most good scores by this measure will be outliers.
# To build a prior you might look at all books with at least x ratings (say 400)
# Then try to find a fast way to get a posterior from this given the observed
# rating. Instead, we will use the following ad-hoc thing:
# We calculate stars2 which is such that the chance of getting stars or above
# is 1/x. We want x to be something like (# books checked)/position.
# Assuming stars is 5 - p this works out to a quadratic in p.
# p^2 (n^2 + ns^2) - p (2nk + ns^2) + k^2 = 0
# Here s = number of standard deviations (about 4)
# k = n*(5 - stars)
def score(stars, votes, user_avg):
    if votes == 0:
        return 1
    s = 4
    a = votes**2 + s**2 * votes
    b = 2*votes**2 * (5 - stars) + s**2 * votes
    c = votes**2 * (5 - stars)**2
    if b**2 - 4*a*c < 0:
        return 1
    p = (b + (b**2 - 4*a*c)**0.5)/(2*a)
    # Mean user rating is around 3.9
    return p/(5 - user_avg)*1.1

book_list = [(name, books[name][0], books[name][1]) for name in books]
book_list.sort(key=lambda book: score(book[1], book[2], 4))
book_list = book_list[:2000]

book_count = 0
all_users = {}

user_checked = {}
with open('data.csv', 'r') as data_csv:
    for line in data_csv:
        stars, votes, user_avg, user_count, users, name = line.strip().split(',')
        user_checked[name] = Book(
                float(stars), int(votes), float(user_avg), int(user_count))

checked_list = [(name, params) for name, params in user_checked.items()]
checked_list.sort(key=lambda pair:
        score(pair[1].stars, pair[1].votes, pair[1].user_avg))

for pair in checked_list[:100]:
    name, book = pair
    print("%f %s" % (score(book.stars, book.votes, book.user_avg), name))


root = "https://www.goodreads.com"
book_str = "/book/show/"
user_str = "/user/show/"
lst = "10198"

def parse_user(user):
    # Save a little work with a memo
    global all_users
    if user in all_users:
        return all_users[user]

    # Get page
    user_url = root + user_str + user
    user_response = requests.get(user_url)
    user_soup = BeautifulSoup(user_response.text, 'html.parser')

    # This must handle
    # public - /user/show/42390
    # private - /user/show/564646
    # author - /user/show/167451
    refs = user_soup.select('a')

    # Pick the link with text "avg"
    for ref in refs:
        text = ref.get_text()
        if text.find('avg') >= 0:
            # Extract float
            num = re.findall("\d+\.\d+", text)
            avg = float(num[0])
            all_users[user] = avg
            # Careful if a user with no ratings writes a non-rating review
            if avg < 1:
                all_users[user] = None
                return None
            with open('users.csv', 'a+') as user_csv:
                user_csv.write("%.2f,%s" % (avg, user) + '\n')
            return avg
    return None
                

# TODO kill session
#s = requests.session()
#s.config['keep_alive'] = False


def parse_book(book):
    name, stars, votes = book

    global user_checked
    if name in user_checked:
        return
    # Get page
    book_url = root + book_str + name
    book_response = requests.get(book_url)
    book_soup = BeautifulSoup(book_response.text, 'html.parser')

    # TODO get avg, num ratings
    #rating_node = book_soup.select('[itemprop=ratingValue]')
    #rating = float(rating_node[0].get_text())

    # Get users reviewing this book
    reviews = book_soup.select('a.user')
    users = [review['href'] for review in reviews]
    for pos, user in enumerate(users):
        num = re.findall("\d+", user)
        users[pos] = num[0]

    # Get users in parallel 
    p = Pool(30)  # Pool tells how many at a time
    avgs = p.map(parse_user, users)
    p.terminate()
    p.join()

    #avgs = [parse_user(user) for user in users]
    avgs = [avg for avg in avgs if avg != None]
    user_avg = sum(avgs)/len(avgs)

    # Write this down in case we fail
    with open('data.csv', 'a+') as data_csv:
        data_csv.write("%.2f,%d,%f,%d,%s,%s"
                % (stars, votes, user_avg, len(users), ' '.join(users), name)
                + '\n')
    scores[name] = score(stars, votes, user_avg)
    print("%f %s" % (scores[name], name))


#for book in book_list:
#    parse_book(book)
#p = Pool(30)  # Pool tells how many at a time
#p.map(parse_book, book_list)
#p.terminate()
#p.join()

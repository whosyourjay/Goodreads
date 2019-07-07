books = {}
with open('books.csv', 'r') as f:
    for line in f:
        stars, votes, name = line.split(',')
        books[name] = (float(stars), int(votes))
print(len(books))

def score(book):
    if book[2] == 0:
        return 0
    return book[1] - 2/book[2]**0.5

book_list = [(name, books[name][0], books[name][1]) for name in books]
book_list.sort(key=lambda book: score(book))

print('\n'.join(map(str, book_list[-100:])))

# TODO resolve dupes
# Set of reviewers visible on the page should be enough
# If I can get redirect info that's better

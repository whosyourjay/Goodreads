# Goodreads
To get the best books run
```
python book-list.py
python goodreads.py
```

Wait 10 seconds per candidate book evaluated. On subsequent runs, just do
```
python goodreads.py
```

`books.csv` contains easy-to-grab info like name, rating, and number of voters. `data.csv` contains more info. On rerun `goodreads.py` will use cached info.

Edit `lists` in `book-list.py` if you just want the best of a specific list.

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

books.csv contains easy-to-grab info like name, rating, and number of voters. Data.csv contains more info. On rerun `goodreads.py` will use cached info.

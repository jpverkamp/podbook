# podbook
Generate podcasts from audiobooks

Expected directory structure:
- `./books/book.yml`
- `./books/*.mp3`

`book.yml` should contain at least `title` and `author` (for now). 

mp3 files will be returned in order, using the filename as the chapter title.

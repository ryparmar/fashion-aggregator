# Scrapers for second hand shops



### Running scrapers at given time
https://phoenixnap.com/kb/linux-at-command
at now +5 hours  # ctrl+d to save the job

cd /home/spaceape/projects/fashion-aggregator/scraper/fashion

scrapy crawl unimoda -a category=damske -o data/damske.jsonl --logfile damske.log --loglevel INFO -s JOBDIR=crawls/unimoda-damske | at now +5 hours

scrapy crawl unimoda -a category=panske -o data/panske.jsonl --logfile panske.log --loglevel INFO -s JOBDIR=crawls/unimoda-panske | at now +9 hours
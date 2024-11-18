import threading
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import pymongo
from queue import Queue
import time

# MongoDB setup
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["crawler"]
collection = db["pages"]

# Target URL to find
target_heading = '<h1 class="cpp-h1">Permanent Faculty</h1>'
target_url = "https://www.cpp.edu/sci/computer-science/faculty-and-staff/permanent-faculty.shtml"

# Frontier queue
frontier = Queue()
visited = set()

# Mutex for synchronization
visited_lock = threading.Lock()

# Start URL
start_url = "https://www.cpp.edu/sci/computer-science/"

# Helper function to check if a URL is valid for crawling
def is_valid_url(url):
    return url.endswith(('.html', '.shtml')) and url not in visited

# Function to retrieve HTML content of a page
def retrieve_html(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        else:
            print(f"Failed to retrieve {url}")
            return None
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

# Function to parse the HTML and check for the target page
def parse_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    body = str(soup.find('body'))
    return target_heading in body

# Function to store page content in MongoDB
def store_page(url, html):
    collection.insert_one({"url": url, "html": html})

# Function to add a URL to the frontier if not already visited
def add_to_frontier(url):
    with visited_lock:
        if url not in visited:
            visited.add(url)
            frontier.put(url)

# Threaded crawler function
def crawler_thread():
    while True:
        # Wait until there is a URL in the frontier
        url = frontier.get()
        if url is None:
            break  # Exit the thread if there are no more URLs to process

        # Retrieve the HTML content of the URL
        print(f"Processing: {url}")
        html = retrieve_html(url)

        if html:
            # Store the page's HTML content in MongoDB
            store_page(url, html)

            # Check if we have found the target page
            if parse_html(html):
                print(f"Target page found: {url}")
                # Here you could signal the crawler to stop, or just flag this page
                frontier.queue.clear()  # Clear the frontier to stop the crawler

            # Parse the HTML to find all links and add them to the frontier
            soup = BeautifulSoup(html, 'html.parser')
            links = soup.find_all('a', href=True)
            for link in links:
                link_url = link['href']
                full_url = urljoin(url, link_url)  # Resolve relative URLs
                if is_valid_url(full_url):
                    add_to_frontier(full_url)

        # Indicate that the URL has been processed
        frontier.task_done()

# Initialize the frontier with the starting URL
frontier.put(start_url)

# Number of threads to use
num_threads = 5

# Start the crawler threads
threads = []
for i in range(num_threads):
    thread = threading.Thread(target=crawler_thread)
    thread.start()
    threads.append(thread)

# Wait for all threads to finish
frontier.join()

# Terminate threads
for i in range(num_threads):
    frontier.put(None)  # Send the signal to stop each thread

for thread in threads:
    thread.join()

print("Crawling finished.")
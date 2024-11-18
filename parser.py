import pymongo
from bs4 import BeautifulSoup
import re

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["crawler"] 
pages_collection = db["pages"]
professors_collection = db["professors"]

target_url = "https://www.cpp.edu/sci/computer-science/faculty-and-staff/permanent-faculty.shtml"

page_data = pages_collection.find_one({"url": target_url})

if not page_data:
    print(f"Permanent Faculty page not found in the database. Exiting.")
else:
    soup = BeautifulSoup(page_data['html'], 'html.parser')

    faculty_list = soup.find_all('div', class_='faculty-member')

    for faculty in faculty_list:
        name = faculty.find('h3').get_text(strip=True) if faculty.find('h3') else 'N/A'
        title = faculty.find('p', class_='title').get_text(strip=True) if faculty.find('p', class_='title') else 'N/A'
        office = faculty.find('p', class_='office').get_text(strip=True) if faculty.find('p', class_='office') else 'N/A'
        phone = faculty.find('p', class_='phone').get_text(strip=True) if faculty.find('p', class_='phone') else 'N/A'
        email = faculty.find('p', class_='email').get_text(strip=True) if faculty.find('p', class_='email') else 'N/A'
        website = faculty.find('a', href=True)['href'] if faculty.find('a', href=True) else 'N/A'

        phone = re.sub(r'\s+', ' ', phone) 
        email = re.sub(r'\s+', ' ', email) 

        professor_data = {
            "name": name,
            "title": title,
            "office": office,
            "phone": phone,
            "email": email,
            "website": website
        }

        professors_collection.insert_one(professor_data)
        print(f"Inserted professor: {name}")

    print("Faculty parsing complete.")
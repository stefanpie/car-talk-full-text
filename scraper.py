import shutil
import sqlite3
from pathlib import Path

import requests
import tqdm
from bs4 import BeautifulSoup
from joblib import Parallel, delayed

URL_BASE = "https://www.cartalk.com"
URL_PUZZLERS = "https://www.cartalk.com/radio/puzzler/"
URL_LETTERS = "https://www.cartalk.com/radio/letter/"
URL_SHOWS = "https://www.cartalk.com/radio/show/"
URL_STAFF = "https://www.cartalk.com/content/staff-credits"

HEADER = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0"
    )
}


def scrape_staff():
    print("Scraping staff...")
    response = requests.get(
        URL_STAFF,
        headers=HEADER,
    )
    html = response.text
    soup = BeautifulSoup(html, "html.parser")

    table = soup.select_one(
        ".node-cartalk-content > section > div > div > div > div > center > table"
    )

    staff = []
    for row in table.find_all("tr"):
        if "Car Talk's Official Staff Credits" in row.text:
            continue
        position = row.find("td").text.strip().replace("\n", "")
        name = row.find("td").find_next("td").text.strip().replace("\n", "")
        staff.append({"position": position, "name": name})
    return staff


def get_single_puzzle(link):
    response = requests.get(
        URL_BASE + link["href"],
        headers=HEADER,
    )
    html = response.text
    soup = BeautifulSoup(html, "html.parser")

    title = soup.select_one("h1").text.strip().replace("\n", "")
    date = soup.select_one("article").select_one(".date-display-single").text.strip()

    main_text = soup.select_one("article")
    for ul in main_text.select(".fa-ul"):
        ul.extract()
    for media in main_text.select(".media"):
        media.extract()
    main_text = main_text.text.strip()

    return {
        "title": title,
        "date": date,
        "main_text": main_text,
    }


def scrape_puzzlers(n_jobs=1, n_max=None):
    print("Scraping puzzlers...")
    response = requests.get(
        URL_PUZZLERS,
        headers=HEADER,
    )
    html = response.text
    soup = BeautifulSoup(html, "html.parser")

    links = soup.select("#block-system-main a")
    links = [link for link in links if "/radio/puzzler/" in link["href"]]

    if n_max is not None and n_max < len(links):
        links = links[:n_max]

    puzzlers = Parallel(n_jobs=n_jobs, backend="threading")(
        delayed(get_single_puzzle)(link) for link in tqdm.tqdm(links)
    )

    return puzzlers


def get_single_letter(link):
    response = requests.get(
        URL_BASE + link["href"],
        headers=HEADER,
    )
    html = response.text
    soup = BeautifulSoup(html, "html.parser")

    title = soup.select_one("h1").text.strip().replace("\n", "")

    main_text_s = soup.select_one("#block-system-main")
    for p in main_text_s.select("p"):
        if p.select("a[href='../content/read-car-talk']"):
            p.extract()
    main_text = main_text_s.text.strip()

    return {
        "title": title,
        "main_text": main_text,
    }


def scrape_letters(n_jobs=1, n_max=None):
    print("Scraping letters...")
    response = requests.get(
        URL_LETTERS,
        headers=HEADER,
    )
    html = response.text
    soup = BeautifulSoup(html, "html.parser")

    links = soup.select("#block-system-main a")
    links = [link for link in links if "/radio/letter/" in link["href"]]

    if n_max is not None and n_max < len(links):
        links = links[:n_max]

    letters = Parallel(n_jobs=n_jobs, backend="threading")(
        delayed(get_single_letter)(link) for link in tqdm.tqdm(links)
    )

    return letters


if __name__ == "__main__":
    N_JOBS = -1

    db_fp = Path("cartalk.db")
    if db_fp.exists():
        db_fp.unlink()

    db = sqlite3.connect(db_fp)

    staff = scrape_staff()
    db.execute("""
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            position TEXT,
            name TEXT
        )
        """)
    db.commit()
    for person in staff:
        db.execute(
            """
            INSERT INTO staff (position, name)
            VALUES (?, ?)
            """,
            (person["position"], person["name"]),
        )
    db.commit()

    puzzlers = scrape_puzzlers(n_jobs=N_JOBS, n_max=None)
    db.execute("""
        CREATE TABLE IF NOT EXISTS puzzlers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            date TEXT,
            main_text TEXT
        )
        """)
    db.commit()
    for puzzler in puzzlers:
        db.execute(
            """
            INSERT INTO puzzlers (title, date, main_text)
            VALUES (?, ?, ?)
            """,
            (puzzler["title"], puzzler["date"], puzzler["main_text"]),
        )
    db.commit()

    letters = scrape_letters(n_jobs=N_JOBS, n_max=None)
    db.execute("""
        CREATE TABLE IF NOT EXISTS letters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            main_text TEXT
        )
        """)
    db.commit()
    for letter in letters:
        db.execute(
            """
            INSERT INTO letters (title, main_text)
            VALUES (?, ?)
            """,
            (letter["title"], letter["main_text"]),
        )
    db.commit()

    db.close()

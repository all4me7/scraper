from flask import Flask, render_template, request
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from requests.exceptions import ConnectionError
import requests as req
import httpx
import asyncio
import webbrowser


app = Flask(__name__)


async def status_check(list_to_scrape, list_for_dead_links):
    async with httpx.AsyncClient() as client:
        for link in list_to_scrape:
            try:
                response = await client.get(link)
            except Exception as err:
                list_for_dead_links.append(str(link))
                print(err)
            if response.status_code == 404:
                list_for_dead_links.append(str(link))
            else:
                continue

async def status_check_v2(list_to_scrape, list_for_dead_links, prot, dom):
    async with httpx.AsyncClient() as client:
        for link in list_to_scrape:
            if link.startswith("/"):
                link = prot + dom + link
            try:
                response = await client.get(link)
            except Exception as err:
                list_for_dead_links.append(str(link))
                print(err)
            if response.status_code == 404:
                list_for_dead_links.append(str(link))
            else:
                continue

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/', methods=['GET', 'POST'])
def main():
    # VARIABLES
    results_list = []
    hyperlinks = []
    dead_links = []
    PROTOCOL = "https://"

    # GET VALUES FROM HTML
    if request.method == 'POST':
        if 'approve' in request.form:
            url = request.form['url']
            tag = request.form['tag']
            atr = request.form['attribute']
            val = request.form['value']

            # FIXING URL'S
            if url.startswith(PROTOCOL) is not True:
                url = PROTOCOL + url

            domain_name = urlparse(url).netloc

            # SOUP SETUP
            try:
                response = req.get(url)
            except ConnectionError:
                return render_template("index.html")

            soup = BeautifulSoup(response.content, 'html.parser')

            # SCRAPING SITE
            if len(url) != 0 and len(tag) == 0 and len(atr) == 0 and len(val) == 0:
                    final = []
                    all_elements = [x for x in soup.find_all(True)]
                    src_list = [x.get("src") for x in all_elements if x.get("src") != None]
                    data_src_list = [x.get("data-src") for x in all_elements if x.get("data-src") != None]
                    href_list = [x.get("href") for x in all_elements if x.get("href") != None]
                    added_lists = list(set(src_list + data_src_list + href_list))
                    filtered = [x for x in added_lists if str(x).startswith("/") or str(x).startswith("http")]
                    for i in filtered:
                        if i.startswith("/"):
                            i = f"https://{domain_name}{i}"
                        final.append(i)
                    asyncio.run(status_check(final, dead_links))

            # SCRAPING TAG
            elif len(url) != 0 and len(tag) != 0 and len(atr) == 0 and len(val) == 0:
                if tag.endswith('@'):
                    tag = tag.removesuffix('@')
                    scraped_tags = soup.find_all(tag)
                    for single_tag in scraped_tags:
                        results_list.append(single_tag.text)
                else:
                    scraped_tags = soup.find_all(tag)
                    for single_tag in scraped_tags:
                        results_list.append(single_tag)

            #SCRAPING  ATTRIBUTE
            elif len(url) != 0 and len(tag) != 0 and len(atr) != 0 and len(val) == 0:
                if atr.endswith('$'):
                    atr = atr.removesuffix('$')
                    scraped_tags = soup.find_all(tag, attrs={atr: True})
                    for single_tag in scraped_tags:
                        results_list.append(single_tag[atr])
                elif atr.endswith('#'):
                    atr = atr.removesuffix('#')
                    scraped_tags = [x[atr] for x in soup.find_all(tag, attrs={atr: True})]
                    filtered_content = [x.strip() for x in scraped_tags if str(x).startswith("http") or str(x).startswith("/")]
                    filtered_content = list(set(filtered_content))
                    for link in filtered_content:
                        if link.startswith("/"):
                            link = PROTOCOL + domain_name + link
                            hyperlinks.append(link)
                        else:
                            hyperlinks.append(link)
                elif atr.endswith('!'):
                    atr = atr.removesuffix('!')
                    scraped_tags = [x[atr] for x in soup.find_all(tag, attrs={atr: True})]
                    filtered_content = [x.strip() for x in scraped_tags if str(x).startswith("http") or str(x).startswith("/")]
                    filtered_content = list(set(filtered_content))
                    asyncio.run(status_check_v2(filtered_content, dead_links, PROTOCOL, domain_name))
                elif atr.endswith('@'):
                    atr = atr.removesuffix('@')
                    scraped_tags = soup.find_all(tag, attrs={atr: True})
                    for single_tag in scraped_tags:
                        results_list.append(single_tag.text)
                else:
                    scraped_tags = soup.find_all(tag, attrs={atr: True})
                    for single_tag in scraped_tags:
                        results_list.append(single_tag)

            # SCRAPING ATTRIBUTE VALUE
            elif len(url) != 0 and len(tag) != 0 and len(atr) != 0 and len(val) != 0:
                if val.endswith('@'):
                    val = val.removesuffix('@')
                    scraped_tags = soup.find_all(tag, attrs={atr: val})
                    for single_tag in scraped_tags:
                        results_list.append(single_tag.text)
                else:
                    scraped_tags = soup.find_all(tag, attrs={atr: val})
                    for single_tag in scraped_tags:
                        results_list.append(single_tag)
            else:
                pass

        # USED TAGS/ATTRIBUTES/VALUES LABEL
        used_tags = f'{tag} {atr} {val}'

    return render_template(
        'index.html',
        url = url,
        results_list = results_list,
        used_tags = used_tags,
        dead_links = dead_links,
        hyperlinks = hyperlinks
        )


if __name__ == '__main__':
    webbrowser.open("http://127.0.0.1:5000")
    app.run()

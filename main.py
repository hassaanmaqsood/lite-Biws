import requests
from bs4 import BeautifulSoup

searchKeywords = ["daa+simple+and+functional", "daa+systems"] #keywords to search
usedKeywords =[] #output of keywords
baseurl = "https://google.com/search?q="
fetchURL = []
for keywords in searchKeywords:
  fetchURL.append(baseurl+keywords)

# Fetch urls itertatively and find keywords
for url in fetchURL:
  page = requests.get(url)
  soup = BeautifulSoup(page.content, 'html.parser')

  outboundsLinks = []
  links = soup.select('a')

  for elem in links:
    #print(elem.get('href')[0:7])
    if elem.get('href')[0:7] == "/url?q=":
      outboundsLinks.append(elem.get('href')[7:])

  for links in range(len(outboundsLinks)):
    outboundsLinks[links-1]=outboundsLinks[links-1][0:(outboundsLinks[links-1].find("&sa="))]

  relatedMetaKeywords = []
  for link in outboundsLinks:
    #try:
    page = requests.get(link)
    soup = BeautifulSoup(page.content, 'html.parser')
    #get all keywords
    metaKeywords = soup.select('[name="keywords"]')
    for elem in metaKeywords:
      usedKeywords.append(elem.get('content'))
    relatedMetaKeywords.append(metaKeywords)
    #except:
      #print("Link Broken")

  #print("here are meta tags selected")
  #for tags in relatedMetaKeywords:
    #print(tags)

print(usedKeywords)

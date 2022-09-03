import requests
import json
from bs4 import BeautifulSoup

#iterate over the array to create a permutation set
#it does not include set with all the keywords
def perKeywords(A,sub,char):
  for k in A:
    temp = A.copy()
    temp.remove(k)
    conc = ""
    for i in range(len(temp)):
      conc=conc+char+temp[i]
    conc=conc[1:]
    if len(conc)>=1:
      if conc not in sub:
        sub.append(conc)
        perKeywords(temp,sub,char)
    elif len(conc)>1:
      sub.append(conc)
      return sub

searchKeywords = [] #keywords to search
querryChar = "+"
basicKeywords = ["daa","system","simple","functional"]
perKeywords(basicKeywords, searchKeywords, querryChar)
usedKeywords =[] #output of keywords
baseurl = "https://google.com/search?q="
fetchURL = []
for keywords in searchKeywords:
  fetchURL.append(baseurl+keywords)
allURLs=[] #URL to export
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
  allURLs.append(outboundsLinks)
  relatedMetaKeywords = []
  for link in outboundsLinks:
    try:
      print(link)
      page = requests.get(link)
      soup = BeautifulSoup(page.content, 'html.parser')
      #get all keywords
      metaKeywords = soup.select('[name="keywords"]')
      for elem in metaKeywords:
        usedKeywords.append(elem.get('content'))
      relatedMetaKeywords.append(metaKeywords)
    except:
      print("Link Broken")
      pass

#stuff we required that's websites that ranked on first page and thier URLs
LinkKey ={ 
    "links": allURLs, 
    "keywords": usedKeywords 
} 
    
# the json file where the output must be stored 
export_file = open("LinksKeys-liteBiws.json", "w") 
json.dump(LinkKey, export_file, indent = 3)
export_file.close() 

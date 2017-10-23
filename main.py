import bs4
import urllib3
import pprint
import re


steam_special_url = "http://store.steampowered.com/search/?specials="
http = urllib3.PoolManager()






def get_number_pages():
    first_page = http.request("GET", steam_special_url + str(1))
    html_soup = bs4.BeautifulSoup(first_page.data, 'html.parser')

    result = html_soup.find_all("div", { "class" : "search_pagination_right" })
    result = str(result)

    searchstring = 'page='
    pagelist =[m.start() for m in re.finditer( searchstring, result)]

    # it assumes that the 2nd to last result is the total number of pages
    index = pagelist[len(pagelist) - 2] + len(searchstring)
    # this code
    a = 0
    page_number = ""
    while(result[index+a] != "\""):
        page_number += result[index+a]
        a+=1

    return int(page_number)

def get_pages():

    pages = []
    for i in range(1, get_number_pages() + 1):
        pages.append( bs4.BeautifulSoup(
            http.request("GET", steam_special_url + str(i)).data , 'html.parser'))

    return pages

def get_testpage():

    testpage = bs4.BeautifulSoup(
        http.request("GET", steam_special_url + str(2)).data, 'html.parser')
    return [testpage]

def main():
    steam_resuts = []
    pages = get_testpage()
    for page in pages:
        i = page.find_all("a", {"class": "search_result_row"})
        for result in i:
            steam_resuts.append(result)
    print(steam_resuts[0].prettify())


#ds_collapse app_impression_tracked


if __name__ == '__main__':
    main()


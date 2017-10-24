import difflib

import bs4
import os

import time
import urllib3
import pprint
import re


steam_special_url_fistpage = "http://store.steampowered.com/search/?specials=1"
and_page = "&page="
http = urllib3.PoolManager()
ROOTDIR = os.path.dirname(os.path.realpath(__file__))

def get_number_pages():
    first_page = http.request("GET", steam_special_url_fistpage)
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
    pages.append( bs4.BeautifulSoup(
        http.request("GET", steam_special_url_fistpage).data , 'html.parser'))
    num_pages = get_number_pages()
    for i in range(2, num_pages + 1):
        pages.append( bs4.BeautifulSoup(
            http.request("GET", steam_special_url_fistpage + and_page + str(i)).data, 'html.parser'))
        print("got page "+ str(i) + "/" + str(num_pages))

    return pages


def get_testpages():

    testpage = bs4.BeautifulSoup(
        http.request("GET", steam_special_url_fistpage).data, 'html.parser')
    #time.sleep(5)
    testpage2 = bs4.BeautifulSoup(
        http.request("GET", steam_special_url_fistpage + "&page=2").data, 'html.parser')

    # with open(ROOTDIR + "\\" + "test.txt", 'w') as outfile:
    #     outfile.write(str(testpage.prettify().encode()))
    #     outfile.write("|END|")
    #     outfile.write(str(testpage2.prettify().encode()))

    return [testpage, testpage2]


def get_result_list(pages):
    results = []
    for page in pages:
        i = page.find_all("a", {"class": "search_result_row"})
        for result in i:
            results.append(result)
        i.clear()
    return results


def get_discount_percents(results_list):
    discount_percents = []
    for r in results_list:
        string = str(r.find("div", {"class": "col search_discount responsive_secondrow"}))
        span = "<span>"
        #for some fucking reason not all results have a discount number
        if string.find(span) != -1:
            # the +1 and -1 are to cut off the - and the %
            start = string.find(span) + len(span) + 1
            end = string.find("</span>") - 1
            discount_percents.append(int(string[start:end]))
        else:
            discount_percents.append(0)
    return discount_percents

def get_titles_list(results_list):
    titles = []
    for result in results_list:
        titles.append( str(result.find("span", {"class": "title"}).string))
    return titles

def main():
    pages = get_testpages()
    #pages = get_pages()
    results_list = get_result_list(pages)
    titles = get_titles_list(results_list)
    percents_list = get_discount_percents(results_list)

    filter_results = []

    for i in range(0, len(titles)):
        filter_results.append([percents_list[i], titles[i]])

    filter_results.sort( key= lambda p: p[0], reverse=True)

    #for row in filter_results:
    #    print(str(row[0]) + " " + row[1] + "\n")
    # todo there are bugs with unicode encoding. should make a method where it encodes the text and then filters out the tm and c's
    # todo slice results so that only item with >30 discount are shown
    # todo add urls to results
    with open(ROOTDIR + "\\" + "sales.txt", 'w') as outfile:
        for row in filter_results:
            outfile.write(str(row[0]) + " " + str(row[1].encode('utf-8'))[2: len(str(row[1].encode('utf-8'))) -1] + "\n")

    print("done")



if __name__ == '__main__':
    main()
    #get_testpages()

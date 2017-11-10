import bs4
import os

import time

import sys
import urllib3
import pprint
import re
from appJar import gui
from utils import ROOTDIR, listmerger, log, log_return, ints_str
from utils import dir_sep as dirsep


steam_special_url_fistpage = "http://store.steampowered.com/search/?specials=1"
and_page = "&page="
http = urllib3.PoolManager()

html_file = "test.html"

def get_number_pages():
    first_page = http.request("GET", steam_special_url_fistpage)
    html_soup = bs4.BeautifulSoup(first_page.data, 'html.parser')

    result = html_soup.find_all("div", { "class" : "search_pagination_right" })
    result = str(result)

    searchstring = 'page='
    pagelist =[m.start() for m in re.finditer(searchstring, result)]

    # it assumes that the 2nd to last result is the total number of pages
    index = pagelist[len(pagelist) - 2] + len(searchstring)
    # this code
    i = 0
    page_number = ""
    while result[index+i] != "\"":
        page_number += result[index+i]
        i += 1

    return int(page_number)


def get_pages():
    results = []
    page = bs4.BeautifulSoup( http.request("GET", steam_special_url_fistpage).data , 'html.parser')
    results = get_results_from_page( page, results)
    num_pages = get_number_pages()
    for i in range(2, num_pages + 1):
        results = get_results_from_page(
            bs4.BeautifulSoup(http.request("GET", steam_special_url_fistpage + and_page + str(i)).data, 'html.parser'), results)
        log("got page "+ str(i) + "/" + str(num_pages))

    return results

def get_results_from_page(page, result_list):
    i = page.find_all("a", {"class": "search_result_row"})
    for result in i:
        result_list.append(result)
    return result_list

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

    return get_result_list([testpage, testpage2])


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
        titles.append(str(result.find("span", {"class": "title"}).string))
    return titles



def slice_results(results, minimum_discount, percents_index):
    before = len(results)
    for i in range(0, len(results)):
        if results[i][percents_index] < minimum_discount:
            break
    results = results[:i]
    log(str(len(results)) + " out of " + str(before) + " had good enough reviews")
    return results


def create_html(filtered_results):
    page = bs4.BeautifulSoup(http.request("GET", steam_special_url_fistpage).data, 'html.parser')
    tag = page.find("div", {"id": "search_result_container"})
    tag.clear()
    for result in filtered_results:
        tag.append(result[1])

    with open(ROOTDIR + dirsep + "results.html", 'w', encoding="utf-8") as outfile:
        outfile.write(str(page))

def get_user_reviews(results):
    # returns 2 lists
    # the first list is how many user reviews the result got
    # the second list is what percentage was positive
    n_user_reviews = []
    percent_reviews_positive = []
    found = 0
    log("scraping reviews")
    for result in results:
        var = result.find("span", {"class": "search_review_summary"})
        if not isinstance(var, type(None)):# if true it contains a review
            var = str(var)
            of_the_str = "% of the "
            of_the_start = var.find(of_the_str)
            of_the_end = of_the_start + len(of_the_str)
            # this part checks how many of the reviews where positive
            percent_positive_as_str = ""
            for char in var[of_the_start - 3:of_the_start]:# 3 is because a max of 3 digets
                if char in ints_str:
                    percent_positive_as_str += char

            percent_reviews_positive.append(int(percent_positive_as_str))

            # this part get how many reviews it got
            temp_n_reviews = ""
            for char in var[of_the_end:]:
                if char == " ":
                    break
                else:
                    if not char == "," and not char == ".":
                        temp_n_reviews += char
            #print("reviews " + temp_n_reviews)
            n_user_reviews.append(int(temp_n_reviews))

            found += 1
        else:
            n_user_reviews.append(0)
            percent_reviews_positive.append(0)
    log(str(found) + " out of " + str(len(results)) + " had reviews")
    return n_user_reviews, percent_reviews_positive


def ger_good_games(merged_results, min_reviews, min_positive, n_rev_idx, min_positive_idx):
    ret = []
    for result in merged_results:
        if result[n_rev_idx] >= min_reviews and result[min_positive_idx] >= min_positive:
            ret.append(result)
    return ret

def run(threads):
    # todo make gui
    # todo add chache system
    # todo redesign app so the bs4 object are in memory for as short as possible
    # find the search result container
    # clear it's contents and dump in the results
    test = False
    if test:
        results_list = get_testpages()
    else:
        results_list = get_pages()

    n_user_reviews, percent_reviews_positive = get_user_reviews(results_list)
    #titles = get_titles_list(results_list)
    percents_list = get_discount_percents(results_list)

    # todo
    filter_results = listmerger([percents_list, results_list, n_user_reviews, percent_reviews_positive])
    filter_results.sort( key= lambda p: p[0], reverse=True)
    filter_results = slice_results(filter_results, 40, 0)
    filter_results = ger_good_games(filter_results, 100, 75, 2, 3)

    create_html(filter_results)


    # this part is deprecated
    #for row in filter_results:
    #    print(str(row[0]) + " " + row[1] + "\n")
    # with open(ROOTDIR + dirsep + "sales.txt", 'w', encoding="utf-8") as outfile:
    #     for row in filter_results:
    #         outfile.write(str(row[0]) + " " + str(row[1].encode('utf-8'))[2: len(str(row[1].encode('utf-8'))) -1] + "\n")#remove unicode encoding before use

    print("done")
class Gui:
    app = gui("Login Form")

    def init_start_scr(self):
        app = self.app
        app.addLabel("userLab", "Username:", 0, 0)
        app.addEntry("userEnt", 0, 1)
        app.setFocus("userEnt")
        app.addLabel("passLab", "Password:", 1, 0)
        app.addSecretEntry("passEnt", 1, 1)
        app.addButtons(["Submit", "Cancel"], self.press, colspan=2)

    def init_loading_scr(self):
        app = self.app

    def init_settings(self):
        app = self.app
        app.setGeom(300, 225)
        app.setResizable(canResize=False)
        app.enableEnter(self.press)


    def open(self):
        self.init_settings()
        self.init_start_scr()
        self.app.go()

    def press(self, btnName):
        app = self.app
        if btnName == "Cancel":
            app.stop()

        if app.getEntry("userEnt") == "rjarvis":
            if app.getEntry("passEnt") == "abc":
                app.infoBox("Success", "Congratulations, you are logged in!")
        else:
            app.errorBox("Failed login", "Invalid username or password")

# todo add gui
# todo add filters to filter out fake games
# todo count duplicates to see if there's somthing i can do about it

if __name__ == '__main__':
    #ui = Gui()
    #ui.open()
    run(1)

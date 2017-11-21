import bs4
import os

import time
import csv
import sys
import urllib3
import pprint
import re
from appJar import gui
from utils import ROOTDIR, listmerger, log, log_return, ints_str, get_methods_form_claas
from utils import dir_sep as dirsep

steam_special_url_firstpage = "http://store.steampowered.com/search/?specials=1"
and_page = "&page="
http = urllib3.PoolManager()

html_file = "test.html"


class Data_Sraping:
    # every methode in this class will be applied to the the results
    # they all must take the list of results as an argument and add a list to the dict in this object and have no return
    # a list in which each result lines up with a result from the argument
    # like this ["review_scores": [list of review scores]]
    scraped_dict = dict

    scraped_dict['n_user_reviews'] = []
    scraped_dict['percent_reviews_positive'] = []  # todo refactor these back into the methods

    def get_user_reviews(self, results):
        # returns 2 lists
        # the first list is how many user reviews the result got
        # the second list is what percentage was positive
        n_user_reviews = []
        percent_reviews_positive = []
        found = 0
        log("scraping reviews")
        for result in results:
            var = result.find("span", {"class": "search_review_summary"})
            if not isinstance(var, type(None)):  # if true it contains a review
                var = str(var)
                of_the_str = "% of the "
                of_the_start = var.find(of_the_str)
                of_the_end = of_the_start + len(of_the_str)
                # this part checks how many of the reviews where positive
                percent_positive_as_str = ""
                for char in var[of_the_start - 3:of_the_start]:  # 3 is because a max of 3 digets
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
                # print("reviews " + temp_n_reviews)
                n_user_reviews.append(int(temp_n_reviews))

                found += 1
            else:
                n_user_reviews.append(0)
                percent_reviews_positive.append(0)
        log(str(found) + " out of " + str(len(results)) + " had reviews")
        for i in range(len(n_user_reviews)):
            self.scraped_dict['n_user_reviews'].append(n_user_reviews[i])
            self.scraped_dict['percent_reviews_positive'].append(percent_reviews_positive[i])

        class helper_methods:  # helper methods for Data_Scraping in seperate class so they won't be applied to data
            def test(self):
                pass

    scraped_dict["discount_percents"] = []  # todo refactor these back into method

    def get_discount_percents(self, results_list):
        discount_percents = []
        for r in results_list:
            string = str(r.find("div", {"class": "col search_discount responsive_secondrow"}))
            span = "<span>"
            # for some fucking reason not all results have a discount number
            if string.find(span) != -1:
                # the +1 and -1 are to cut off the - and the %
                start = string.find(span) + len(span) + 1
                end = string.find("</span>") - 1
                discount_percents.append(int(string[start:end]))
            else:
                discount_percents.append(0)
        for item in discount_percents:
            self.scraped_dict["discount_percents"].append(item)

    scraped_dict["titles"] = []  # todo refactor these back into method

    def get_titles_list(self, results_list):
        titles = []
        for result in results_list:
            titles.append(str(result.find("span", {"class": "title"}).string))
        for title in titles:
            self.scraped_dict["titles"].append(title)


class Filter:
    # every methode in this class will be applied to the the results
    # they all must take the list of results as an argument and returns the filtered list

    minimum_discount = 40
    def get_highly_discounted(self, merged_results, keys):
        percents_index = keys["discount_percents"]
        # parameters for get_good_games
        # todo make configureable
        before = len(merged_results)
        for i in range(0, len(merged_results)):
            if merged_results[i][percents_index] < self.minimum_discount:
                break
        merged_results = merged_results[:i]
        log(str(len(merged_results)) + " out of " + str(before) + " had good enough reviews")
        return merged_results

    # parameters for get_good_games
    # todo make configureable
    min_reviews = 100
    min_positive = 75
    def get_good_games(self, merged_results, keys):
        n_rev_idx = keys['n_user_reviews']
        min_positive_idx = keys['percent_reviews_positive']
        ret = []
        for result in merged_results:
            if result[self.n_rev_idx] >= self.min_reviews and result[self.min_positive_idx] >= self.min_positive:
                ret.append(result)
        return ret


def get_number_pages():
    first_page = http.request("GET", steam_special_url_firstpage)
    html_soup = bs4.BeautifulSoup(first_page.data, 'html.parser')

    result = html_soup.find_all("div", {"class": "search_pagination_right"})
    result = str(result)

    searchstring = 'page='
    pagelist = [m.start() for m in re.finditer(searchstring, result)]

    # it assumes that the 2nd to last result is the total number of pages
    index = pagelist[len(pagelist) - 2] + len(searchstring)
    # this code
    i = 0
    page_number = ""
    while result[index + i] != "\"":
        page_number += result[index + i]
        i += 1

    return int(page_number)


# def get_pages(): DEPRICATED
#     results = []
#     page = bs4.BeautifulSoup(http.request("GET", steam_special_url_firstpage).data, 'html.parser')
#     results = get_results_from_page( page, results)
#     num_pages = get_number_pages()
#     for i in range(2, num_pages + 1):
#         results = get_results_from_page(
#             bs4.BeautifulSoup(http.request("GET", steam_special_url_firstpage + and_page + str(i)).data, 'html.parser'), results)
#         log("got page "+ str(i) + "/" + str(num_pages))
#
#     return results


def run_scrape(test):
    results_as_strs = []
    if test:
        num_pages = 5
    else:
        num_pages = get_number_pages()
    for i in range(1, num_pages + 1):
        page_results_as_bs4 = get_results_from_page_n(i)
        log("got page " + str(i) + "/" + str(num_pages))

        apply_data_scraping(page_results_as_bs4)

        for result in page_results_as_bs4:
            results_as_strs.append(str(result))

    results_as_strs = apply_filters(results_as_strs)
    create_html(results_as_strs)


def apply_data_scraping(page_as_bs4):
    methods = get_methods_form_claas(Data_Sraping)  # returns list of 2 tuoles 0 = name 1 = method
    for method in methods:
        method[1](page_as_bs4)


def apply_filters(results_as_strs):
    # todo some lines of code that apply the methods in filter methods to the page
    # todo turn the data into a csv fist so it stays nice and organized

    keys = dict
    keys['results_as_strs'] = 0
    data = [results_as_strs]

    i = 1
    for key in Data_Sraping.scraped_dict.keys():
        data.append(Data_Sraping.scraped_dict[key])
        keys[key] = i
        i += 1

    data = listmerger(data)

    return results_as_strs  # only the ones that got past the filters
    pass


def get_results_from_page_n(page_n):
    page_results = []
    if page_n == 1:  # page 1 is special because it has no &page=n
        bs4.BeautifulSoup(http.request("GET", steam_special_url_firstpage).data, 'html.parser')
    else:
        page = bs4.BeautifulSoup(http.request("GET", steam_special_url_firstpage + and_page + str(page_n)).data, 'html.parser')

    i = page.find_all("a", {"class": "search_result_row"})
    for result in i:
        page_results.append(result)
    return page_results


def get_result_list(pages):
    results = []
    for page in pages:
        i = page.find_all("a", {"class": "search_result_row"})
        for result in i:
            results.append(result)
        i.clear()
    return results


def create_html(results_as_strs):  # todo get rid of that block thing on the page
    page = bs4.BeautifulSoup(http.request("GET", steam_special_url_firstpage).data, 'html.parser')
    tag = page.find("div", {"id": "search_result_container"})
    tag.clear()
    for result in results_as_strs:
        tag.append(bs4.BeautifulSoup(result, 'html.parser'))  # turns it back into bs4

    with open(ROOTDIR + dirsep + "results.html", 'w', encoding="utf-8") as outfile:
        outfile.write(str(page))


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
    # titles = get_titles_list(results_list)
    percents_list = get_discount_percents(results_list)

    # todo
    filter_results = listmerger([percents_list, results_list, n_user_reviews, percent_reviews_positive])
    filter_results.sort(key=lambda p: p[0], reverse=True)
    filter_results = slice_results(filter_results, 40, 0)
    filter_results = get_good_games(filter_results, 100, 75, 2, 3)

    create_html(filter_results)

    # this part is deprecated
    # for row in filter_results:
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
    # ui = Gui()
    # ui.open()
    run(1)

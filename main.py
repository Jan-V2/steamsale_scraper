import collections
import bs4
import urllib3
import re
from appJar import gui
from utils import ROOTDIR, listmerger, log, log_return, list_demerger, get_methods_from_class, ints_str
from utils import dir_sep as dirsep

steam_special_url_firstpage = "http://store.steampowered.com/search/?specials=1"
and_page = "&page="
http = urllib3.PoolManager()

html_file = "test.html"


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

def run_scrape(is_test):
    results_as_strs = []
    if is_test:
        num_pages = 5
    else:
        num_pages = get_number_pages()

    data_scraper = Data_Scraper()
    for i in range(1, num_pages + 1):
        page_results_as_bs4 = get_results_from_page_n(i)
        log("got page " + str(i) + "/" + str(num_pages))

        apply_data_scraping(page_results_as_bs4, data_scraper)

        for result in page_results_as_bs4:
            results_as_strs.append(str(result))

    results_as_strs = apply_filters(results_as_strs, data_scraper.scraped_dict)
    create_html(results_as_strs)
    log('done')



def apply_data_scraping(page_as_bs4, data_scraper):
    methods = get_methods_from_class(data_scraper)  # returns list of 2 tuoles 0 = name 1 = method
    for method in methods:
        method[1](page_as_bs4)


def apply_filters(results_as_strs, scraped_dict):
    keys = collections.defaultdict(int)# a dict contianing the indexes for bits of data
    keys.update({'results_as_strs':0})
    merged_results = [results_as_strs]

    i = 1
    for key in scraped_dict.keys():
        merged_results.append(scraped_dict[key])
        keys.update({key: i})
        i += 1

    merged_results = listmerger(merged_results)
    filter = Filter()
    for method in get_methods_from_class(filter):
        merged_results = method[1](merged_results, keys)

    return list_demerger(merged_results, keys['results_as_strs']) # only results_as_strs that got past the filters



def get_results_from_page_n(page_n):
    page_results = []
    if page_n == 1:  # page 1 is special because it has no &page=n
        page = bs4.BeautifulSoup(http.request("GET", steam_special_url_firstpage).data, 'html.parser')
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


def create_html(results_as_strs):
    page = bs4.BeautifulSoup(http.request("GET", steam_special_url_firstpage).data, 'html.parser')

    # deletes extra search options things because they break the page
    tag = page.find("div", {"id": "additional_search_options"})
    tag.clear()# deletes the search options bar thing
    #tag = page.find("div", {"class": "leftcol large"}) commented out because it leaves an ugly blue bar
    #tag.clear()# deletes the searchbar thing above the results

    # dumps the results in the page
    tag = page.find("div", {"id": "search_result_container"})
    tag.clear()
    # todo make it so that it adds the html as text tot the page rather than bs4 to save ram
    for result in results_as_strs:
        i = bs4.BeautifulSoup(result, 'html.parser')
        tag.append(i)  # turns it back into bs4

    with open(ROOTDIR + dirsep + "results.html", 'w', encoding="utf-8") as outfile:
        outfile.write(str(page))


class Data_Scraper:
    # every methode in this class will be applied to the the results
    # they all must take the list of results as an argument and add a list to the dict in this object and have no return
    # a list in which each result lines up with a result from the argument
    # like this ["review_scores": [list of review scores]]
    scraped_dict = collections.defaultdict(list)

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
        for i in range(len(n_user_reviews)):
            self.scraped_dict['n_user_reviews'].append(n_user_reviews[i])
            self.scraped_dict['percent_reviews_positive'].append(percent_reviews_positive[i])

    def get_discount_percents(self, results_list):
        log('scraping discount percents')
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

    def get_titles_list(self, results_list):
        log("scraping title")
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
        merged_results.sort(key=lambda p: p[percents_index], reverse=True)
        before = len(merged_results)
        for i in range(0, len(merged_results)):
            if merged_results[i][percents_index] < self.minimum_discount:
                break
        merged_results = merged_results[:i]
        log(str(len(merged_results)) + " out of " + str(before) + " had deep enough discount")
        return merged_results

    # parameters for get_good_games
    # todo make configureable
    min_reviews = 100
    min_positive = 65

    def get_good_games(self, merged_results, keys):
        n_rev_idx = keys['n_user_reviews']
        min_positive_idx = keys['percent_reviews_positive']
        ret = []
        before = len(merged_results)
        for result in merged_results:
            if result[n_rev_idx] >= self.min_reviews and result[min_positive_idx] >= self.min_positive:
                ret.append(result)
        log(str(len(ret)) + " out of " + str(before) + " had good enough reviews")
        return ret

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


# todo count duplicates to see if there's somthing i can do about it
# todo make gui
# todo add chache system
if __name__ == '__main__':
    # ui = Gui()
    # ui.open()
    run_scrape(False)

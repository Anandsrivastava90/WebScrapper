# doing necessary imports

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS,cross_origin
import requests
from bs4 import BeautifulSoup as bs, BeautifulSoup
from urllib.request import urlopen as uReq
import pymongo

app = Flask(__name__)  # initialising the flask app with the name 'app'




@app.route('/', methods=['POST', 'GET']) # route with allowed methods as POST and GET
def index():
    if request.method == 'POST':
        searchString = request.form['content'].replace(" ", "") # obtaining the search string entered in the form
        try:
            dbConn = pymongo.MongoClient("mongodb://localhost:27017/")  # opening a connection to Mongo
            db = dbConn['crawlerDB'] # connecting to the database called crawlerDB
            reviews = db[searchString].find({})  # searching the collection with the name same as the keyword
            if reviews.count() > 0:  # if there is a collection with searched keyword and it has records in it
                return render_template('results.html', reviews=reviews) # show the results to user
            else:
                flipkart_url = "https://www.flipkart.com/search?q=" + searchString # preparing the URL to search the product on flipkart
                flipkart_page = requests.get(flipkart_url, timeout=5)  # Requesting the Webpage on the Internet
                flipkart_html = BeautifulSoup(flipkart_page.content, 'html.parser')
                bigboxes = flipkart_html.findAll("div", {"class": "bhgxx2 col-12-12"})
                del bigboxes[0:3]
                box = bigboxes[0]
                product_link = "https://www.flipkart.com" + box.div.div.div.a['href']
                productRes = requests.get(product_link)

                prod_html = BeautifulSoup(productRes.content, 'html.parser')
                all_reviews_link = prod_html.find('div', {'class': 'swINJg _3nrCtb'})

                data = str(all_reviews_link.find_parent().get('href'))
                reviews_url = "https://www.flipkart.com" + data
                reviewsReq = requests.get(reviews_url)

                reviews_html = BeautifulSoup(reviewsReq.content, 'html.parser')
                a = reviews_html.find('div', {'class', '_2zg3yZ _3KSYCY'}).span.text
                total_count = int(a.split(' ')[-1])

                page_review_link = reviews_html.find('nav', {'class': '_1ypTlJ'})

                page_url = page_review_link.find('a', href=True)
                navigation_url = "https://www.flipkart.com" + str(page_url['href'])
                web_page = navigation_url[:navigation_url.rfind('1')]
                for i in range(1, total_count + 1):

                    nav_url = web_page + str(i)
                    reviewsReq_page = requests.get(nav_url)
                    reviews_html_page = BeautifulSoup(reviewsReq_page.content, 'html.parser')
                    commentboxes = reviews_html_page.find_all('div', {'class': "_1PBCrt"})
                    reviews = []
                    table = db[searchString]
                    for review in commentboxes:
                        try:
                            review_header = review.find_all('p', {'class': '_2xg6Ul'})
                            review_header = [e.get_text() for e in review_header]

                        except:

                            review_header = 'No Comment Heading'

                        try:
                            rating = review.find_all('div', {'class': 'hGSR34 E_uFuv'})
                            rating = [e.get_text() for e in rating]

                        except:

                            rating = 'No Rating'

                        try:

                            detailed_review = review.find_all('div', {'class': 'qwjRop'})
                            detailed_review = [e.get_text() for e in detailed_review]
                        except:

                            detailed_review = 'No customer Comment'

                        try:
                            user = review.find_all('p', {'class': '_3LYOAd _3sxSiS'})
                            user = [e.get_text() for e in user]
                        except:

                            user = 'No User'

                        mydict = {"Product": searchString, "Name": user, "Rating": rating, "CommentHead": review_header,
                                  "Comment": detailed_review}
                        x = table.insert_one(mydict)
                        reviews.append(mydict)
                return render_template('results.html', reviews=reviews) # showing the review to the user
        except:
            return 'something is wrong'
            #return render_template('results.html')
    else:
        return render_template('index.html')
if __name__ == "__main__":
    app.run(port=8000,debug=True) # running the app on the local machine on port 8000
import json
from flask import Flask, render_template, session, request
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options



app = Flask(__name__)
server_token = 'cx34Sdl58Bhg9'

def handleSearch(searchTerm, website):

    if(not searchTerm or not website):
        return 'Missing arguments', 500

    # set up the driver
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)
    chrome_options.add_argument("--headless")

    # driver = webdriver.Chrome("chromedriver")
    driver = webdriver.Chrome(options=chrome_options)
    driver.maximize_window()

    # navigate to google
    driver.get("https://www.google.com")

    # find the search bar element and enter the search term
    search_bar = driver.find_element(By.NAME, "q")
    search_bar.send_keys(searchTerm + Keys.RETURN)

    # wait for the search results to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "search"))
    )

    # find the first search result and click on it
    search_results = driver.find_elements(By.XPATH, "//div[@class='yuRUbf']//a")

    for result in search_results:
        link = result.get_attribute('href')
        print(link)
        if website in link:
            print('result found')
            result.click()
            driver.quit()
            return {'status': 'Successfully clicked the link', 'searchTerm': searchTerm, 'website': website, 'code': 200}
            break

    # something went wrong!
    driver.quit()
    return {'status': 'Error while clicking the link', 'searchTerm': searchTerm, 'website': website, 'code': 500}


@app.route('/searchApi')
def index():
    return 'Silence is Gold!', 200

@app.route('/searchApi/getConfig')
def getConfig():
    with open( "./websitesConfig.json"  )  as f:
        menu_items_dict = json.load( f )
        websitesData = menu_items_dict

    return render_template('config.html' , data=json.dumps(websitesData, separators=(',', ':')) )

@app.route('/searchApi/updateConfig', methods = ['POST'])
def updateConfig():
    jsonBody = request.json
    token = jsonBody.get('token')
    if(not token or token != server_token):
            return 'Please provide a valid token', 403

    with open( "./websitesConfig.json" , 'w') as f:
            f.write(jsonBody.get('data'))
    return {}, 200

@app.route('/searchApi/searchKeywords', methods = ['GET'])
def initiateSearch():
    try:
        token = request.args.get('token')
        # searchData = jsonBody.get('searchData')
        with open( "./websitesConfig.json"  )  as f:
            menu_items_dict = json.load( f )
            searchData = menu_items_dict
        responseBody = []

        if(not token or token != server_token):
            return 'Please provide a valid token', 403
        
        if not searchData:
            return 'Empty list provided', 500

        for searchItem in searchData:
            res = handleSearch(searchItem.get('searchTerm'), searchItem.get('website'))
            responseBody.append(res)
        
        print(responseBody)
        return responseBody, 200
    
    except Exception as exp:
        return 'Somehing went wrong!', 500
    

    # driver.quit()
    # close the driver
    # WebDriverWait(driver, 10000).until(
    #     EC.presence_of_element_located((By.ID, "search"))
    # )



if __name__ == '__main__':
	app.run(port=8003, debug=True)
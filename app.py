import json
import smtplib
from flask import Flask, render_template, session, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime,timedelta
import time




app = Flask(__name__)
server_token = 'cx34Sdl58Bhg9'


email_address = "fidelityhomegroupcronjobs@gmail.com"
email_password = "pjbzjsvfdkoytyrp"
smtp_server = "smtp.gmail.com"
smtp_port = 587


# Dictionary to keep track of successful and unsuccessful searches
search_results = {
    'success': [],
    'failure': []
}

def handleSearch(searchTerm, website):
    print(website)
    if(not searchTerm or not website):
        return 'Missing arguments', 500

    # set up the driver
    chrome_options = Options()
    chrome_options.add_experimental_option("detach", True)
    chrome_options.add_argument("--headless") 
    # driver = webdriver.Chrome("chromedriver")
    driver = webdriver.Chrome("chromedriver", options=chrome_options)
    # driver = webdriver.Chrome(options=chrome_options)
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

    # Find the website in the search results up to 4 pages
    for page_number in range(1, 5):
        # find the first search result and click on it
        search_results = driver.find_elements(By.XPATH, "//div[@class='yuRUbf']//a")

        
        for result in search_results:
            link = result.get_attribute('href')
            print(link)
            if website in link:
                print('result found')
                result.click()
                driver.quit()
                return {'status': 'Successfully clicked the link', 'searchTerm': searchTerm, 'website': website, 'page_number': page_number, 'code': 200}
                break


        # move to the next page
        next_page = driver.find_element(By.XPATH, f"//a[@aria-label='Page {page_number + 1}']")
        next_page.click()
        WebDriverWait(driver, 100).until(EC.presence_of_element_located((By.ID, "search")))
   
    # something went wrong!
    driver.quit()
    return {'status': 'Error while clicking the link', 'searchTerm': searchTerm, 'website': website, 'code': 500}

def send_email(subject, body, attachment=None):
    recipient_emails = ["cronjob@fidelityhomegroup.com", "mirrashidmir009@gmail.com"]
    msg = MIMEMultipart()
    msg["From"] = email_address
    msg["To"] = ", ".join(recipient_emails)
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    if attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{attachment}"')
        msg.attach(part)

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(email_address, email_password)
        server.sendmail(email_address, recipient_emails, msg.as_string())
        server.quit()
        print("Email sent successfully.")
    except Exception as e:
        print("Error sending email:", e)


search_job_triggered = False

def run_search_job(search_data, num_runs):
    run_interval = 1400 * 60 / num_runs  # Interval between each run in seconds =>  minutes each day * 60
    completed_runs = 0  # Counter to keep track of completed runs

    for _ in range(num_runs):
        stats = load_stats_from_file()

        for search_item in search_data:
            try:
                res = handleSearch(search_item.get('searchTerm'), search_item.get('website'))
                if res.get('code') == 200:
                    search_results['success'].append(res)
                    stats[search_item.get('searchTerm')] = stats.get(search_item.get('searchTerm'), {'success': 0, 'failure': 0})
                    stats[search_item.get('searchTerm')]['success'] += 1
                else:
                    search_results['failure'].append(res)
                    stats[search_item.get('searchTerm')] = stats.get(search_item.get('searchTerm'), {'success': 0, 'failure': 0})
                    stats[search_item.get('searchTerm')]['failure'] += 1
            except Exception as e:
                print("Error in handleSearch:", e)

        # Write updated stats to the file
        update_stats_to_file(stats)

        print(search_results)

        completed_runs += 1

        if completed_runs == num_runs:
            # If all runs are completed, send the summary email
            send_summary_email(stats)

        # Wait for the specified interval before the next run
        time.sleep(run_interval)

def schedule_search_job(search_data, num_runs):
    # Call the function to schedule the job with desired parameters
    run_search_job(search_data, num_runs)


def update_stats_to_file(stats):
    with open("stats.json", "w") as file:
        json.dump(stats, file, indent=4)

def load_stats_from_file():
    try:
        with open("stats.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def clear_stats_file():
    with open("stats.json", "w") as file:
        json.dump({}, file, indent=4)


def send_summary_email(stats):
    try:
        # Sending a summary email with all search results
        date = datetime.now().strftime("%Y-%m-%d")
        time_now = datetime.now().strftime("%H:%M:%S")
        subject = f"Search Results Summary on {date} at {time_now} | Success"
        body = ""
        for search_term, stat in stats.items():
            success_count = stat.get('success', 0)
            failure_count = stat.get('failure', 0)
            body += f"Search Term: {search_term}\nSuccess: {success_count}\nFailure: {failure_count}\n\n"

        send_email(subject, body)
    except Exception as e:
        print("Error in sending email:", e)

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
def initiate_search():
    global search_job_triggered

    try:
        token = request.args.get('token')
        

        with open("./websitesConfig.json") as f:
            menu_items_dict = json.load(f)
            search_data = menu_items_dict

        if not token or token != server_token:
            return 'Please provide a valid token', 403


        if not search_data:
            return 'Empty list provided', 500


        if not search_job_triggered:
            # Call the function to schedule the job with desired parameters
            num_runs = 120  # Set the number of runs as needed
            schedule_search_job(search_data, num_runs)
            search_job_triggered = True


        clear_stats_file()

        return jsonify(search_results), 200

    except Exception as exp:
        subject = "Search Results Summary | Error"
        body = "Something went wrong"
        send_email(subject, body)
        return 'Something went wrong!', 500

    # driver.quit()
    # close the driver
    # WebDriverWait(driver, 10000).until(
    #     EC.presence_of_element_located((By.ID, "search"))
    # )


if __name__ == '__main__':
#  gunicorn -w 1 -b 127.0.0.1:8003 app:app
 app.run(port=8003, debug=True)
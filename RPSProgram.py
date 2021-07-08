"""
This program utilizes Selenium and Python to automate the process of checking for studies on the UCalgary SONA RPS website.
Copyright (C) 2021  Gurveer Gill

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from time import time, sleep, strftime

from discord_webhooks import DiscordWebhooks
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

# General program parameters
USERNAME = ""
PASSWORD = ""
CODE_SLEEP_TIME = 30
WEBHOOK_URL = ("")
SEND_NOTIFICATION = True
RECORD_STUDIES = False
LOCAL_TESTING = False
BROWSER = webdriver.Firefox()
STUDY_OMISSION_LIST = []  # List to add studies already notified about, so that repeat notifications aren't sent.

def local_test():
    """Local testing function"""

    import os
    global WEBHOOK_URL

    html_file = os.getcwd() + "//" + " " # <- Put path to html studies files here.
    BROWSER.get("file:///" + html_file)
    TESTING_WEBHOOK_URL = ()
    WEBHOOK_URL = TESTING_WEBHOOK_URL


def start_RPS(username, password):
    """Opens the browser, logs into RPS, and opens the study view."""

    # Open the RPS website
    BROWSER.get("https://ucalgary.sona-systems.com/Default.aspx?ReturnUrl=%2f")
    WebDriverWait(BROWSER, 3)  # In case of slow loading, wait 3 seconds for page to ensure the page has fully loaded.

    # Enter username and password
    username_input_field = BROWSER.find_element_by_id("ctl00_ContentPlaceHolder1_userid")
    password_input_field = BROWSER.find_element_by_id("ctl00_ContentPlaceHolder1_pw")

    username_input_field.send_keys(username)
    password_input_field.send_keys(password)

    # Click authentication button
    login_button = BROWSER.find_element_by_id("ctl00_ContentPlaceHolder1_default_auth_button")
    login_button.click()

    # Open study view
    WebDriverWait(BROWSER, 3)  # In case of slow loading, wait 3 seconds for page to ensure the page has fully loaded.
    study_view_button = BROWSER.find_element_by_id("lnkStudySignupLink")
    study_view_button.click()


def study_exists():
    """Check if RPS contains any studies."""

    # If no studies exist, return false. Otherwise, return true.
    if "No studies are available at this time." in BROWSER.page_source:
        return False
    return True


def discord_notification():
    """Sends a discord notification of an available study."""

    webhook = DiscordWebhooks(WEBHOOK_URL)

    # Retrieve study information
    raw_study_info = BROWSER.find_element_by_xpath("//*[contains(@id, 'HyperlinkStudentStudyInfo')]").text
    raw_study_credits = BROWSER.find_element_by_xpath("//*[contains(@id, 'LabelCredits')]").text.strip("()")
    raw_study_description = BROWSER.find_element_by_xpath("//*[contains(@id, 'LabelStudyType')]").text
    raw_study_eligibility = BROWSER.find_element_by_xpath("//*[contains(@id, 'LabelIndvitation')]").text

    # Check if any of the field don't exist and, if they don't, then set their respective variable to unknown
    if raw_study_info == "":
        raw_study_info = "Unknown"
    if raw_study_credits == "":
        raw_study_credits = "Unknown"
    if raw_study_description == "":
        raw_study_description = "Unknown"
    if raw_study_eligibility == "":
        raw_study_eligibility = "Unknown"

    # Set the contents of the messages
    webhook.set_content(content="@everyone", title="Study Up!", url="https://ucalgary.sona"
                                                                    "-systems.com/default.aspx",
                        color=0xFFA500)

    # Attaches an author
    webhook.set_author(name="RPS Study Notification Bot")

    # Appends fields with study information
    webhook.add_field(name="Study:", value=raw_study_info)
    webhook.add_field(name="Credits:", value=raw_study_credits)
    webhook.add_field(name="Description:", value=raw_study_description)
    webhook.add_field(name="Eligibility:", value=raw_study_eligibility)

    # Check if a notification has already been sent for the particular study
    if raw_study_info not in STUDY_OMISSION_LIST:
        webhook.send()

    return raw_study_info, raw_study_credits, raw_study_description, raw_study_eligibility


def file_recording(study_info, study_credits, study_description, study_eligibility):
    """Record that a study was posted in a .txt file."""

    if study_info not in STUDY_OMISSION_LIST:
        with open("recordFile.txt", "a") as recordingFile:
            recordingFile.write("Notification Sent: %s\n"
                                "    Study Info: %s\n    Credits: %s\n    Description: %s\n    Eligibility: %s\n"
                                % (str(strftime("%l:%M %p %z on %b %d, %Y")),
                                   study_info, study_credits, study_description, study_eligibility))


def main():
    if LOCAL_TESTING:
        local_test()
        if study_exists():
            discord_notification()

    else:
        start_time, refresh_time = time()
        hour = 0

        start_RPS(USERNAME, PASSWORD)

        try:
            while True:
                # Check if a study is up or not
                if study_exists():

                    # Send notification if SEND_NOTIFICATION is true
                    if SEND_NOTIFICATION:
                        study_info, study_credits, study_description, study_eligibility = discord_notification()

                        # Record study information if RECORD_STUDIES is true
                        if RECORD_STUDIES:
                            file_recording(study_info, study_credits, study_description, study_eligibility)

                        STUDY_OMISSION_LIST.append(study_info)
                        refresh_time = time()

                        print("Study!\nMinutes since program execution:", (time() - start_time) / 60 + (hour * 60))
                        print()

                # Make the program sleep for CODE_SLEEP_TIME number of minutes and then refresh the website.
                sleep(CODE_SLEEP_TIME * 60)
                BROWSER.refresh()

                # Check if an hour has elapsed since the program began running
                if (time() - start_time) / 60 >= 60:
                    print("\nHour Elapsed")
                    start_time = time()
                    hour += 1

                # TODO: Fix the logic behind notifying of a study that was already notified about. A dictionary could be
                #  a potential solution, but the code would need some overall changing. A nested list wouldn't work
                #  because it the study info wouldn't be found in the main list as its in a nested list. So,
                #  go with a dict.
                if (time() - refresh_time) / 60 >= 21:
                    for _ in range(len(STUDY_OMISSION_LIST)):
                        STUDY_OMISSION_LIST.pop()
                    refresh_time = time()

        except KeyboardInterrupt:
            print("Minutes since program execution:", (time() - start_time) / 60 + (hour * 60))
            BROWSER.quit()


if __name__ == "__main__":
    main()

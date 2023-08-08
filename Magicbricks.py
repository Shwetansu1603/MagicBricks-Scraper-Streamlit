import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import time
import pandas as pd
import base64
from io import BytesIO

def scrape_property_data(url):
    # Specify the path to the Chrome WebDriver executable
    webdriver_path = "{Webdriver_Location}"

    # Configure the Chrome WebDriver service
    service = Service(webdriver_path)

    # Launch the browser
    driver = webdriver.Chrome(service=service)

    # Open the webpage
    driver.get(url)

    # Wait for the page to load
    time.sleep(3)

    # Scroll to the bottom of the page
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.find_element_by_tag_name('body').send_keys(Keys.END)
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    # Get the page source after scrolling
    page_source = driver.page_source

    # Close the browser
    driver.quit()

    # Create BeautifulSoup object from the page source
    soup = BeautifulSoup(page_source, 'html.parser')

    # Find all divs with class "mb-srp__card"
    property_divs = soup.find_all('div', class_='mb-srp__card')

    # Create a list to store the property data dictionaries
    data_list = []

    # Iterate over the property divs
    for div in property_divs:
        property_data = {}

        # Extract the data from the first column and split it into 'Details' and 'Location'
        details_location = div.find('h2', class_='mb-srp__card--title').text.strip()
        if 'for' in details_location:
            details, location = details_location.split('for', 1)
        else:
            details = details_location
            location = ""

        property_data['Details'] = details.strip()
        property_data['Location'] = location.strip()

        # Society_Name = div.find('a', class_='mb-srp__card__society--name')
        # property_data['Society Name'] = Society_Name.text.strip() if Society_Name else "N/A"

        Price = div.find('div', class_='mb-srp__card__price--amount')
        property_data['Price'] = Price.text.strip() if Price else "N/A"

        PricePerSize = div.find('div', class_='mb-srp__card__price--size')
        property_data['Price per Size'] = PricePerSize.text.strip() if PricePerSize else "N/A"

        summary_list = div.find('div', class_='mb-srp__card__summary__list')
        if summary_list:
            labels = summary_list.find_all('div', class_='mb-srp__card__summary--label')
            values = summary_list.find_all('div', class_='mb-srp__card__summary--value')
            for label, value in zip(labels, values):
                label_text = label.text.strip()
                value_text = value.text.strip()
                if label_text != "":
                    property_data[label_text] = value_text

        # Append the property data dictionary to the list
        data_list.append(property_data)

    # Create a DataFrame from the list of dictionaries
    df = pd.DataFrame(data_list)

    return df

# Create a Streamlit app
def main():
    st.title("MagicBricks Property Data Scraper")

    # Get the URL input from the user
    url = st.text_input("Enter the MagicBricks URL to scrape")

    if st.button("Scrape"):
        if url:
            st.info("Scraping in progress...")
            df = scrape_property_data(url)
            if not df.empty:
                st.success("Scraping completed successfully!")

                # Fill blank entries with "N/A"
                df.fillna("N/A", inplace=True)

                # Create a BytesIO buffer for Excel file
                excel_buffer = BytesIO()

                # Create Excel writer using the buffer
                excel_writer = pd.ExcelWriter(excel_buffer, engine="xlsxwriter")
                df.to_excel(excel_writer, index=False)
                excel_writer.close()
                excel_buffer.seek(0)

                # Create a button to download the Excel file
                button_label = "Download Excel File"
                button_text = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{base64.b64encode(excel_buffer.read()).decode()}" download="property_data.xlsx">{button_label}</a>'
                st.markdown(button_text, unsafe_allow_html=True)
            else:
                st.warning("No data found. Please check the URL or try a different one.")
        else:
            st.error("Please enter a valid URL.")

# Run the Streamlit app
if __name__ == '__main__':
    main()

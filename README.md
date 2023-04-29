Project Description

This project is a web scraping script built with Selenium, which is designed to extract data related to logistics from a logistics service provider's website. The script is capable of automating the entire process of logging in, navigating to the required pages, extracting data, and saving it to a xlsx file.

The data that can be extracted includes the name of the cargo, the origin and destination of the shipment, the type of shipment, the date of shipment, and the current status of the shipment and other data.

## Installation and Setup

To use this script, you will need to have Python 3 installed on your machine, along with the following libraries:

- selenium
- pandas
- BeautifulSoup

To install these libraries, you can use the following command:

```
pip install selenium pandas bs4
```

You will also need to download the ChromeDriver executable and save it to a directory on your machine. You can download the latest version of ChromeDriver from the following link: https://chromedriver.chromium.org/downloads

Once you have installed the required libraries and downloaded the ChromeDriver executable, you can clone this repository to your local machine using the following command:

```
git clone https://github.com/molchoun/logistics-web-scraping-selenium.git
```

## Usage

To use this script, you will need to provide your login credentials for the logistics service provider's website in the `config.py` file. You will also need to modify the `search_criteria` dictionary in the `main.py` file to specify the search criteria for the shipments you want to extract data for.

Once you have set the required parameters, you can run the script using the following command:

```
python scrape.py
```

The script will then launch the Chrome browser and automate the process of logging in, navigating to the required pages, and extracting data. The extracted data will be saved to a CSV file in the `data` directory.

## License

This project is licensed under the MIT License. You are free to use, modify, and distribute the code as you see fit.

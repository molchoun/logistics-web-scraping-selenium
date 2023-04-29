import pandas as pd
from bs4 import BeautifulSoup
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager


def get_dfs(driver, df, company_name ):
	"""Gets the source page html and extracts the necessary data useing bs4.
		Returns the pandas dataframe of the page data concatenated with the 
		previous pages data"""

	page_content = driver.page_source
	soup = BeautifulSoup(page_content, 'html.parser')
	table = soup.find('table', class_='pl-table')

	for row in table.tbody.find_all('tr'):    
	# Find all data for each column
		columns = row.find_all('td')
		if(columns != []):
			load_id = columns[0].text.strip()
			pick_up = columns[1].text.strip()
			pick_location = columns[2].text.strip()
			deliver_location = columns[3].text.strip()
			distance = columns[4].text.strip()
			weight = columns[5].text.strip()
			equipment = columns[6].text.strip()
			view = f'https://quickview.parade.ai/q/external/{company_name}/{load_id}?utm_medium=button&utm_source=p4c'

			df = pd.concat([df, pd.DataFrame.from_dict({'Load ID': [load_id],  'Pick-up Date': [pick_up],
							'Pick-up Location': [pick_location], 'Deliver Location': [deliver_location],
							'Distance': [distance], 'Weight': [weight],
							'Equipment': [equipment], 'View': [view]})])
	return df

def click(selector, input_data=None):
	"""Finds the element by css selector and clicks on it , or sends input text"""

	button = WebDriverWait(driver, 30).until(
		EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
	ActionChains(driver).move_to_element(button).click(button).perform()
	time.sleep(1)
	if input_data is not None:
		button.send_keys(input_data)
		time.sleep(1)

def create_driver():
	"""Creates and returns the driver object"""

	op = webdriver.ChromeOptions()
	op.add_argument("--headless")
	op.add_argument("--disable-gpu")
	op.add_argument("--disable-crash-reporter")
	op.add_argument("--disable-extensions")
	op.add_argument("--disable-in-process-stack-traces")
	op.add_argument("--disable-logging")
	op.add_argument("--disable-dev-shm-usage")
	op.add_argument("--log-level=3")
	op.add_argument("--output=/dev/null")
	driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=op)
	# Uncomment the line bellow for debugging purpose to see the chrome GUI
	# driver = webdriver.Chrome(ChromeDriverManager().install())

	return driver

def read_credentials():
	"""Reads the login credentials from file and returns the user and password"""

	login_credentials = open('login_credentials.txt', 'r')
	user = login_credentials.readline()
	password = login_credentials.readline()

	return (user, password)

def postprocess_result(df):

	pickup = df['Pick-up Location'].tolist()
	deliver = df['Deliver Location'].tolist()

	df.rename(columns={'Pick-up Location': 'Pick-up City', 'Deliver Location': 'Deliver City'}, inplace=True)
	# Split the pickup and delivery addresses by city and state and
	# write them in different columns
	df['Pick-up City'] = [i.split(',')[0].strip() for i in pickup]
	df['Pick-up State'] = [i.split(',')[1].strip() for i in pickup]
	df['Deliver City'] = [i.split(',')[0].strip() for i in deliver]
	df['Deliver State'] = [i.split(',')[1].strip() for i in deliver]
	
	cols = ['Load ID', 'Pick-up City', 'Pick-up State', 'Pick-up Date', 'Deliver City', 'Deliver State' ,
			'Distance', 'Weight', 'Equipment', 'View']

	df = df[cols]
	df = df.drop_duplicates('Load ID', keep='first')
	
	return df

def main(driver):
	
	driver.get('https://carriers.parade.ai')
	time.sleep(2)
	user, passwd = read_credentials()
	# username input
	click("#username-uid1", user)
	# password input
	click('#password-uid2', passwd)
	# click submit
	button = 'body > div.atlaskit-portal-container > div > div > div:nth-child(3) > div.css-23yjpu.ez8cmp61 > div > div > div > form > div.form-footer-wrapper > button'
	click(button)

	load = WebDriverWait(driver, 30).until(
		EC.presence_of_element_located((By.CLASS_NAME, "company__name")))
	print('Sucessfully loged in')

	companies = driver.find_elements(By.CLASS_NAME, 'company__name')
	df = pd.DataFrame(columns=['Load ID', 'Pick-up Date', 'Pick-up Location', 'Deliver Location',
								'Distance', 'Weight', 'Equipment', 'View'])
	for comp in companies:
		ActionChains(driver).scroll_by_amount(-200000, -2000).perform()
		time.sleep(1)
		ActionChains(driver).move_to_element(comp).click(comp).perform()
		# Click "All Loads" button
		click("#tabnav > nav > div:nth-child(3) > div")

		current_url = str(driver.current_url)
		prefix = current_url.index('direct/')
		suffix = current_url.index('?tab=all_loads')
		company_name = current_url[prefix + len('direct/'): suffix]
		print(f"Starting scraping {company_name} >>>>>>>>>>>>")
		df = get_dfs(driver, df, company_name)
		next_page_selector = '#partner-page > div.right-panel-wrapper > div > div.public-loads > div > div > div > button.css-1wcgx3p'
		try:
			next_page = driver.find_element(By.CSS_SELECTOR, next_page_selector)
		except NoSuchElementException:
			continue
		ActionChains(driver).scroll_by_amount(200000, 2000).perform()
		time.sleep(1)
		while not next_page.get_property('disabled'):
			ActionChains(driver).move_to_element(next_page).click(next_page).perform()
			df = get_dfs(driver, df, company_name)

	return postprocess_result(df)	

if __name__ == "__main__":
	
	start_time = time.time()
	driver = create_driver()
	print("Starting scraping Parade")
	df = main(driver)
	filename = f"parade_{pd.to_datetime('today').strftime('%d-%m-%Y')}.xlsx"
	df.to_excel(filename, index=False)
	print(f"Scrapping results are saved to {filename} file")
	print("Total time ", int(time.time() - start_time), " seconds")
	driver.close()
	sys.exit()

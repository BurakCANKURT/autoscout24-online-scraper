from selenium import webdriver
from selenium.webdriver.chrome.service import  Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
from webdriver_manager.chrome import ChromeDriverManager
import os
from selenium.webdriver.chrome.options import Options



class OnlineAutoscout24:
    def __init__(self):
        self.driver =None
        self.website = 'https://www.autoscout24.com/'


    def startDriver(self):
        options = Options()
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--headless")
        service = Service(executable_path=ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service,options=options)
        

        return self.driver
        


    def pop_up_accept(self, driver):
        try:
            pop_up_accept = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//button[@class = "_consent-accept_1lphq_114"]'))
            )
            pop_up_accept.click()
        except:
            pass
    
    def pure_number(self,text):
        """
        pure_text = ''
        for letter in text:
            if letter==',':
                letter = ''
            pure_text = letter + pure_text
        """
        return text.replace(',', '')

    def find_last_page_num(self):

        try:
            pagination_bar = WebDriverWait(self.driver, 20).until(
                lambda driver: driver.find_elements(By.XPATH, '//nav[@class ="scr-pagination FilteredListPagination_pagination__3WXZT"]/ul/li')
            )


            last_page = pagination_bar[-3]
            last_page_number = int(last_page.text)
        except:
            last_page_number = 1
        return last_page_number


    def all_car_links(self, webpage_url):
        self.driver.get(webpage_url)

        try:
            possible_all_car_links = WebDriverWait(self.driver, 20).until(
                lambda driver: driver.find_elements(By.XPATH,'//div[@class = "ListItem_header__J6xlG ListItem_header_new_design__Rvyv_"]/a'))
                
            all_links = []
            for link in possible_all_car_links:
                car_link = link.get_attribute('href')
                all_links.append(car_link)         
        except:
            all_links = []
        return all_links

    def split_url_until_find_page_add_powertype(self, url):
        splitted_url = url.split('&powertype')
        splitted_elements = []
        for element in splitted_url:
            splitted_elements.append(element)
        return splitted_elements


    def safe_find_element(self, driver, selectors, timeout=10):
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        for by, selector in selectors:
            try:
                element = WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located((by, selector))
                )
                return element
            except:
                continue
        return None
        
    def scrap_the_page_to_df(self, url):
        self.driver.get(url)

        
        all_headers = []
        all_features = []
        df_feature = {}
        try:
            # TODO Car Brand
            car_name = WebDriverWait(self.driver, 20).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, 'span.StageTitle_boldClassifiedInfo__sQb0l'))
            )
            car_name_string = car_name.text.strip()
            df_feature['brand'] = car_name_string.strip().split(' ')[0]
        except:
            df_feature['brand'] = ''
        
        # TODO Car Model
        df_feature['model'] = ' '.join(car_name_string.split(' ')[1:]) if car_name_string else ''

        try:
            # TODO Car Price
            car_price = WebDriverWait(self.driver, 20).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, 'span.PriceInfo_price__XU0aF'))
            )
              
            df_feature['price'] = car_price.text
        except:
            df_feature['price'] = ''

        try:
            # TODO General Feature
            first_feature_block = WebDriverWait(self.driver, 20).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, 'div.VehicleOverview_containerMoreThanFourItems__691k2'))
            )
            first_feature_block_each_row = WebDriverWait(first_feature_block,20).until(
                lambda driver: driver.find_elements(By.CSS_SELECTOR,
                                                    'div.VehicleOverview_itemContainer__XSLWi')
            )
            
            for row in first_feature_block_each_row:
                first_row_header = row.find_element(By.CSS_SELECTOR, 'div.VehicleOverview_itemTitle__S2_lb').text
                first_row_feature = row.find_element(By.CSS_SELECTOR, 'div.VehicleOverview_itemText__AI4dA').text
                df_feature[first_row_header] = first_row_feature
        except:
            pass
        
        try:
            # TODO All Feature
            all_block = WebDriverWait(self.driver, 20).until(
                lambda driver: driver.find_elements(By.CSS_SELECTOR,
                                                    'dl.DataGrid_defaultDlStyle__xlLi_')
            )
            
            for each_block in all_block:
                all_headers_general = each_block.find_elements(By.CSS_SELECTOR, 'dt')
                for header in all_headers_general:
                    all_headers.append(header.text)

                all_features_general = each_block.find_elements(By.CSS_SELECTOR, 'dd')
                for feature in all_features_general:
                    all_features.append(feature.text)
        except:
            pass

        index = 0
        while index < len(all_features):
            df_feature[all_headers[index]] = all_features[index]
            index += 1
        df = pd.DataFrame([df_feature])
        print(f"Currnet df is-- >{df}")

        return df

    #TODO Contstuct selection phase for fuel_type, power , mileage, gearbox: WORKING <<TESTED>>
    def contruct_all_possibilities_for_FPMG(self, fuel,each_power_from,each_power_to,each_mileage_from,each_mileage_to,gearbox_array):

        all_FPMG = []
        for each_fuel in fuel:
            for each_gearbox in gearbox_array:
                fpmg = f'fuel={each_fuel}&gear={each_gearbox}&kmfrom={each_mileage_from}&kmto={each_mileage_to}&powerfrom={each_power_from}&powerto={each_power_to}&powertype=hp'
                all_FPMG.append(fpmg)
        return all_FPMG

    #TODO select brand #TODO select model
    def filtered_form(self, brand_model,fuel_array, power_from_array,power_to_array ,mileage_from_array,mileage_to_array, gearbox_array):
        all_urls = []
        all_FPMG = self.contruct_all_possibilities_for_FPMG(fuel_array,power_from_array,power_to_array,mileage_from_array,mileage_to_array,gearbox_array)
        for fpmg in all_FPMG:
            page_url = f'{self.website}/lst/{brand_model}/?atype=C&cy=D%2CA%2CB%2CE%2CF%2CI%2CL%2CNL&damaged_listing=exclude&desc=0&{fpmg}&powertype=kw&search_id=ppuu00tm4c&sort=standard&source=homepage_search-mask&ustate=N%2CU'
            all_urls.append(page_url)
        return all_urls

    #Working <<Tested>>
    def generate_url_for_web(self, brand,selected_brand_models, country_array):
        all_brand_model_country_array = []

        brand_url = f'https://www.autoscout24.com/lst/{brand}?atype=C&cy=D%2CA%2CB%2CE%2CF%2CI%2CL%2CNL&damaged_listing=exclude&desc=0&powertype=kw&search_id=72faoj4adc&sort=standard&source=homepage_search-mask&ustate=N%2CU'

        self.driver.get(brand_url)
        brand_car_info = WebDriverWait(self.driver, 20).until(
            EC.visibility_of_element_located(
                (By.XPATH, '//h1[@data-testid = "list-header-title"]'))
        )
        brand_car_info_text = brand_car_info.text
        brand_car_amount_text = brand_car_info_text.split(' ')[0]
        brand_car_amount = self.pure_number(brand_car_amount_text)
        
        index = 0
        if int(brand_car_amount) > 400:

            for each_brand_model in selected_brand_models:
                brand_model_url = f'https://www.autoscout24.com/lst/{each_brand_model}?atype=C&cy=D%2CA%2CB%2CE%2CF%2CI%2CL%2CNL&damaged_listing=exclude&desc=0&powertype=kw&search_id=72faoj4adc&sort=standard&source=homepage_search-mask&ustate=N%2CU'
                self.driver.get(brand_model_url)
                car_info = WebDriverWait(self.driver, 20).until(
                    EC.visibility_of_element_located(
                        (By.XPATH, '//h1[@data-testid = "list-header-title"]'))
                )
                car_info_text = car_info.text
                car_amount_text = car_info_text.split(' ')[0]
                car_amount = self.pure_number(car_amount_text)
                if int(car_amount) > 400:
                    for country in country_array:
                        country_url = f'https://www.autoscout24.com/lst/{each_brand_model}?atype=C&cy={country}&damaged_listing=exclude&desc=0&powertype=kw&search_id=72faoj4adc&sort=standard&source=homepage_search-mask&ustate=N%2CU'
                        print(f'Index: {index} ')
                        all_brand_model_country_array.append(country_url)
                        index += 1
                else:
                    all_brand_model_country_array.append(brand_model_url)
                    print(f'Index: {index}')
                    index += 1
        else:
            print(f'Index: {index} ')
            all_brand_model_country_array.append(brand_url)
            index += 1

        return all_brand_model_country_array

    
    def brand_model_for_web(self, wanted_brand):
        page_url = f'{self.website}/lst/{wanted_brand}?atype=C&cy=D%2CA%2CB%2CE%2CF%2CI%2CL%2CNL&damaged_listing=exclude&desc=0&powertype=kw&search_id=ppuu00tm4c&sort=standard&source=homepage_search-mask&ustate=N%2CU'
        self.driver.get(page_url)
        # TODO ALL Models
        all_brand_input_for_model = WebDriverWait(self.driver, 20).until(
            lambda driver: driver.find_elements(By.XPATH, '//div[@class = "input-wrapper"]/input')
        )
        brand_model = all_brand_input_for_model[1]
        brand_model.click()
        try:
            all_models = self.driver.find_elements(By.XPATH, '//li[@role= "option"]')
            brand_model_array = []
            for model in all_models:
                model_text = model.text
                lower_text = model_text.lower()
                final_model_letter = ''
                for model_letter in lower_text:
                    if model_letter == ' ':
                        model_letter = '-'
                    final_model_letter = final_model_letter + model_letter
                    brand_model_array.append(final_model_letter)
            return brand_model_array
        except:
            pass

    
    def generate_specific_brand_model_country_url_for_web(self, brand,selected_models):
        print(f'Selected models:{selected_models}')
        country_array = ['D', 'A', 'B', 'E', 'F', 'I', 'L', 'NL']
        models = self.brand_model_for_web(brand)
        brand_model_array = []

        for model in selected_models:

            brand_model_text = f'{brand}/{model}'
            brand_model_array.append(brand_model_text)
        print(f'Brand model array: {brand_model_array}')

        brand_model_country_urls = self.generate_url_for_web(brand,brand_model_array, country_array)
        return brand_model_country_urls

    def fix_car_amount(self, amount_text):
        try:
            splitted_car_amount = amount_text.split(',')
            return splitted_car_amount[0]+splitted_car_amount[1]
        except:
            return amount_text
        
    def check_car_amount(self):
        car_info = WebDriverWait(self.driver, 20).until(
            EC.visibility_of_element_located(
                (By.XPATH, '//h1[@data-testid = "list-header-title"]'))
        )
        car_info_text = car_info.text
        car_amount_text = car_info_text.split(' ')[0]
        return car_amount_text


    
        
      
                        
    def find_all_brands_array(self):
        all_brands_array = []

        all_brand_input = self.driver.find_elements(By.XPATH,'//div[@class = "input-wrapper"]/input')
        brand_input = all_brand_input[0]
        brand_input.click()
        all_brands = self.driver.find_elements(By.XPATH, '//ul[@id= "make-input-primary-filter-suggestions"]/li')
        for brand in all_brands:
            if brand != all_brands[0]:
                final_letter_brand = ''
                brand_text = brand.text
                brand_text = brand_text.lower()
                for brand_letter in brand_text:
                    if brand_letter == ' ':
                        brand_letter = '-'
                    final_letter_brand = final_letter_brand + brand_letter
                print(f'Brand: {final_letter_brand}')
                all_brands_array.append(final_letter_brand)
        return all_brands_array

    def find_all_brand_model_array(self):
        print('Starting to work!')
        all_brand_model_array = []
        
        all_brands_array = self.find_all_brands_array()
        for brand_key in all_brands_array:
            page_url = f'{self.website}/lst/{brand_key}?atype=C&cy=D%2CA%2CB%2CE%2CF%2CI%2CL%2CNL&damaged_listing=exclude&desc=0&powertype=kw&search_id=ppuu00tm4c&sort=standard&source=homepage_search-mask&ustate=N%2CU'
            self.driver.get(page_url)
            # TODO ALL Models
            
            all_brand_input_for_model = WebDriverWait(self.driver, 20).until(
                lambda driver: driver.find_elements(By.XPATH,
                                                    '//div[@class = "input-wrapper"]/input')
            )
            
            brand_input_for_model = all_brand_input_for_model[1]
            brand_input_for_model.click()
            try:
                all_models = self.driver.find_elements(By.XPATH, '//li[@role= "option"]')
                all_models_array  = []
                for model in all_models:
                    model_text = model.text
                    lower_text = model_text.lower()
                    final_model_letter = ''
                    for model_letter in lower_text:
                        if model_letter == ' ':
                            model_letter = '-'
                        final_model_letter = final_model_letter + model_letter
                    all_models_array.append(final_model_letter)
                    print(f'Current  = {brand_key}/{final_model_letter}')
                all_brand_model_array.append(all_models_array)
            except Exception as e:
                print(f'Error : {e}')

        return all_brand_model_array

    
    
    


        
    def find_mileage_and_power(self):
        all_mileage = []
        time.sleep(1)
        mileage_from_input = self.driver.find_element(By.XPATH, '//button[@id= "mileageFrom-input"]')
        mileage_from_input.click()

        all_miles = self.driver.find_elements(By.XPATH, '//ul[@id= "mileageFrom-input-suggestions"]/li')

        for mile in all_miles:
            if mile == all_miles[0]:
                all_mileage.append('')
            from_text = ''
            for each_text_from in mile.text:
                if each_text_from == ',':
                    each_text_from = ""
                from_text = from_text + each_text_from
            all_mileage.append(from_text)

        return all_mileage


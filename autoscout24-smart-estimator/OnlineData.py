from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import streamlit as st
from OnlineAutoscout24 import OnlineAutoscout24
import os
from ScrapElements import ScrapElements 

class OnlineData:
    def __init__(self):
        self.autoscout24 = None
        self.scraper = None
        self.scrapElements = ScrapElements()
        self.mileage_and_power_options = self.scrapElements.mileage_and_power_options
        self.all_fuel_options = self.scrapElements.all_fuel_options
        self.all_brands = self.scrapElements.all_brands
        self.all_model_for_each_brand = self.scrapElements.all_model_for_each_brand


    
    def brand_index_finder(self, selected_brand,all_brands):
        all_indices = []  
        for brand in selected_brand:
            index = 0
            for each_brand in all_brands:
                if brand == each_brand:
                    all_indices.append(index)
                    break
                index += 1
        return all_indices

    def find_selected_brands_models(self, selected_brand, all_models, all_brands):
        all_indices = self.brand_index_finder(selected_brand,all_brands)
        all_models_array = []
        for index in all_indices:
            all_models_array.append(all_models[index])
        return all_models_array

    def find_selected_brands_models_for_selection(self, selected_brand,all_models, all_brands):
        all_indices = self.brand_index_finder(selected_brand,all_brands)
        all_models_array = []
        for index in all_indices:
            for model in all_models[index]:
                all_models_array.append(model)
        return all_models_array

    def sorting_model_brand_selections(self, selected_brand,selected_model,all_model_for_each_brand,all_brands):
        all_brand_indices = self.brand_index_finder(selected_brand,all_brands)
        all_brand_model_patterns = []
        for brand_index in all_brand_indices:
            for each_selected_model in selected_model: 
                if each_selected_model in all_model_for_each_brand[brand_index]:
                    all_brand_model_patterns.append(f'{all_brands[brand_index]}/{each_selected_model}')
                
        return all_brand_model_patterns

    def kill_driver_process(self):
        import psutil
        try:
            parent = psutil.Process(self.driver_process_pid)
            for child in parent.children(recursive=True):
                child.kill()
            parent.kill()
            print("Driver process and child processes killed successfully.")
        except Exception as e:
            print(f"Error while killing driver processes: {e}")

    
    
    def scrap_page_by_page_web(self, selected_brands,selected_models,counter,fuel_array, power_from_array, power_to_array, mileage_from_array,mileage_to_array, gearbox_array,status, st, all_model_for_each_brand,all_brands, placeholder, ): 
        self.autoscout24 = OnlineAutoscout24()
        self.scraper = self.autoscout24.startDriver()
        try:
            while st.session_state['data_scraped'] == False:
                
                brands_models = self.sorting_model_brand_selections(selected_brands,selected_models,all_model_for_each_brand,all_brands)
                if 'all_df' not in st.session_state:
                    st.session_state.all_df = []
                all_url = []
                for brand_model in brands_models:
                    all_url = all_url + self.autoscout24.filtered_form(brand_model,fuel_array, power_from_array,power_to_array ,mileage_from_array,mileage_to_array, gearbox_array)
                
                url_index = 0
                for url in all_url:
                    if not status:
                        break 
                    print(f'Current url index = {url_index} Length of all url: {len(all_url)} -> Url : {url_index}')
                    
                    
                    self.scraper.get(url)
                    
                    WebDriverWait(self.scraper, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'div.ListItem_header__J6xlG'))
                    )
                    
                    car_amount = int(self.autoscout24.fix_car_amount(self.autoscout24.check_car_amount()))
                    print(f"Current link --> {url}")
                    print(f"Car amount--> {car_amount}")
                    last_page_num = self.autoscout24.find_last_page_num()
                    split_elements = self.autoscout24.split_url_until_find_page_add_powertype(url)
                    
                    
                    for page_index in range(1, last_page_num + 1):    
                        if not status:
                            break  

                        webpage_url = f'{split_elements[0]}&page={page_index}&powertype{split_elements[1]}'
                        
                        all_car_array_with_0_pages = self.autoscout24.all_car_links(webpage_url)
                        print(f"All car Array with 0: {all_car_array_with_0_pages}")
                        all_car_array = all_car_array_with_0_pages[:car_amount]

                        print(all_car_array)
                        
                        with placeholder.container():
                            for each_link in all_car_array:
                                
                                if not status:           
                                    break
                        
                                df = self.autoscout24.scrap_the_page_to_df(each_link)
                                print(f"Current df is--> {df}")
                                
                                try:
                                    
                                    self.display_cards(df, st)
                                    print(f'WEB=> Df is : {df}')
                                    st.session_state.all_df.append(df)
                                    counter += 1
                                    print(f'Current Page Number -----> {page_index} //// Car ----> {counter}')
                                except Exception as e:
                                    print(f"Error: {e}")              
                    
                    url_index += 1
                st.session_state['data_scraped'] = True

                if 'all_df' in st.session_state:
                    all_df = st.session_state.all_df
                    if isinstance(all_df, list) and len(all_df) > 0:
                    
                        combined_df = pd.concat(all_df, ignore_index=True)
                        combined_df.to_csv('temp_data.csv', index=False)
                        #st.session_state.all_df = combined_df 
                    
                    elif isinstance(all_df, pd.DataFrame) and not all_df.empty:
                        all_df.to_csv('temp_data.csv', index=False)
                    else:
                        st.session_state.loading = False
                        st.markdown(
                        "<style>.spinner-container { display: none; }</style>",
                        unsafe_allow_html=True
                        )  
                        st.warning('No car found...')
                if st.session_state['data_scraped'] == True:
                    break
        except Exception as e:
            
            st.warning(f"Exception: {e}")

        finally:
            if hasattr(self, 'scraper') and self.scraper:
                try:
                    self.scraper.quit()
                    print("Driver closed successfully!")
                except Exception as e:
                    print(f"Error closing driver: {e}")

                try:
                    self.kill_driver_process()
                except Exception as e:
                    print(f"Error during process kill: {e}")
        
        
        
        

    def display_cards(self, df, st):
        with st.container():
            
            st.markdown(
                f"""
                <style>
                    .info-card {{
                        background-color: #f8f9fa;
                        padding: 15px;
                        border-radius: 10px;
                        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                        margin-bottom: 10px;
                        text-align: left;
                        font-family: Arial, sans-serif;
                    }}
                    .info-card .row {{
                        display: flex;
                        flex-wrap: wrap;
                        gap: 20px;
                        align-items: center;
                        justify-content: flex-start;
                        font-size: 18px;
                        color: #333;
                    }}
                    .info-card .price {{
                        color: #1e88e5;
                        font-weight: bold;
                        font-size: 18px;
                    }}

                    /* Expander header */
                    details summary {{
                        background-color: #2c3e50; /* 🔵 Buraya istediğin rengi verebilirsin */
                        color: white;
                        font-weight: bold;
                        border-radius: 8px;
                        padding: 10px;
                        cursor: pointer;
                    }}
                    

                    details[open] {{
                        background-color: #ffffff;
                        padding: 15px;
                        border-radius: 8px;
                        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.4);
                        color: #333333;
                    }}



                    /* View Details inside */
                    .details-grid {{
                        display: grid;
                        grid-template-columns: 1fr 1fr;
                        gap: 10px 30px;
                        font-size: 16px;
                        color: #444;
                        margin-top: 10px;
                    }}
                    .details-grid p {{
                        margin: 0;
                        padding: 4px 0;
                    }}
                    .details-title {{
                        font-size: 20px;
                        font-weight: bold;
                        margin-bottom: 10px;
                        color: #1e88e5;
                    }}
                </style>

                <div class="info-card">
                    <div class="row">
                        <div><strong> Brand:</strong> {df['brand'].values[0]}</div>
                        <div><strong> Model:</strong> {df['model'].values[0]}</div>
                        <div class="price"><strong> Price:</strong> {df['price'].values[0]}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # View Details part
            with st.expander("View Details", expanded=False):
                st.markdown(f"""
                    <div class="details-title">🔍 Detailed Information</div>
                    <div class="details-grid">
                        <p><strong>Fuel type:</strong> {df['Fuel type'].values[0]}</p>
                        <p><strong>Mileage:</strong> {df['Mileage'].values[0]}</p>
                        <p><strong>Gearbox:</strong> {df['Gearbox'].values[0]}</p>
                        <p><strong>Power:</strong> {df['Power'].values[0]}</p>
                        <p><strong>Type:</strong> {df['Type'].values[0]}</p>
                        <p><strong>First Registration:</strong> {df['First registration'].values[0]}</p>
                        <p><strong>Seller:</strong> {df['Seller'].values[0]}</p>
                    </div>
                """, unsafe_allow_html=True)

            
            st.markdown("<hr style='border: 1px solid black; margin: 20px 0;'>", unsafe_allow_html=True)


    def update_selection_for_fuel(self, picked_types):
        all_url_versions = []
        all_fuel_type = {
            'Hybrid(Electric/Gasoline)': '2', 
            'Hybrid(Electric/Diesel)': '3',
            'Gasoline': 'B',
            'CNG' : 'C',
            'Diesel': 'D',
            'Electric' : 'E',
            'Hydrogen' : 'H',
            'LPG' :  'L',
            'Ethanol' : 'M',
            'Others' : 'O' 
        }   
        for each_picked in picked_types:       
            for fuel_type in all_fuel_type:
                if each_picked == fuel_type:
                    all_url_versions.append(all_fuel_type[each_picked])
        return  all_url_versions         

    all_gear_options = ['Automatic','Manuel' ,'Semi-automatic']

    def update_selection_for_gearbox(self, picked_types):
        all_url_versions = []
        all_gear = {
            'Automatic' : 'A',
            'Manuel' : 'M',
            'Semi-automatic' : 'S',
        }
        for each_picked in picked_types:       
            for fuel_type in all_gear:
                if each_picked == fuel_type:
                    all_url_versions.append(all_gear[each_picked])
        return  all_url_versions    

    

    def add_to_all_df(self, all_filtrations,current_filtration):
        if self.check_empty_filtrations(current_filtration): 
            if current_filtration in all_filtrations:
                all_filtrations.remove(current_filtration)
            all_filtrations.append(current_filtration)

    #Shows the previous filtrations
    def find_prev_filtration(self, all_filtrations,current_filtration,system_index):
        if self.check_empty_filtrations(current_filtration): 
            if system_index != 0 and system_index != 1:
                return all_filtrations[system_index - 2]
            
    def is_changed(self, prev_filtration,current_filtration,system_index):
    
        if system_index != 0 and system_index != 1 :
            if current_filtration == prev_filtration:
                return False
            else: 
                return True

    #This functions controls the filtrations are they empyt or not.
    def check_empty_filtrations(self, filtration):
        for index in range(len(filtration)):
            if filtration[index] == '' or filtration[index] == []: 
                return False
            elif index == len(filtration) - 1 and filtration[index] != []:       
                return True
    

    def is_empty(self, selection_name):
        if not selection_name:
            return True

    def remove_temp_csv(self, csv_name):
        if os.path.exists(csv_name):
            os.remove(csv_name)

    def is_driver_alive(self, driver):
        try:
            driver.title
            return True
        except:
            return False
    
    def is_number(self, value):
        try:
            int(value)
            return True
        except (ValueError, TypeError):
            return False

    def main_section(self):
        #placeholder = st.sidebar.empty()
        stop_placeholder = st.empty()
        placeholder = st.empty()
        placeholderStop = st.empty()
        
        if 'all_filtrations' not in st.session_state:
            st.session_state.all_filtrations = []

        selected_brands = st.sidebar.multiselect('Select brands' , self.all_brands)

        selected_models = st.sidebar.multiselect('Select models', self.find_selected_brands_models_for_selection(selected_brands,self.all_model_for_each_brand, self.all_brands))

        selected_fuel_types = st.sidebar.multiselect('Select fuel type', self.all_fuel_options)
        url_type_fuel = self.update_selection_for_fuel(selected_fuel_types)

        selected_gearbox = st.sidebar.multiselect('Select gearbox', self.all_gear_options)
        url_type_gear = self.update_selection_for_gearbox(selected_gearbox)

        selected_mileage_from = st.sidebar.selectbox('Select mileage from', self.mileage_and_power_options)
        selected_mileage_to = st.sidebar.selectbox('Select mileage to', self.mileage_and_power_options)

        selected_power_from = st.sidebar.text_input('Select power from')
        selected_power_to = st.sidebar.text_input('Select power to')

        all_selected_filtrations = [selected_brands,selected_models,selected_fuel_types,selected_gearbox,selected_mileage_to,selected_power_from,selected_power_to]
        

        if 'filtration_completed' not in st.session_state:
            st.session_state['filtration_completed'] = False
        
        if 'data_scraped' not in st.session_state:
            st.session_state['data_scraped'] = False


        #This code block controls the counter of the page
        st.session_state['filtration_completed'] = self.check_empty_filtrations(all_selected_filtrations)

        if 'status' not in st.session_state:
            st.session_state['status'] = False

        if 'stop_button_clicked' not in st.session_state:
            st.session_state['stop_button_clicked'] = False

        filtration_names = ['Brand', 'Model', 'Fuel Type', 'Gearbox', 'Mileage From','Mileage To', 'Power From', 'Power To']
        for index, selection in enumerate(all_selected_filtrations):
            if self.is_empty(selection):
                st.session_state['filtration_completed'] = False
                if not st.session_state['status']:
                    st.warning(f'Please fill in the {filtration_names[index]} field!')
        
        if not self.is_number(selected_power_from) or not self.is_number(selected_power_to):
            if not st.session_state['status']:
                st.warning("Please enter valid numeric values for Power fields!")
                st.session_state['filtration_completed'] = False
        
        if selected_mileage_from and selected_mileage_to:
            try:
                if int(selected_mileage_from) > int(selected_mileage_to):
                    st.warning("Mileage From cannot be greater than Mileage To!")
                    st.session_state['filtration_completed'] = False
            except ValueError:
                pass
        if selected_power_from and selected_power_to:
            try:
                if int(selected_power_from) > int(selected_power_to):
                    st.warning("Power From cannot be greater than Power To!")
                    st.session_state['filtration_completed'] = False
            except ValueError:
                pass
        
        

        self.add_to_all_df(st.session_state.all_filtrations,all_selected_filtrations)

        if self.is_changed(self.find_prev_filtration(st.session_state.all_filtrations,all_selected_filtrations,len(st.session_state.all_filtrations)),all_selected_filtrations,len(st.session_state.all_filtrations)) == True:
            
            
            if 'rerun_in_progress' not in st.session_state:
                st.session_state['rerun_in_progress'] = True  
                st.warning('Please wait...')
                st.session_state['status'] = False
                st.rerun()   
            else:
                st.session_state['rerun_in_progress'] = False  

        if st.sidebar.button('🚀  Start Scraping'):
            if st.session_state['filtration_completed'] == False:
                st.warning('Please complete the filtration!')
            else:
                st.session_state['status'] = True
                st.session_state['data_scraped'] = False
                st.session_state['all_df'] = []

                if os.path.exists('temp_data.csv'):
                    os.remove('temp_data.csv')
                
                    


        if st.session_state['status'] == True and st.session_state['filtration_completed'] == True:
            
            if not st.session_state.get('stop_button_clicked', False):
                
                if stop_placeholder.button('🔴 Stop / Finish'):
                    
                    st.session_state['data_scraped'] = True
                    st.session_state['scraping_completed'] = True
                    st.markdown("<style>.spinner-container { display: none; }</style>", unsafe_allow_html=True)

                    st.session_state['stop_button_clicked'] = True
                    stop_placeholder.empty()  

            else:
                if stop_placeholder.button('Stop / Finish'):
                    # Buton tıklandığında yapılacak işlemler
                    st.session_state['data_scraped'] = True
                    st.session_state['scraping_completed'] = True
                    st.markdown("<style>.spinner-container { display: none; }</style>", unsafe_allow_html=True)

                    st.session_state['stop_button_clicked'] = True
                    stop_placeholder.empty()
                
                
                                   
            self.remove_temp_csv('temp_data.csv')
            
            if st.session_state['status'] == True and st.session_state['data_scraped'] == False:
                
                st.session_state.all_df = []
                
                
                with placeholder.container():
                    st.warning('Process Started...')
                
                
                self.scrap_page_by_page_web(selected_brands,selected_models,0,url_type_fuel, selected_power_from, selected_power_to, selected_mileage_from,selected_mileage_to, url_type_gear,st.session_state['status'], st, self.all_model_for_each_brand, self.all_brands, placeholder)
                
                
                st.session_state['data_scraped'] = True
                placeholder.empty()  
            
            
            if  st.session_state.get('data_scraped', True):
                stop_placeholder.empty()

            if 'all_df' in st.session_state and st.session_state.all_df  and st.session_state['data_scraped'] == True:
                
                combined_df = pd.concat(st.session_state['all_df'], ignore_index=True)
                with placeholder.container():
                    st.write("✅ Scraped Data:")
                    for df in st.session_state['all_df']:
                        self.display_cards(df, st)

                    
                    st.download_button(
                        label="Download CSV",
                        data=combined_df.to_csv(index=False),
                        file_name="Filtered_Data.csv",
                        mime="text/csv"
                    )
                placeholderStop.empty()
                
                
"""                
if __name__ == '__main__':
    main_instance = OnlineData()
    main_section = main_instance.main_section()"""

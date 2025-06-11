import pandas as pd
import streamlit as st
from ScrapElements import ScrapElements 
import numpy as np
from OnlineData import OnlineData
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBRegressor
import re


class Main:
    def __init__(self):
        self.online_data = OnlineData()
        self.brand = None
        self.model = None
        self.mileage = None   
        self.power = None    
        self.fuel_type = None
        self.gearbox = None
        self.scrapElements = ScrapElements()
        self.mileage_and_power_options = self.scrapElements.mileage_and_power_options
        self.all_fuel_options = self.scrapElements.all_fuel_options
        self.all_brands = self.scrapElements.all_brands
        self.all_model_for_each_brand = self.scrapElements.all_model_for_each_brand
        self.df = pd.read_csv("autoscout24.csv")
        self.df = self.preproces_data(self.df)
        self.pipeline = None
        
        
                


    def main(self):
        
     
        st.set_page_config(page_title="Ask the price to the Model!", layout="centered")

     
        st.sidebar.title("Menu ")
        secilen_sayfa = st.sidebar.radio("", ["🎯 Ask to The model", "🔍 Search Car Data"])
   
     
        if secilen_sayfa == "🎯 Ask to The model":
            if 'status_mileage' not in st.session_state:
                st.session_state['status_mileage'] = False
                
            if 'status_power' not in st.session_state:
                st.session_state['status_power'] = False

            st.title("Smart Vehicle Price Estimator ")
            st.write("Select your desired car features below to get started.")
            
        
            col1, col2 = st.columns(2)
            with col1:
                
                self.brand = st.selectbox("Brand", self.all_brands)
                
                try:
                    self.mileage = int(st.text_input("Mileage"))
                    
                    st.session_state['status_mileage'] = True
                except:
                    st.warning("Invalid input for Mileage! ")
                
                
                
            with col2:
                self.model = st.selectbox("Model", self.all_model_for_each_brand[self.all_brands.index(self.brand)])
                
                try:
                    self.power = int(st.text_input("Power"))
                    if self.power < 30:
                        st.warning("Power can be lower than 30 hp ! ")
                    elif self.power > 2000:
                        st.warning("Power can be lower than 2000 hp  ! ")
                    else:
                        st.session_state['status_power'] = True
                except:
                    st.warning("Invalid input for Power! ")

                

            self.gearbox = st.radio("Gearbox", ['Automatic', 'Manuel','Semi-automatic'])
            
            self.fuel_type = st.selectbox("Fuel Type", self.all_fuel_options)

            
            
            if st.button('Predict') and st.session_state['status_mileage'] and st.session_state['status_power']:
                
                brand = self.brand.strip().lower()
                model = self.model.strip().lower()
                

                brand_model_df = self.df[
                    (self.df["brand"].str.strip().str.lower() == brand) &
                    (self.df["model"].str.strip().str.lower() == model)
                ].copy()

                if len(brand_model_df) >= 100:
                    df_train = brand_model_df
                else:
                    df_train = self.df[self.df["brand"].str.lower() == brand]


                
                self.pipeline = self.train_model(df_train)
                pipeline = self.train_model(df_train)

                user_input = pd.DataFrame([{
                    "Fuel type": self.fuel_type,
                    "Gearbox": self.gearbox,
                    "Mileage": self.mileage,
                    "Power": self.power
                }])


                predicted_price = pipeline.predict(user_input)[0]

                

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Predicted Price", f"{int(predicted_price):,} €")
                with col2:
                    st.info(
                        f"""
                        **Car Features:**
                        
                        - Brand: `{self.brand.upper()}`
                        - Model: `{self.model.upper()}`
                        - Fuel Type: `{self.fuel_type}`
                        - Gearbox: `{self.gearbox}`
                        - Mileage: `{self.mileage:,} km`
                        - Power: `{self.power} hp`
                        """
                    )

                    
        elif secilen_sayfa == "🔍 Search Car Data":
            self.online_data.main_section()

    def train_model(self, df):
        X = df[["Fuel type", "Gearbox", "Mileage", "Power"]]
        y = df["price"]
        
        column_transform = ColumnTransformer(transformers=[
            ("fuel", OneHotEncoder(handle_unknown="ignore", sparse_output=False), ["Fuel type"]),
            ("gearbox", OneHotEncoder(handle_unknown="ignore", sparse_output=False), ["Gearbox"]),
            ("num", "passthrough", ["Mileage", "Power"])
        ])

        pipeline = Pipeline([
            ("pre", column_transform),
            ("model", XGBRegressor(
                n_estimators=300,
                max_depth=7,
                learning_rate=0.05,
                random_state=42
            ))
        ])

        pipeline.fit(X, y)
        return pipeline


    def preproces_data(self, df):
        
        
        columns_needed = [
            "price", "Mileage", "Gearbox", "First registration", 
            "Fuel type", "Power", "brand", "model"
        ]
        df_filtered = self.df[columns_needed].copy()
        


        def extract_hp(power_str):
            if isinstance(power_str, str):
                match = re.search(r"\((\d+)\s*hp\)", power_str)
                if match:
                    return int(match.group(1))
            return np.nan
        
        


        
        df_filtered = df_filtered[
            (df_filtered["Mileage"] != "-") &
            (df_filtered["price"] != "-") &
            (df_filtered["Power"] != "-")
        ].copy()

        
        df_filtered["Power"] = df_filtered["Power"].apply(extract_hp)

        df_filtered["Mileage"] = (
            df_filtered["Mileage"]
            .astype(str)
            .str.replace(".", "", regex=False)
            .str.replace(" km", "", regex=False)
            .str.replace(",", "", regex=False)
            .astype(float)
        )

        df_filtered["registration_year"] = (
            df_filtered["First registration"]
            .astype(str)
            .str.extract(r"(\d{4})")
            .astype(float)
        )

        df_filtered["price"] = pd.to_numeric(df_filtered["price"], errors="coerce")


        

       
        df_clean = df_filtered.drop(columns=["First registration"])
        
        df_filtered = df_clean[
            (df_clean["price"] >= 1000) & (df_clean["price"] <= 150000)
        ]
        df_filtered.dropna(inplace=True)

        return df_filtered

                
if __name__ == '__main__':
    main_instance = Main()
    main_instance.main()

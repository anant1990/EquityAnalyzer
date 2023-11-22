import streamlit as st
import datetime as dt
import pandas as pd
from PIL import Image
import yfinance as yf
import requests
from bs4 import BeautifulSoup

headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'}

def scrape_stock_data(ticker):
    """Scrapes stock data from Yahoo Finance.

    Args:
        ticker: The ticker symbol of the company to scrape data for.

    Returns:
        A Pandas DataFrame object containing the stock data.
    """

    # Get the company's stock data from Yahoo Finance.
    stock_data = yf.Ticker(ticker).history(period='1d')

    # Return the stock data as a Pandas DataFrame object.
    return stock_data

def calculate_dcf(ticker, growth_rate):

    stock_cf = yf.Ticker(ticker).cashflow
    cashflow_df = pd.DataFrame(stock_cf)

    # Most recent free cash flow
    free_cash_flow = (cashflow_df.loc['Free Cash Flow'][0] + cashflow_df.loc['Free Cash Flow'][1] + cashflow_df.loc['Free Cash Flow'][2])/3
    st.write("Average cashflow for projection is:", free_cash_flow)

    # Calculate the present value of the FCFs.
    pv_of_fcfs = 0
    pv_of_lcf = 0
    for year in range(1, 10):
        pv_of_fcfs += ((free_cash_flow) * ((1 + growth_rate) ** (year - 1))) / (1 + 0.08) ** year
        pv_of_lcf = (free_cash_flow) * ((1 + growth_rate) ** (year - 1))
        #st.write(((free_cash_flow) * ((1 + growth_rate) ** (year - 1)))/1000000)

    # Calculate the terminal value of the FCFs.
    # terminal_value = free_cash_flow * (1 + growth_rate) ** 9 / (0.1 - growth_rate)
    terminal_value = (pv_of_lcf)/((growth_rate - 0.02)*((1+0.1) ** 9))

    # Calculate the total DCF. (Enterprise value)
    dcf = pv_of_fcfs + terminal_value

    cash_casheq = pd.DataFrame(yf.Ticker(ticker).balance_sheet).loc['Cash And Cash Equivalents'][0]
    total_debt = pd.DataFrame(yf.Ticker(ticker).balance_sheet).loc['Total Debt'][0]
    equity_value = dcf + cash_casheq - total_debt

    total_shares = pd.DataFrame(yf.Ticker(ticker).balance_sheet).loc['Share Issued'][0]

    instrinsic_value = equity_value/(total_shares)

    st.write("Calculated Instrinsic Value through the DCF method is:", instrinsic_value)

    return instrinsic_value

def eps_valuation(ticker, ttm_eps, growth_rate, growth_decline_rate):

    final_eps_val = 0.00
    final_eps_val = ttm_eps * (1 + growth_rate)
    for year in range(1,5):
        final_eps_val = final_eps_val * (1 + (growth_rate * ((1 - growth_decline_rate)**(year-1))))
        #st.write("EPS in Y", year+1, ":", final_eps_val)
    
    # st.write(yf.Ticker(ticker).info)
    st.write("Get Forward P/E")
    st.write(get_forward_pe_from_website(ticker))
    st.write(get_epsttm_from_website(ticker))

    #Projected Value
    final_eps_val = final_eps_val * (get_forward_pe_from_website(ticker))

    #Discounting to present value
    final_eps_val = final_eps_val/((1+0.1)**(year+1))

    return final_eps_val

def get_forward_pe_from_website(ticker):
    try:
        # Replace 'URL' with the actual URL of the website providing forward P/E information
        url = f'https://finance.yahoo.com/quote/{ticker}/key-statistics'

        # Send a GET request to the URL
        response = requests.get(url, headers=headers, timeout=5)

        st.write("Response status code: ", response)
        st.write("URL is:", url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            st.write("Hello")

            # Locate the element containing the forward P/E ratio
            forward_pe_element = soup.find('div', {'class': 'D(ib) W(1/2) Bxz(bb) Pstart(12px) Va(t) ie-7_D(i) ie-7_Pos(a) smartphone_D(b) smartphone_W(100%) smartphone_Pstart(0px) smartphone_BdB smartphone_Bdc($seperatorColor)'}).find_all('td', {'class':'Ta(end) Fw(600) Lh(14px)'})[2].text
            st.write("Forward P/E Element")
            st.write(forward_pe_element)

            # Extract the forward P/E ratio
            forward_pe_ratio = float(forward_pe_element)

            #st.write(forward_pe_ratio)
            return forward_pe_ratio

        else:
            print(f"Failed to fetch data. Status Code: {response.status_code}")
            return None

    except Exception as e:
        print(f"Error: {e}")
        return None

def get_epsttm_from_website(ticker):
    try:
        # Replace 'URL' with the actual URL of the website providing eps ttm information
        url = f'https://finance.yahoo.com/quote/{ticker}'

        # Send a GET request to the URL
        response = requests.get(url, headers=headers, timeout=5)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            # Locate the element containing the ttm eps
            epsttm_element = soup.find('div', {'class': 'D(ib) W(1/2) Bxz(bb) Pstart(12px) Va(t) ie-7_D(i) ie-7_Pos(a) smartphone_D(b) smartphone_W(100%) smartphone_Pstart(0px) smartphone_BdB smartphone_Bdc($seperatorColor)'}).find_all('td', {'class':'Ta(end) Fw(600) Lh(14px)'})[3].text
            #st.write(epsttm_element)

            # Extract the forward P/E ratio
            epsttm = float(epsttm_element)

            #st.write(epsttm)
            return epsttm

        else:
            print(f"Failed to fetch data. Status Code: {response.status_code}")
            return None

    except Exception as e:
        print(f"Error: {e}")
        return None

def get_marketcap_from_website(ticker):
    try:
        # Replace 'URL' with the actual URL of the website providing eps ttm information
        url = f'https://finance.yahoo.com/quote/' + ticker + '/key-statistics'

        # Send a GET request to the URL
        response = requests.get(url, headers=headers, timeout=5)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            # Locate the price of the ticker
            current_market_cap_text = soup.find('div', {'class': 'Pos(r) Mt(10px)'}).find_all('td', {'class':'Fw(500) Ta(end) Pstart(10px) Miw(60px)'})[0].text
            #current_market_cap = float(current_market_price_text)
            st.write(current_market_cap_text)

            current_market_price_text = soup.find('div', {'class': 'D(ib) Mend(20px)'}).find('fin-streamer', {'class':'Fw(b) Fz(36px) Mb(-4px) D(ib)'}).text
            current_market_price = float(current_market_price_text)
            st.write(current_market_price)

            #st.write(epsttm)
            return current_market_cap_text

        else:
            print(f"Failed to fetch data. Status Code: {response.status_code}")
            return None

    except Exception as e:
        print(f"Error: {e}")
        return None

def display_dcf(dcf):

  # Display the DCF of the stock to the user.
  st.write(f"The DCF of the stock is: {dcf:.2f}")

# Get the ticker symbol from the user.
ticker = st.text_input("Enter a ticker symbol: ")
growth_rate = st.number_input("Enter the growth rate: ")
growth_decline_rate = st.number_input("Enter the growth decline rate: ")

# Scrape the stock data for the specified ticker.
stock_df = scrape_stock_data(ticker)

# Display the stock data to the user.
st.write(stock_df)

# Calculate DCF for the specified ticker.
stock_dcf = calculate_dcf(ticker, growth_rate)

ttm_eps = get_epsttm_from_website(ticker)
eps_val = eps_valuation(ticker, ttm_eps, growth_rate, growth_decline_rate)

#st.write("EPS value obtained with inputs is:", eps_val)
st.divider()
col1, col2 = st.columns(2)

with col1:
    st.subheader("DCF (Intrinsic)")
    st.title("%.2f" %stock_dcf)

with col2:
    st.subheader("P/E (Relative)")
    st.title("%.2f" %eps_val)

st.divider()

# col1.metric("DCF (Intrinsic)", "%.2f" %stock_dcf)
# col2.metric("P/E (Relative)", "%.2f" %eps_val)

import sqlite3
import hashlib
import streamlit as st
import pandas as pd

# Function to create a user table
def create_user_table():
    conn = sqlite3.connect('users.db')  # Specify the path if needed
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Function to create a user in the database
def create_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hash_password(password)))
        conn.commit()
        st.success("User  created successfully! You can now log in.")
    except sqlite3.IntegrityError:
        st.error("Username already exists.")
    except Exception as e:
        st.error(f"An error occurred: {e}")
    finally:
        conn.close()

# Function to verify user credentials
def verify_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username=? AND password=?', (username, hash_password(password)))
    user = c.fetchone()
    conn.close()
    return user is not None

# Create the user table at the start of the app
create_user_table()

# Streamlit app layout
st.title("Dealer Price Lookup")

# Session state to keep track of logged-in user
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# Login page
if not st.session_state.logged_in:
    st.header("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type='password')

    if st.button("Login"):
        if verify_user(username, password):
            st.session_state.logged_in = True  # Set logged-in state
            st.success("Logged in successfully!")
        else:
            st.error("Invalid username or password")

    # Button to show the sign-up section
    if st.button("Create an Account"):
        st.session_state.show_signup = True

    # Sign-Up Section
    if 'show_signup' not in st.session_state:
        st.session_state.show_signup = False

    if st.session_state.show_signup:
        st.header("Sign Up")
        new_username = st.text_input("New Username")
        new_password = st.text_input("New Password", type='password')

        if st.button("Sign Up"):
            if new_username and new_password:
                create_user(new_username, new_password)
                st.session_state.show_signup = False  # Hide sign-up section after successful sign-up
            else:
                st.warning("Please enter a username and password.")
# Load the Excel file
@st.cache_data
def load_data():
    try:
        data = pd.read_excel('dealer_prices.xlsx')
        st.success("Data loaded successfully!")
        return data
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()  # Return an empty DataFrame on error

# Function to get unique products based on the model
def get_unique_products(model, data):
    # Filter data based on the model
    filtered_data = data[data['product_complete_name'].str.contains(model, case=False, na=False)]

    if not filtered_data.empty:
        # Group by 'brand' and 'cat' to find the minimum price
        min_prices = filtered_data.groupby(['brand', 'cat'])['price'].min().reset_index()
        min_prices.rename(columns={'price': 'min_price'}, inplace=True)

        # Merge to keep only those products that have the minimum price
        unique_products = filtered_data.merge(min_prices, on=['brand', 'cat'])
        unique_products = unique_products[unique_products['price'] == unique_products['min_price']]

        # Drop the 'min_price' column as it's no longer needed
        unique_products.drop(columns=['min_price'], inplace=True)

        return unique_products

    return pd.DataFrame()  # Return an empty DataFrame if no matches found

# Load data
data = load_data()

# Search page
if st.session_state.logged_in:
    st.header("Floor Price Search Engine")
    search_model = st.text_input("Enter Product Model")

    if st.button("Search"):
        if search_model:  # Check if the search model is not empty
            unique_products = get_unique_products(search_model, data)
            if not unique_products.empty:
                st.write("### Unique Products Found:")
                st.dataframe(unique_products)  # Display the unique products
            else:
                st.warning("No products found for the specified model.")
        else:
            st.warning("Please enter a model to search.")
def get_all_users():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT username FROM users')
    users = c.fetchall()  # Fetch all user records
    conn.close()
    return users
if st.session_state.logged_in:
    st.header("User  List")
    # Assuming you have a way to check if the user is an admin
    if username == "rezazo":  # Replace with your admin check logic
        users = get_all_users()
        st.write("### Registered Users:")
        if users:
            st.dataframe(pd.DataFrame(users, columns=["Username"]))
        else:
            st.write("No users found.")
    else:
        st.warning("You do not have permission to view the user list.")

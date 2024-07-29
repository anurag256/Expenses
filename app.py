import streamlit as st
import pandas as pd
import sqlite3
import bcrypt
import os
import io


# Create a directory to store user data
employee_data = 'database/userdata/employee.db'
if not os.path.exists(employee_data):
    os.makedirs(employee_data)

# Function to hash passwords
def hash_password(password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password

# Function to verify passwords
def verify_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password)

# Registration page
def register():
    st.title("Register")
    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    if st.button("Register"):
        if password == confirm_password:
            hashed_password = hash_password(password)
            # Create a new database file for the user
            with sqlite3.connect(employee_data) as conn:
                cursor = conn.cursor()
                cursor.execute(f'''CREATE TABLE IF NOT EXISTS {username} (
                                    id INTEGER PRIMARY KEY,
                                    VisitDate DATE,
                                    InTime TIME,
                                    OutTime TIME,
                                    VisitPlace TEXT,
                                    TravelBy TEXT,
                                    Expance INTEGER)''')
                conn.commit()
            with sqlite3.connect("user.db") as user_con:
                cur = user_con.cursor()
                try:
                    cur.execute(f"INSERT INTO users (uid, email, password) VALUES (?, ?, ?)", (username, email, hashed_password))
                    user_con.commit()
                except Exception as e:
                    print(f"User Auth not saved due to {e}")
            st.success("Account created successfully!")
        else:
            st.error("Passwords do not match")

# Login page
def login():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        try:
            if os.path.exists(employee_data):
                with sqlite3.connect("user.db") as conn:
                    cursor = conn.cursor()
                    user = cursor.execute("SELECT * FROM users WHERE uid=?", (username,)).fetchone()
                    if user:
                        if verify_password(password, user[2]):
                            st.session_state.logged_in = True
                            st.session_state.username = username  # Initialize username here
                            st.rerun()
                        else:
                            st.error("Invalid password")
                    else:
                        st.error("User not found")
            else:
                st.error("User not found")
        except Exception as e:
            print(e)

# Main page
def main():
    st.title("Employee Expanse Data")
    df = ''
    if 'username' not in st.session_state:
        st.session_state.username = None
    username = st.session_state.username

    # Create a form to input data
    dateOfVisit = st.date_input("Select Date")
    timein = st.time_input("InTime")
    timeout = st.time_input("OutTime")
    visitedPlace = st.text_input("VisitedPlace")
    travelVia = st.text_input("Travel By")
    expance = st.number_input("Total Expance")

    # Save the data to the database
    with sqlite3.connect(employee_data) as conn:
        if st.button("Submit"):
            conn.execute(f"INSERT INTO {username} (VisitDate, InTime, OutTime, VisitPlace, TravelBy, Expance) VALUES (?, ?, ?, ?, ?, ?)", (dateOfVisit, timein.strftime("%H:%M:%S"), timeout.strftime("%H:%M:%S"), visitedPlace, travelVia, expance))
            conn.commit()
        # Display the data
        try:
            df = pd.read_sql_query(f"SELECT * FROM {username}", conn)
            st.dataframe(df)
        except Exception as e:
            print(e)

        # Add a download button
        try:
            buffer = io.BytesIO()
            df.to_excel(buffer, index=False)
            buffer.seek(0)

            st.download_button(
                label="Download data as Excel",
                data=buffer.getvalue(),
                file_name=f'{username}_data.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        except Exception as e:
            print(e)

# Navigation
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    page = st.selectbox("Select a page", ["Login", "Register"])
    if page == "Login":
        login()
    elif page == "Register":
        register()
else:
    main()
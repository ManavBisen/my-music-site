# main_app.py
import streamlit as st
import time
import datetime
import os
import base64
from collections import defaultdict

# Initialize session state
if 'users' not in st.session_state:
    st.session_state.users = {}
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'shop_items' not in st.session_state:
    st.session_state.shop_items = []
if 'daily_tasks' not in st.session_state:
    st.session_state.daily_tasks = defaultdict(dict)

# User class
class User:
    def __init__(self, username, password, secret_code=None):
        self.username = username
        self.password = password
        self.title = "None"
        self.level = 0
        self.xp = 0
        self.total_xp = 0
        self.profile_pic = None
        self.inventory = []
        self.is_superuser = secret_code == "shadow_monarch"
        self.required_xp = 10
        self.last_task_date = None

    def update_level(self):
        while self.xp >= self.required_xp:
            self.xp -= self.required_xp
            self.level += 1
            if self.required_xp < 60:
                self.required_xp += 1
            else:
                self.required_xp = 60
            self.update_title()
            st.toast(f"Level Up! Now Level {self.level}", icon="🎉")

    def update_title(self):
        if self.level >= 10:
            self.title = "Valedictorian"
        elif self.level >= 5:
            self.title = "Vessel of the Monarch"
        elif self.level >= 1:
            self.title = "Player"

# Authentication functions
def register():
    with st.form("Register"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        secret_code = st.text_input("Secret Code (optional)", type="password")
        submitted = st.form_submit_button("Register")

        if submitted:
            if username in st.session_state.users:
                st.error("Username exists!")
            else:
                new_user = User(username, password, secret_code)
                st.session_state.users[username] = new_user
                st.success("Registered!")

def login():
    with st.form("Login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            user = st.session_state.users.get(username)
            if user and user.password == password:
                st.session_state.current_user = user
                st.rerun()
            else:
                st.error("Invalid credentials")

# Home Page
def home_page():
    user = st.session_state.current_user
    st.title("Solo Leveling")

    # Profile Section
    col1, col2 = st.columns([1,3])
    with col1:
        # if user.profile_pic:
        #     st.image(user.profile_pic, width=100)
        # else:
        #     st.file_uploader("Upload Profile Picture", type=["png", "jpg"], key="profile_upload")
        st.header("Profile")
        
    with col2:
        st.subheader(f"Username- {user.username}")
        # st.write(f"Username: {user.username}")
        st.subheader(f"Title- {user.title}")
        st.subheader(f"Level: {user.level}")
        st.subheader(f"XP: {user.xp}/{user.required_xp}")
        progress = user.xp / user.required_xp
        st.progress(progress)

    # Timer Section
    if 'start_time' not in st.session_state:
        st.session_state.start_time = None

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Start Timer"):
            st.session_state.start_time = time.time()
            st.toast("Work started! 🚀")
    with col2:
        if st.button("Stop Timer"):
            if st.session_state.start_time:
                elapsed = time.time() - st.session_state.start_time
                minutes = elapsed // 60
                user.xp += minutes
                user.total_xp += minutes
                if minutes >= 60:
                    user.xp += 10
                    user.total_xp += 10
                user.update_level()
                st.session_state.start_time = None
                st.toast(f"Earned {minutes} XP! 💰")

    # Display timer
    if st.session_state.start_time:
        elapsed = time.time() - st.session_state.start_time
        st.write(f"Elapsed time: {str(datetime.timedelta(seconds=int(elapsed)))}")

# Shop Page
def shop_page():
    st.title("Shop")
    user = st.session_state.current_user

    if user.is_superuser:
        with st.form("Add Item"):
            item_name = st.text_input("Item Name")
            item_file = st.file_uploader("Upload Item")
            price = st.number_input("Price (XP)", min_value=1)
            min_title = st.selectbox("Minimum Title", ["Player", "Vessel of the Monarch", "Valedictorian"])
            submitted = st.form_submit_button("Add Item")

            if submitted:
                st.session_state.shop_items.append({
                    "name": item_name,
                    "file": item_file,
                    "price": price,
                    "min_title": min_title
                })

    for item in st.session_state.shop_items:
        col1, col2 = st.columns([3,1])
        with col1:
            st.write(f"{item['name']} - {item['price']} XP")
            st.write(f"Requires: {item['min_title']}")
        with col2:
            if user.title >= item['min_title'] and user.xp >= item['price']:
                if st.button(f"Buy {item['name']}"):
                    user.xp -= item['price']
                    user.inventory.append(item)
                    st.success("Purchased!")

# Inventory Page
def inventory_page():
    st.title("Inventory")
    user = st.session_state.current_user

    for item in user.inventory:
        col1, col2 = st.columns([3,1])
        with col1:
            st.write(item['name'])
        with col2:
            if item['file']:
                st.download_button(
                    label="Download",
                    data=item['file'].getvalue(),
                    file_name=item['name']
                )

# Leaderboard Page
def leaderboard_page():
    st.title("Leaderboard")
    users = sorted(st.session_state.users.values(), key=lambda x: x.level, reverse=True)[:10]

    for i, user in enumerate(users):
        st.write(f"{i+1}. {user.username} - Level {user.level} ({user.title})")

# Daily Tasks Page
def daily_tasks_page():
    st.title("Daily Tasks")
    user = st.session_state.current_user

    # Check if new day
    today = datetime.date.today()
    if user.last_task_date != today:
        user.last_task_date = today
        st.session_state.daily_tasks[user.username] = {
            'study': False,
            'exercise': False,
            'reading': False
        }

    tasks = st.session_state.daily_tasks[user.username]

    # Study Task
    with st.expander("40 Minutes Study"):
        if st.button("Start Study Timer"):
            # Timer implementation similar to home page
            pass
        if tasks['study']:
            st.success("Completed!")

    # Exercise Task
    tasks['exercise'] = st.checkbox("Completed 50 Push-ups & Squats")

    # Reading Task
    tasks['reading'] = st.checkbox("Read One Book Page")

    if st.button("Submit Tasks"):
        completed = sum(tasks.values())
        if completed == 3:
            user.xp += 180
        elif completed == 0:
            user.xp -= 30
        elif completed == 1:
            user.xp -= 10
        user.update_level()

# Challenge Page
def challenge_page():
    st.title("Challenge")
    if st.button("Start 3-Hour Challenge"):
        # Challenge timer implementation
        pass
    if st.checkbox("I completed the challenge"):
        user = st.session_state.current_user
        user.xp += 250
        user.update_level()

# Main App
def main():
    st.sidebar.title("Navigation")
    pages = {
        "Home": home_page,
        "Shop": shop_page,
        "Inventory": inventory_page,
        "Leaderboard": leaderboard_page,
        "Daily Tasks": daily_tasks_page,
        "Challenge": challenge_page
    }

    if not st.session_state.current_user:
        page = st.sidebar.selectbox("Menu", ["Login", "Register"])
        if page == "Login":
            login()
        else:
            register()
    else:
        selection = st.sidebar.selectbox("Go to", list(pages.keys()))
        pages[selection]()
        if st.sidebar.button("Logout"):
            st.session_state.current_user = None
            st.rerun()

if __name__ == "__main__":
    main()
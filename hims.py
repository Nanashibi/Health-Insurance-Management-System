# Trial_App.py with Data Visualisation under report & analytics 
import streamlit as st
import pymysql
from pymysql import OperationalError
import base64

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
from datetime import datetime

# Initialize the total premium variable globally
total_premium_collected = 0

# Initialize the total claims approved variable globally
total_claims_approved = 0

# Database connection function
def create_connection():
    try:
        connection = pymysql.connect(
            host="localhost",
            user="root",
            password="pwd",
            database="HealthInsuranceDB"
        )
        return connection
    except OperationalError as e:
        st.error(f"Database connection error: {e}")
        return None

# Function to encode the image to base64
def get_base64_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

# Function to set page style with conditional background
def set_page_style(background_image_path):
    base64_image = get_base64_image(background_image_path)
    page_bg = f"""
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{base64_image}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        color: #333;
        height: 5500px;
    }}
    
    /* Style adjustments for various elements */
    h1 {{
        font-family: 'Arial', sans-serif;
        color: #004466;
        text-align: center;
        font-size: 3rem;
        padding: 1.5rem 0;
    }}

    h2, h3 {{
        color: #006699;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }}

    .stTextInput, .stNumberInput, .stTextArea {{
        font-size: 1.1rem;
        color: #333;
    }}
    
    .stButton > button {{
        background-color: #008080;
        color: white;
        font-size: 1.1rem;
        padding: 0.5rem 1rem;
        border: none;
        border-radius: 5px;
    }}
    
    .stButton > button:hover {{
        background-color: #004d4d;
        color: #ffffff;
    }}
    
    .st-alert {{
        color: #004466;
    }}

    /* Add semi-transparent background to main content */
    .block-container {{
        background-color: rgba(255, 255, 255, 0.85);  /* 0.85 is the opacity - adjust as needed */
        padding: 2rem;
        border-radius: 10px;
        min-height: 100vh;
        height: auto;
        display: flex; /* Use flexbox for alignment */
        flex-direction: column; /* Arrange elements vertically */
        justify-content: flex-start; /* Align content to start */
    }}

    /* Make sure elements inside maintain good contrast */
    .block-container * {{
        color: #333;
    }}

    /* Ensure header text remains visible */
    .block-container h1, .block-container h2, .block-container h3 {{
        color: #004466;
    }}

    

    /* Style success/error messages */
    .stSuccess, .stError {{
        background-color: rgba(255, 255, 255, 0.9);
    }}
    </style>
    """
    st.markdown(page_bg, unsafe_allow_html=True)

# Apply the appropriate background based on login state
if st.session_state.get("logged_in", False):
    set_page_style("HomePageBackground.png")  # Post-login background
else:
    set_page_style("LoginPageBackground.png")   # Login/registration background

def register_user(username, password):
    conn = create_connection()
    if conn is None:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, 'policy_holder')", (username, password))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error during registration: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def login(username, password):
    conn = create_connection()
    if conn is None:
        return None, None
    
    cursor = conn.cursor()
    cursor.execute("SELECT role, user_id FROM users WHERE username = %s and password = %s", (username, password))
    result = cursor.fetchone()
    conn.close()

    if result:
        return result[0], result[1]  # Return user role and user ID
    else:
        return None, None
   
# Add new policy holder
def add_policy_holder(name, age, contact, address):
    conn = create_connection()
    if conn is None:
        return
    
    cursor = conn.cursor()
    cursor.execute("INSERT INTO policy_holders (name, age, contact, address) VALUES (%s, %s, %s, %s)",
                   (name, age, contact, address))
    conn.commit()
    conn.close()
    st.success("Policy holder added successfully.")

# View all policy holders
def view_policy_holders():
    conn = create_connection()
    if conn is None:
        return []
    
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM policy_holders")
    policy_holders = cursor.fetchall()
    conn.close()
    return policy_holders

# Add new policy
def add_policy(policy_name, policy_details, premium):
    conn = create_connection()
    if conn is None:
        return
    
    cursor = conn.cursor()
    cursor.execute("INSERT INTO policies (policy_name, policy_details, premium) VALUES (%s, %s, %s)",
                   (policy_name, policy_details, premium))
    conn.commit()
    conn.close()

# Update existing policy
def update_policy(policy_id, policy_name, premium, coverage_amount):
    conn = create_connection()
    if conn is None:
        return
    
    cursor = conn.cursor()
    cursor.execute("UPDATE policies SET policy_name=%s, premium=%s, coverage_amount=%s WHERE policy_id=%s",
                   (policy_name, premium, coverage_amount, policy_id))
    conn.commit()
    conn.close()
    st.success("Policy updated successfully.")

# Premium calculation (based on coverage and age factors for simplicity)
def calculate_premium(coverage_amount, age):
    base_rate = 0.05
    age_factor = 1.2 if age > 45 else 1.0
    premium = coverage_amount * base_rate * age_factor
    return premium

def get_policy_holder_id(user_id):
    conn = create_connection()
    if conn is None:
        return None
    
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM policy_holders WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else None

def view_policies():
    conn = create_connection()
    if conn is None:
        return []
    
    cursor = conn.cursor()
    cursor.execute("SELECT policy_id, policy_name, policy_details, premium FROM policies")
    policies = cursor.fetchall()
    conn.close()
    return policies

def buy_policy(user_id, policy_id, name, age, contact, address):
    conn = create_connection()
    if conn is None:
        return False

    try:
        cursor = conn.cursor()

        # Check if the policy holder already exists
        cursor.execute("""
            SELECT id FROM policy_holders WHERE user_id = %s
        """, (user_id,))
        existing_policy_holder = cursor.fetchone()

        # If policy holder exists, use their ID; otherwise, insert new record
        if existing_policy_holder:
            policy_holder_id = existing_policy_holder[0]
        else:
            # Insert new policy holder
            cursor.execute("""
                INSERT INTO policy_holders (user_id, name, age, contact, address) 
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, name, age, contact, address))
            policy_holder_id = cursor.lastrowid  # Get the newly inserted policy holder ID
        
          # Fetch the premium amount for the selected policy
        cursor.execute("""
            SELECT premium FROM policies WHERE policy_id = %s
        """, (policy_id,))
        premium_amount = cursor.fetchone()[0]

        # Update the total premium collected
        global total_premium_collected
        total_premium_collected += premium_amount

        # Add to policy_purchases
        cursor.execute("""
            INSERT INTO policy_purchases (user_id, policy_id)
            VALUES (%s, %s)
        """, (user_id, policy_id))

        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error purchasing policy: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# Add this new function to get user's purchased policies and latest purchased policy (Nested Query)
def get_user_policies(user_id):
    conn = create_connection()
    if conn is None:
        return []

    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.policy_id, p.policy_name, p.policy_details, p.premium,
            (SELECT MAX(pp.purchase_date) 
             FROM policy_purchases pp 
             WHERE pp.policy_id = p.policy_id AND pp.user_id = %s) AS latest_purchase_date
        FROM policies p
        WHERE p.policy_id IN (
            SELECT pp.policy_id
            FROM policy_purchases pp
            WHERE pp.user_id = %s
        )
        ORDER BY latest_purchase_date DESC
    """, (user_id, user_id))
    
    policies = cursor.fetchall()
    conn.close()
    return policies

def delete_policy(policy_id):
    conn = create_connection()
    if conn is None:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM policies WHERE policy_id = %s", (policy_id,))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error deleting policy: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# Submit a claim
def submit_claim(policy_holder_id, claim_amount, description):
    conn = create_connection()
    if conn is None:
        return
    
    cursor = conn.cursor()
    cursor.execute("INSERT INTO claims (policy_holder_id, claim_amount, description, status) VALUES (%s, %s, %s, %s)",
                   (policy_holder_id, claim_amount, description, 'Pending'))
    conn.commit()
    conn.close()
    st.success("Claim submitted successfully.")

# Process claim by admin
def process_claim(claim_id, action):
    conn = create_connection()
    if conn is None:
        return
    
    cursor = conn.cursor()
    status = 'Approved' if action == 'approve' else 'Rejected'
    cursor.execute("UPDATE claims SET status = %s WHERE claim_id = %s", (status, claim_id))
    conn.commit()
    conn.close()
    st.success(f"Claim {status} successfully.")

# View claims for processing by admin
def view_claims():
    conn = create_connection()
    if conn is None:
        return
    
    cursor = conn.cursor()
    cursor.execute("SELECT claim_id, policy_holder_id, claim_amount, description, status FROM claims WHERE status = 'Pending'")
    pending_claims = cursor.fetchall()
    
    if pending_claims:
        for claim in pending_claims:
            claim_id, policy_holder_id, claim_amount, description, status = claim
            
            st.write(f"Claim ID: {claim_id}")
            st.write(f"Policy Holder ID: {policy_holder_id}")
            st.write(f"Claim Amount: {claim_amount}")
            st.write(f"Description: {description}")
            st.write(f"Status: {status}")
            
            # Buttons to approve or reject the claim
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Approve Claim {claim_id}", key=f"approve_{claim_id}"):
                    update_claim_status(claim_id, 'Approved')
            with col2:
                if st.button(f"Reject Claim {claim_id}", key=f"reject_{claim_id}"):
                    update_claim_status(claim_id, 'Rejected')
            st.markdown("---")
    else:
        st.info("No pending claims.")
    
    conn.close()

# Update claim status and track approved claim amount
def update_claim_status(claim_id, new_status, claim_amount):
    global total_claims_approved
    conn = create_connection()
    if conn is None:
        return
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE claims SET status = %s WHERE claim_id = %s
        """, (new_status, claim_id))

        if new_status == 'Approved':
            # Update the total claims approved
            total_claims_approved += claim_amount
        
        conn.commit()
    except Exception as e:
        st.error(f"Error updating claim status: {e}")
        conn.rollback()
    finally:
        conn.close()

# Update claim status function
def update_claim_status(claim_id, new_status):
    conn = create_connection()
    if conn is None:
        return
    
    cursor = conn.cursor()
    cursor.execute("UPDATE claims SET status = %s WHERE claim_id = %s", (new_status, claim_id))
    conn.commit()
    conn.close()
    st.success(f"Claim {claim_id} has been {new_status.lower()}.")

# Retrieve claims submitted by a policy holder
def get_policy_holder_claims(policy_holder_id):
    conn = create_connection()
    if conn is None:
        return []

    cursor = conn.cursor()
    cursor.execute("""
        SELECT claim_id, claim_amount, description, status
        FROM claims
        WHERE policy_holder_id = %s
        ORDER BY claim_id DESC
    """, (policy_holder_id,))
    
    claims = cursor.fetchall()
    conn.close()
    return claims

# Generate reports and analytics
def generate_reports():
    conn = create_connection()
    if conn is None:
        return
    
    cursor = conn.cursor()
    
    # Report: Total policies
    cursor.execute("SELECT COUNT(*) FROM policies")
    total_policies = cursor.fetchone()[0]
    
    # Report: Total claims submitted and approved
    cursor.execute("SELECT COUNT(*) FROM claims WHERE status = 'Approved'")
    approved_claims = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM claims")
    total_claims = cursor.fetchone()[0]
    
    # Report: Total premium collected
    cursor.execute("SELECT SUM(premium) FROM policies")
    total_premium_collected = cursor.fetchone()[0] or 0.0

    # Report: Total claims approved (sum of approved claim amounts)
    cursor.execute("SELECT SUM(claim_amount) FROM claims WHERE status = 'Approved'")
    total_claims_approved = cursor.fetchone()[0] or 0.0

    # Report: Total policies sold by category
    cursor.execute("SELECT policy_name, COUNT(*) FROM policy_purchases p JOIN policies pol ON p.policy_id = pol.policy_id GROUP BY policy_name")
    policies_data = cursor.fetchall()
    policies_df = pd.DataFrame(policies_data, columns=["Policy Name", "Number of Policies Sold"])

    # Plot: Number of Policies Sold
    st.subheader("Number of Policies Sold by Category")
    fig1 = px.bar(policies_df, x="Policy Name", y="Number of Policies Sold", title="Number of Policies Sold by Category")
    st.plotly_chart(fig1)

    # Plot: Relationship between Total Premium Collected and Total Claims Approved (without time constraint)
    st.subheader("Total Premium Collected vs. Total Claims Approved")
    
    # Create a DataFrame for plotting
    relationship_df = pd.DataFrame({
        "Category": ["Total Premium Collected", "Total Claims Approved"],
        "Amount": [total_premium_collected, total_claims_approved]
    })

    # Create a bar chart
    fig2 = px.bar(relationship_df, x="Category", y="Amount", color="Category", title="Total Premium Collected vs. Total Claims Approved")
    st.plotly_chart(fig2)

    conn.close()
    
    st.write(f"Total Policies: {total_policies}")
    st.write(f"Total Claims Submitted: {total_claims}")
    st.write(f"Total Claims Approved: {approved_claims}")
    st.write(f"Total Premium Collected: {total_premium_collected}")
    st.write(f"Total Claims Approved (Amount): {total_claims_approved}")

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.user_id = None
    st.session_state.policy_holder_id = None

if 'registration_mode' not in st.session_state:
    st.session_state.registration_mode = False

# UI for the Health Insurance Management System
st.markdown("<h1 style='text-align: center;font-weight: bold;'>Health Insurance Management System</h1>", unsafe_allow_html=True)

# Display login or registration based on the session state
if not st.session_state.logged_in:
    if st.session_state.registration_mode:
        # Registration section
        st.header("New User Registration")
        reg_username = st.text_input("Register Username", key="register_username_unique")
        reg_password = st.text_input("Register Password", type="password", key="register_password_unique")
        if st.button("Register", key="register_button_unique"):
            if register_user(reg_username, reg_password):
                st.success("Registration successful. You can now log in.")
                st.session_state.registration_mode = False
                st.rerun()
            else:
                st.error("Registration failed.")
        
        if st.button("Back to Login"):
            st.session_state.registration_mode = False
            st.rerun()
    else:
        # Login section
        st.header("Login")
        login_username = st.text_input("Username", key="login_username_unique")
        login_password = st.text_input("Password", type="password", key="login_password_unique")
        container = st.container()
        col1, col2 = container.columns([5, 1.5], gap="large")

        with col1:
            if st.button("Login", key="login_button_unique"):
                role, user_id = login(login_username, login_password)
                if role:
                    st.session_state.logged_in = True
                    st.session_state.role = role
                    st.session_state.user_id = user_id
                    st.success(f"Logged in as {role}")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

        with col2:
            if st.button("Registration"):
                st.session_state.registration_mode = True
                st.rerun()

else:
    st.success("Welcome to the Health Insurance Management System!")

# Main Application
if st.session_state.logged_in:
    role = st.session_state.role
    
    # Admin specific functions
    if role == 'admin':
        st.header("Available Policies")
        policies = view_policies()
        
        for policy in policies:
            policy_id, name, policy_details, premium = policy
            st.write(f"*{name}*")
            st.write(f"Details: {policy_details}")
            st.write(f"Premium: Rs{premium:.2f}")
            
            if st.button(f"Delete Policy {policy_id}", key=f"del_{policy_id}"):
                if delete_policy(policy_id):
                    st.success(f"Policy {name} deleted successfully")
                    st.rerun()
            st.markdown("---")

        st.header("Add New Policy")
        new_policy_name = st.text_input("Policy Name")
        new_policy_details = st.text_area("Details")
        new_policy_premium = st.number_input("Premium Amount", min_value=0.0, step=0.01)
        #coverage_amount = st.number_input("Coverage Amount", min_value=0.0, step=0.01)
        
        if st.button("Add Policy"):
            add_policy(new_policy_name, new_policy_details, new_policy_premium)
            st.success("Policy added successfully")
            st.rerun()
            
        # View all policy holders
        st.subheader("Policy Holder Management")
        policy_holders = view_policy_holders()
        for holder in policy_holders:
            st.write(f"Policy Holder ID: {holder[0]}, Name: {holder[1]}, Age: {holder[2]}, Contact: {holder[3]}, Address: {holder[4]}")
        
        # Claims Processing
        st.subheader("Claims Processing")
        view_claims()
        
        # Reports
        st.subheader("Reports and Analytics")
        generate_reports()
    
    # Policy holder specific functions
    elif role == 'policy_holder':
        # Display user's purchased policies
        st.header("Your Policies")
        user_policies = get_user_policies(st.session_state.user_id)
        if user_policies:
            for policy in user_policies:
                policy_id, name, details, premium, purchase_date = policy
                st.write("---")
                st.write(f"*Policy Name:* {name}")
                st.write(f"*Details:* {details}")
                st.write(f"*Premium:* Rs{premium:.2f}")
                st.write(f"*Purchase Date:* {purchase_date.strftime('%Y-%m-%d %H:%M')}")
            st.write("---")
        else:
            st.info("You haven't purchased any policies yet.")

        # Display available policies for purchase
        st.header("Available Policies")
        policies = view_policies()
        
        # Create a unique identifier for each policy using combination of section and policy_id
        for idx, policy in enumerate(policies):
            policy_id, name, policy_details, premium = policy
            st.write(f"*{name}*")
            st.write(f"Details: {policy_details}")
            st.write(f"Premium: Rs{premium:.2f}")
            
            # Check if user already has this policy
            already_purchased = any(up[0] == policy_id for up in user_policies)
            if already_purchased:
                st.info("You already own this policy")
            else:
                # Using combination of index and policy_id to create unique key
                if st.button(f"Buy Policy {policy_id}", key=f"buy_policy_{idx}_{policy_id}"):
                    st.session_state.buying_policy_id = policy_id
                    st.rerun()
            st.markdown("---")

        # Policy purchase form
        if hasattr(st.session_state, 'buying_policy_id'):
            st.header("Complete Policy Purchase")
            name = st.text_input("Full Name")
            age = st.number_input("Age", min_value=18, max_value=100)
            contact = st.text_input("Contact Number")
            address = st.text_area("Address")
            
            if st.button("Confirm Purchase"):
                if buy_policy(st.session_state.user_id, st.session_state.buying_policy_id, 
                            name, age, contact, address):
                    st.success("Policy purchased successfully!")
                    st.session_state.policy_holder_id = get_policy_holder_id(st.session_state.user_id)
                    del st.session_state.buying_policy_id
                    st.rerun()
        
        # Claims submission section
        if user_policies:  # Only show if user has at least one policy
            st.header("Submit a Claim")
            
            # Dropdown to select which policy to claim against
            claim_policy = st.selectbox(
                "Select Policy for Claim",
                options=[(p[0], p[1]) for p in user_policies],
                format_func=lambda x: x[1]
            )
            
            claim_amount = st.number_input("Claim Amount", min_value=0.0, step=0.01)
            claim_description = st.text_area("Claim Description")
            
            if st.button("Submit Claim"):
                if claim_policy and claim_amount > 0:
                    submit_claim(st.session_state.policy_holder_id, claim_amount, claim_description)
                else:
                    st.error("Please select a policy and enter a valid claim amount.")
        else:
            st.warning("You need to purchase a policy before you can submit claims.")
        st.header("Your Claims")
    
    policy_holder_id = get_policy_holder_id(st.session_state.user_id)
    if policy_holder_id:
        claims = get_policy_holder_claims(policy_holder_id)
        
        if claims:
            for claim in claims:
                claim_id, claim_amount, description, status = claim
                st.write(f"**Claim ID:** {claim_id}")
                st.write(f"**Claim Amount:** Rs{claim_amount:.2f}")
                st.write(f"**Description:** {description}")
                st.write(f"**Status:** :red[{status}]")  # Display status in bold with color for emphasis
                st.markdown("---")
        else:
            st.info("You have no submitted claims.")
    
    # Logout button
    if st.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.success("Logged out successfully")
        st.rerun()

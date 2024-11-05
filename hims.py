import streamlit as st
import pymysql
from pymysql import OperationalError

# Database connection function
def create_connection():
    try:
        connection = pymysql.connect(
            host="localhost",
            user="root",
            password="pwd",
            database="healthinsurancedb"
        )
        return connection
    except OperationalError as e:
        st.error(f"Database connection error: {e}")
        return None

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
def add_policy(policy_name, premium, coverage_amount):
    conn = create_connection()
    if conn is None:
        return
    
    cursor = conn.cursor()
    cursor.execute("INSERT INTO policies (policy_name, premium, coverage_amount) VALUES (%s, %s, %s)",
                   (policy_name, premium, coverage_amount))
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
        # Start transaction
        cursor.execute("START TRANSACTION")
        
        # Add to policy_holders
        cursor.execute("""
            INSERT INTO policy_holders (user_id, name, age, contact, address) 
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, name, age, contact, address))
        
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

# Add this new function to get user's purchased policies
def get_user_policies(user_id):
    conn = create_connection()
    if conn is None:
        return []
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.policy_id, p.policy_name, p.policy_details, p.premium, pp.purchase_date 
        FROM policies p 
        JOIN policy_purchases pp ON p.policy_id = pp.policy_id 
        WHERE pp.user_id = %s
        ORDER BY pp.purchase_date DESC
    """, (user_id,))
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
            
            st.write(f"*Claim ID:* {claim_id}")
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
    
    conn.close()
    
    st.write(f"Total Policies: {total_policies}")
    st.write(f"Total Claims Submitted: {total_claims}")
    st.write(f"Total Claims Approved: {approved_claims}")
    st.write(f"Total Premium Collected: {total_premium_collected}")

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.user_id = None
    st.session_state.policy_holder_id = None

st.title("Health Insurance Management System")

# Login Section
if not st.session_state.logged_in:
    st.header("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        role, user_id = login(username, password)
        if role:
            st.session_state.logged_in = True
            st.session_state.role = role
            st.session_state.user_id = user_id
            st.session_state.policy_holder_id = get_policy_holder_id(user_id)
            st.success(f"Logged in as {role}")
            st.rerun()
        else:
            st.error("Invalid username or password.")

# Main Application
if st.session_state.logged_in:
    role = st.session_state.role
    
    # Main Application
if st.session_state.logged_in:
    role = st.session_state.role
    
    # Admin specific functions
    if role == 'admin':
        st.header("Available Policies")
        policies = view_policies()
        
        for policy in policies:
            policy_id, name, policy_details, premium = policy
            st.write(f"**{name}**")
            st.write(f"Details: {policy_details}")
            st.write(f"Premium: ${premium:.2f}")
            
            if st.button(f"Delete Policy {policy_id}", key=f"del_{policy_id}"):
                if delete_policy(policy_id):
                    st.success(f"Policy {name} deleted successfully")
                    st.rerun()
            st.markdown("---")

        st.header("Add New Policy")
        new_policy_name = st.text_input("Policy Name")
        new_policy_details = st.text_area("Details")
        new_policy_premium = st.number_input("Premium Amount", min_value=0.0, step=0.01)
        coverage_amount = st.number_input("Coverage Amount", min_value=0.0, step=0.01)
        
        if st.button("Add Policy"):
            add_policy(new_policy_name, new_policy_premium, coverage_amount)
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
                st.write(f"**Policy Name:** {name}")
                st.write(f"**Details:** {details}")
                st.write(f"**Premium:** ${premium:.2f}")
                st.write(f"**Purchase Date:** {purchase_date.strftime('%Y-%m-%d %H:%M')}")
            st.write("---")
        else:
            st.info("You haven't purchased any policies yet.")

        # Display available policies for purchase
        st.header("Available Policies")
        policies = view_policies()
        
        # Create a unique identifier for each policy using combination of section and policy_id
        for idx, policy in enumerate(policies):
            policy_id, name, policy_details, premium = policy
            st.write(f"**{name}**")
            st.write(f"Details: {policy_details}")
            st.write(f"Premium: ${premium:.2f}")
            
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
    
    # Logout button
    if st.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.success("Logged out successfully")
        st.rerun()

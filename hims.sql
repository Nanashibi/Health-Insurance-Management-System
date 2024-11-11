USE healthinsurancedb;
CREATE TABLE policies (
    policy_id INT AUTO_INCREMENT PRIMARY KEY,
    policy_name VARCHAR(255) NOT NULL,
    premium DECIMAL(10, 2) NOT NULL,
    policy_details TEXT NOT NULL
);
INSERT INTO policies (policy_name, premium, policy_details) VALUES 
('Individual Health Insurance', 27500, 'The individual gets compensated for illness and medical expenses till the insured limit is reached. The premium of the plan is decided on the basis of age and medical history.'),
('Family Health Insurance', 55000, 'Family Health Insurance Policy secures your entire family under a single cover.'),
('Critical Illness Insurance', 12500, 'The Critical Illness Insurance plan insures the person by offering a lump sum amount of money for life-threatening diseases post diagnosis. The amount is predefined irrespective of expenses.'),
('Senior Citizen Health Insurance', 70000, 'The Senior Citizen Health Insurance will offer you coverage for the cost of hospitalisation and medicines, whether it arises from a health issue or any accident.'),
('Top Up Health Insurance', 12500, 'Top Up Health Insurance plan is for higher coverage amounts. It provides additional coverage over the regular policy to increase the amount of sum insured.'),
('Hospital Daily Cash', 75500, 'Hospital Daily Cash grants individual of routine treatment a benefit of Rs. 500 to 10,000, as per the coverage amount selected.'),
('Personal Accident Insurance', 25000, 'This policy provides a lump sum amount to the victim or his/her family as support.'),
('ULIPs', 65000, 'ULIPs invests a part of your premium and the other remaining part is used for buying health covers.'),
('Disease-Specific', 25000, 'Disease-Specific health insurance provides coverage for specific diseases.'),
('Mediclaim', 27500, 'Mediclaim Policy ensures compensation for your hospitalisation expenses in case of any illness and accident.');
CREATE TABLE policy_holders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    age INT NOT NULL,
    contact VARCHAR(50),
    address TEXT,
    user_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
CREATE TABLE claims (
    claim_id INT AUTO_INCREMENT PRIMARY KEY,
    policy_holder_id INT,
    claim_amount DECIMAL(10, 2),
    description TEXT,
    status ENUM('Pending', 'Approved', 'Rejected') DEFAULT 'Pending',
    FOREIGN KEY (policy_holder_id) REFERENCES policy_holders(id)
);
CREATE TABLE policy_purchases (
    purchase_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    policy_id INT NOT NULL,
    purchase_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (policy_id) REFERENCES policies(policy_id)
);

-- TRIGGERS 
-- 1.Create Log Table and  Trigger to Automatically Log Policy Purchases
CREATE TABLE purchase_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    policy_id INT NOT NULL,
    purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    log_details TEXT
);

DELIMITER //
CREATE TRIGGER after_policy_purchase
AFTER INSERT ON policy_purchases
FOR EACH ROW
BEGIN
    INSERT INTO purchase_logs (user_id, policy_id, purchase_date, log_details)
    VALUES (NEW.user_id, NEW.policy_id, NEW.purchase_date, CONCAT('Policy purchased with ID: ', NEW.policy_id));
END;
//
DELIMITER ;

-- 2. Log Table and Trigger for Claim Submissions

CREATE TABLE claim_submission_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    policy_holder_id INT NOT NULL,
    claim_id INT NOT NULL,
    submission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    log_details TEXT
);

DELIMITER //
CREATE TRIGGER after_claim_submission
AFTER INSERT ON claims
FOR EACH ROW
BEGIN
    INSERT INTO claim_submission_logs (policy_holder_id, claim_id, submission_date, log_details)
    VALUES (NEW.policy_holder_id, NEW.claim_id, NOW(), 
            CONCAT('Claim submitted with ID: ', NEW.claim_id, ' for amount: ', NEW.claim_amount));
END;
//
DELIMITER ;

-- 3. Log Table and Trigger for Claim Status Changes

CREATE TABLE claim_status_change_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    claim_id INT NOT NULL,
    old_status ENUM('Pending', 'Approved', 'Rejected') NOT NULL,
    new_status ENUM('Pending', 'Approved', 'Rejected') NOT NULL,
    change_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    log_details TEXT
);

DELIMITER //
CREATE TRIGGER after_claim_status_change
AFTER UPDATE ON claims
FOR EACH ROW
BEGIN
    IF OLD.status <> NEW.status THEN
        INSERT INTO claim_status_change_logs (claim_id, old_status, new_status, change_date, log_details)
        VALUES (NEW.claim_id, OLD.status, NEW.status, NOW(), 
                CONCAT('Claim status changed from ', OLD.status, ' to ', NEW.status, ' for Claim ID: ', NEW.claim_id));
    END IF;
END;
//
DELIMITER ;

-- 4. Log Table and Trigger for Policy Creation

CREATE TABLE policy_creation_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    policy_id INT NOT NULL,
    policy_name VARCHAR(100),
    creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    log_details TEXT
);

DELIMITER //
CREATE TRIGGER after_policy_creation
AFTER INSERT ON policies
FOR EACH ROW
BEGIN
    INSERT INTO policy_creation_logs (policy_id, policy_name, creation_date, log_details)
    VALUES (NEW.policy_id, NEW.policy_name, NOW(),
            CONCAT('Policy created with ID: ', NEW.policy_id, ' and Name: ', NEW.policy_name));
END;
//
DELIMITER ;

-- 5. Log Table and Trigger for Policy Deletion

CREATE TABLE policy_deletion_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    policy_id INT NOT NULL,
    policy_name VARCHAR(100),
    deletion_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    log_details TEXT
);

DELIMITER //
CREATE TRIGGER after_policy_deletion
AFTER DELETE ON policies
FOR EACH ROW
BEGIN
    INSERT INTO policy_deletion_logs (policy_id, policy_name, deletion_date, log_details)
    VALUES (OLD.policy_id, OLD.policy_name, NOW(),
            CONCAT('Policy deleted with ID: ', OLD.policy_id, ' and Name: ', OLD.policy_name));
END;
//
DELIMITER ;

-- PROCEDURES

-- Database connection function
CREATE PROCEDURE create_connection()
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SHOW ERRORS;
        ROLLBACK;
    END;
    
    CONNECT TO 'localhost' USER 'root' IDENTIFIED BY 'Godbless@8' DATABASE 'HealthInsuranceDB';
END;

-- Register user function
CREATE PROCEDURE register_user(IN username VARCHAR(255), IN password VARCHAR(255))
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SHOW ERRORS;
        ROLLBACK;
        SELECT FALSE;
    END;
    
    INSERT INTO users (username, password, role) VALUES (username, password, 'policy_holder');
    COMMIT;
    SELECT TRUE;
END;

-- Login function
CREATE PROCEDURE login(IN username VARCHAR(255), IN password VARCHAR(255), OUT role VARCHAR(255), OUT user_id INT)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SHOW ERRORS;
        SET role = NULL;
        SET user_id = NULL;
    END;
    
    SELECT u.role, u.user_id
    INTO role, user_id
    FROM users u
    WHERE u.username = username AND u.password = password;
END;

-- Add policy holder function
CREATE PROCEDURE add_policy_holder(IN name VARCHAR(255), IN age INT, IN contact VARCHAR(50), IN address TEXT)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SHOW ERRORS;
        ROLLBACK;
    END;
    
    INSERT INTO policy_holders (name, age, contact, address) VALUES (name, age, contact, address);
    COMMIT;
END;

-- View policy holders function
CREATE PROCEDURE view_policy_holders()
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SHOW ERRORS;
        RETURN;
    END;
    
    SELECT * FROM policy_holders;
END;

-- Add policy function
CREATE PROCEDURE add_policy(IN policy_name VARCHAR(255), IN policy_details TEXT, IN premium DECIMAL(10,2))
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SHOW ERRORS;
        ROLLBACK;
    END;
    
    INSERT INTO policies (policy_name, policy_details, premium) VALUES (policy_name, policy_details, premium);
    COMMIT;
END;

-- Update policy function
CREATE PROCEDURE update_policy(IN policy_id INT, IN policy_name VARCHAR(255), IN premium DECIMAL(10,2), IN coverage_amount DECIMAL(10,2))
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SHOW ERRORS;
        ROLLBACK;
    END;
    
    UPDATE policies
    SET policy_name = policy_name, premium = premium, coverage_amount = coverage_amount
    WHERE policy_id = policy_id;
    COMMIT;
END;

-- Get policy holder ID function
CREATE PROCEDURE get_policy_holder_id(IN user_id INT, OUT policy_holder_id INT)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SHOW ERRORS;
        SET policy_holder_id = NULL;
    END;
    
    SELECT id
    INTO policy_holder_id
    FROM policy_holders
    WHERE user_id = user_id;
END;

-- View policies function
CREATE PROCEDURE view_policies()
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SHOW ERRORS;
        RETURN;
    END;
    
    SELECT policy_id, policy_name, policy_details, premium FROM policies;
END;

-- Buy policy function
CREATE PROCEDURE buy_policy(IN user_id INT, IN policy_id INT, IN name VARCHAR(255), IN age INT, IN contact VARCHAR(50), IN address TEXT)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SHOW ERRORS;
        ROLLBACK;
        RETURN FALSE;
    END;
    
    DECLARE policy_holder_id INT;
    
    -- Check if the policy holder already exists
    SELECT id
    INTO policy_holder_id
    FROM policy_holders
    WHERE user_id = user_id;
    
    IF policy_holder_id IS NULL THEN
        -- Insert new policy holder
        INSERT INTO policy_holders (user_id, name, age, contact, address)
        VALUES (user_id, name, age, contact, address);
        SET policy_holder_id = LAST_INSERT_ID();
    END IF;
    
    -- Fetch the premium amount for the selected policy
    DECLARE premium_amount DECIMAL(10,2);
    SELECT premium
    INTO premium_amount
    FROM policies
    WHERE policy_id = policy_id;
    
    -- Update the total premium collected
    UPDATE global_statistics
    SET total_premium_collected = total_premium_collected + premium_amount;
    
    -- Add to policy_purchases
    INSERT INTO policy_purchases (user_id, policy_id)
    VALUES (user_id, policy_id);
    
    COMMIT;
    RETURN TRUE;
END;

-- Get user policies function
CREATE PROCEDURE get_user_policies(IN user_id INT)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SHOW ERRORS;
        RETURN;
    END;
    
    SELECT p.policy_id, p.policy_name, p.policy_details, p.premium,
           (SELECT MAX(pp.purchase_date)
            FROM policy_purchases pp
            WHERE pp.policy_id = p.policy_id AND pp.user_id = user_id) AS latest_purchase_date
    FROM policies p
    WHERE p.policy_id IN (
        SELECT pp.policy_id
        FROM policy_purchases pp
        WHERE pp.user_id = user_id
    )
    ORDER BY latest_purchase_date DESC;
END;

-- Delete policy function
CREATE PROCEDURE delete_policy(IN policy_id INT)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SHOW ERRORS;
        ROLLBACK;
        RETURN FALSE;
    END;
    
    DELETE FROM policies WHERE policy_id = policy_id;
    COMMIT;
    RETURN TRUE;
END;

-- Submit claim function
CREATE PROCEDURE submit_claim(IN policy_holder_id INT, IN claim_amount DECIMAL(10,2), IN description TEXT)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SHOW ERRORS;
        ROLLBACK;
    END;
    
    INSERT INTO claims (policy_holder_id, claim_amount, description, status)
    VALUES (policy_holder_id, claim_amount, description, 'Pending');
    COMMIT;
END;

-- Process claim function
CREATE PROCEDURE process_claim(IN claim_id INT, IN action VARCHAR(50))
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SHOW ERRORS;
        ROLLBACK;
    END;
    
    DECLARE claim_status VARCHAR(50);
    SET claim_status = CASE action WHEN 'approve' THEN 'Approved' ELSE 'Rejected' END;
    
    UPDATE claims
    SET status = claim_status
    WHERE claim_id = claim_id;
    COMMIT;
END;

-- View claims function
CREATE PROCEDURE view_claims()
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SHOW ERRORS;
        RETURN;
    END;
    
    SELECT claim_id, policy_holder_id, claim_amount, description, status
    FROM claims
    WHERE status = 'Pending';
END;

-- Update claim status function
CREATE PROCEDURE update_claim_status(IN claim_id INT, IN new_status VARCHAR(50), IN claim_amount DECIMAL(10,2))
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SHOW ERRORS;
        ROLLBACK;
    END;
    
    UPDATE claims
    SET status = new_status
    WHERE claim_id = claim_id;
    
    IF new_status = 'Approved' THEN
        UPDATE global_statistics
        SET total_claims_approved = total_claims_approved + claim_amount;
    END IF;
    
    COMMIT;
END;

-- Get policy holder claims function
CREATE PROCEDURE get_policy_holder_claims(IN policy_holder_id INT)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SHOW ERRORS;
        RETURN;
    END;
    
    SELECT claim_id, claim_amount, description, status
    FROM claims
    WHERE policy_holder_id = policy_holder_id
    ORDER BY claim_id DESC;
END;

-- Generate reports function
CREATE PROCEDURE generate_reports()
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SHOW ERRORS;
        RETURN;
    END;
    
    -- Report: Total policies
    DECLARE total_policies INT;
    SELECT COUNT(*) INTO total_policies FROM policies;
    
    -- Report: Total claims submitted and approved
    DECLARE approved_claims INT;
    DECLARE total_claims INT;
    SELECT COUNT(*) INTO approved_claims FROM claims WHERE status = 'Approved';
    SELECT COUNT(*) INTO total_claims FROM claims;
    
    -- Report: Total premium collected
    DECLARE total_premium_collected DECIMAL(10,2);
    SELECT COALESCE(SUM(premium), 0.0) INTO total_premium_collected FROM policies;
    
    -- Report: Total claims approved (sum of approved claim amounts)
    DECLARE total_claims_approved DECIMAL(10,2);
    SELECT COALESCE(SUM(claim_amount), 0.0) INTO total_claims_approved FROM claims WHERE status = 'Approved';
    
    -- Report: Total policies sold by category
    CREATE TEMPORARY TABLE policies_data AS
    SELECT p.policy_name, COUNT(*) AS num_policies_sold
    FROM policy_purchases pp
    JOIN policies p ON pp.policy_id = p.policy_id
    GROUP BY p.policy_name;
    
    -- Display the reports
    SELECT total_policies, total_claims, approved_claims, total_premium_collected, total_claims_approved;
    SELECT * FROM policies_data;
END;
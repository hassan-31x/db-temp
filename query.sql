CREATE DATABASE BloodDonation;
USE BloodDonation;

CREATE TABLE Role (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50),
    description VARCHAR(255)
);

CREATE TABLE Hospital (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255),
    location TEXT,
    contactInformation TEXT,
    bloodBankInventoryId INTEGER,
    createdAt TIMESTAMP,
    updatedAt TIMESTAMP
);

CREATE TABLE User (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(255),
    password_hash VARCHAR(255),
    email VARCHAR(255),
    roleId INTEGER,
    associatedHospitalId INTEGER,
    createdAt TIMESTAMP,
    updatedAt TIMESTAMP,
    FOREIGN KEY (roleId) REFERENCES Role(id),
    FOREIGN KEY (associatedHospitalId) REFERENCES Hospital(id)
);

CREATE TABLE BloodType (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    bloodType VARCHAR(10)
);

CREATE TABLE Donor (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    userId INTEGER,
    name VARCHAR(255),
    bloodTypeId INTEGER,
    contactInformation TEXT,
    medicalHistory TEXT,
    eligibilityStatus BOOLEAN,
    lastDonationDate DATE,
    createdAt TIMESTAMP,
    updatedAt TIMESTAMP,
    FOREIGN KEY (userId) REFERENCES User(id),
    FOREIGN KEY (bloodTypeId) REFERENCES BloodType(id)
);

CREATE TABLE BloodBankInventory (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    hospitalId INTEGER,
    bloodTypeId INTEGER,
    quantityInStock INTEGER,
    expirationDate DATE,
    createdAt TIMESTAMP,
    updatedAt TIMESTAMP,
    FOREIGN KEY (hospitalId) REFERENCES Hospital(id),
    FOREIGN KEY (bloodTypeId) REFERENCES BloodType(id)
);

ALTER TABLE Hospital
ADD FOREIGN KEY (bloodBankInventoryId) REFERENCES BloodBankInventory(id);

CREATE TABLE Appointment (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    donorId INTEGER,
    hospitalId INTEGER,
    appointmentDate DATE,
    appointmentTime TIME,
    status VARCHAR(50),
    createdAt TIMESTAMP,
    updatedAt TIMESTAMP,
    FOREIGN KEY (donorId) REFERENCES Donor(id),
    FOREIGN KEY (hospitalId) REFERENCES Hospital(id)
);

CREATE TABLE BloodRequest (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    hospitalId INTEGER,
    bloodTypeId INTEGER,
    urgencyLevel VARCHAR(50),
    requestStatus VARCHAR(50),
    requestedQuantity INTEGER,
    fulfilledQuantity INTEGER,
    createdAt TIMESTAMP,
    updatedAt TIMESTAMP,
    FOREIGN KEY (hospitalId) REFERENCES Hospital(id),
    FOREIGN KEY (bloodTypeId) REFERENCES BloodType(id)
);

CREATE TABLE BloodDispatch (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    requestId INTEGER,
    bloodTypeId INTEGER,
    quantityDispatched INTEGER,
    dispatchDate TIMESTAMP,
    deliveryStatus VARCHAR(50),
    vehicleInfo TEXT,
    driverName VARCHAR(255),
    estimatedArrival TIMESTAMP,
    createdAt TIMESTAMP,
    updatedAt TIMESTAMP,
    FOREIGN KEY (requestId) REFERENCES BloodRequest(id),
    FOREIGN KEY (bloodTypeId) REFERENCES BloodType(id)
);

ALTER TABLE BloodRequest
ADD COLUMN fulfilledBy INTEGER,
ADD FOREIGN KEY (fulfilledBy) REFERENCES Donor(id);

INSERT INTO Role (name, description) 
VALUES 
  ('Admin', 'System administrator with full access to manage users, hospitals, and blood bank inventory'),
  ('Donor', 'Blood donors who can schedule appointments and view donation history'),
  ('Hospital', 'Healthcare facilities that can request blood and manage their inventory');

INSERT INTO User (username, password_hash, email, roleId, associatedHospitalId, createdAt, updatedAt) 
VALUES 
  (
    'admin', 
    SHA2('admin', 256),  -- Encrypting the password for better security using SHA-256
    'admin@example.com', 
    (SELECT id FROM Role WHERE name = 'Admin' LIMIT 1), 
    NULL,  -- No associated hospital for the Admin role
    CURRENT_TIMESTAMP, 
    CURRENT_TIMESTAMP
  );

INSERT INTO BloodType (bloodType) 
VALUES 
  ('A+'),
  ('A-'),
  ('B+'),
  ('B-'),
  ('AB+'),
  ('AB-'),
  ('O+'),
  ('O-');


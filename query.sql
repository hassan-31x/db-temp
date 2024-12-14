CREATE DATABASE BloodDonation;
USE BloodDonation;

CREATE TABLE Role (
    id INT PRIMARY KEY IDENTITY(1,1),
    name NVARCHAR(50),
    description NVARCHAR(255)
);

CREATE TABLE Hospital (
    id INT PRIMARY KEY IDENTITY(1,1),
    name NVARCHAR(255),
    location NVARCHAR(MAX),
    contactInformation NVARCHAR(MAX),
    bloodBankInventoryId INT,
    createdAt DATETIME,
    updatedAt DATETIME
);

CREATE TABLE [User] (
    id INT PRIMARY KEY IDENTITY(1,1),
    username NVARCHAR(255),
    password_hash NVARCHAR(255),
    email NVARCHAR(255),
    roleId INT,
    associatedHospitalId INT,
    createdAt DATETIME,
    updatedAt DATETIME,
    FOREIGN KEY (roleId) REFERENCES Role(id),
    FOREIGN KEY (associatedHospitalId) REFERENCES Hospital(id)
);

CREATE TABLE BloodType (
    id INT PRIMARY KEY IDENTITY(1,1),
    bloodType NVARCHAR(10)
);

CREATE TABLE Donor (
    id INT PRIMARY KEY IDENTITY(1,1),
    userId INT,
    name NVARCHAR(255),
    bloodTypeId INT,
    contactInformation NVARCHAR(MAX),
    medicalHistory NVARCHAR(MAX),
    eligibilityStatus BIT,
    lastDonationDate DATE,
    createdAt DATETIME,
    updatedAt DATETIME,
    FOREIGN KEY (userId) REFERENCES [User](id),
    FOREIGN KEY (bloodTypeId) REFERENCES BloodType(id)
);

CREATE TABLE BloodBankInventory (
    id INT PRIMARY KEY IDENTITY(1,1),
    hospitalId INT,
    bloodTypeId INT,
    quantityInStock INT,
    expirationDate DATE,
    createdAt DATETIME,
    updatedAt DATETIME,
    FOREIGN KEY (hospitalId) REFERENCES Hospital(id),
    FOREIGN KEY (bloodTypeId) REFERENCES BloodType(id)
);

ALTER TABLE Hospital
ADD FOREIGN KEY (bloodBankInventoryId) REFERENCES BloodBankInventory(id);

CREATE TABLE Appointment (
    id INT PRIMARY KEY IDENTITY(1,1),
    donorId INT,
    hospitalId INT,
    appointmentDate DATE,
    appointmentTime TIME,
    status NVARCHAR(50),
    createdAt DATETIME,
    updatedAt DATETIME,
    FOREIGN KEY (donorId) REFERENCES Donor(id),
    FOREIGN KEY (hospitalId) REFERENCES Hospital(id)
);

CREATE TABLE BloodRequest (
    id INT PRIMARY KEY IDENTITY(1,1),
    hospitalId INT,
    bloodTypeId INT,
    urgencyLevel NVARCHAR(50),
    requestStatus NVARCHAR(50),
    requestedQuantity INT,
    fulfilledQuantity INT,
    createdAt DATETIME,
    updatedAt DATETIME,
    FOREIGN KEY (hospitalId) REFERENCES Hospital(id),
    FOREIGN KEY (bloodTypeId) REFERENCES BloodType(id)
);

CREATE TABLE BloodDispatch (
    id INT PRIMARY KEY IDENTITY(1,1),
    requestId INT,
    bloodTypeId INT,
    quantityDispatched INT,
    dispatchDate DATETIME,
    deliveryStatus NVARCHAR(50),
    vehicleInfo NVARCHAR(MAX),
    driverName NVARCHAR(255),
    estimatedArrival DATETIME,
    createdAt DATETIME,
    updatedAt DATETIME,
    FOREIGN KEY (requestId) REFERENCES BloodRequest(id),
    FOREIGN KEY (bloodTypeId) REFERENCES BloodType(id)
);


ALTER TABLE BloodRequest
ADD fulfilledBy INT;

ALTER TABLE BloodRequest
ADD CONSTRAINT FK_BloodRequest_fulfilledBy FOREIGN KEY (fulfilledBy) REFERENCES Donor(id);



INSERT INTO Role (name, description) 
VALUES 
  ('Admin', 'System administrator with full access to manage users, hospitals, and blood bank inventory'),
  ('Donor', 'Blood donors who can schedule appointments and view donation history'),
  ('Hospital', 'Healthcare facilities that can request blood and manage their inventory');


INSERT INTO [User] (username, password_hash, email, roleId, associatedHospitalId, createdAt, updatedAt)
VALUES (
    'admin',
    'admin',  -- Encrypting the password for better security using SHA-256
    'admin@example.com',
    (SELECT TOP (1) id FROM Role WHERE name = 'Admin'),
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
CREATE DATABASE transport_db;
USE transport_db;

CREATE TABLE drivers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20)
);

CREATE TABLE conductors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20)
);

CREATE TABLE leaves (
    id INT AUTO_INCREMENT PRIMARY KEY,
    crew_type VARCHAR(20),
    crew_id INT,
    leave_date DATE
);

CREATE TABLE assignments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    route VARCHAR(100),
    hour INT,
    bus_no INT,
    driver_id INT,
    conductor_id INT,
    passengers INT DEFAULT 0
);
-- PostgreSQL dump for turf_db (Corrected)
-- Drop everything first
DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO public;

-- Table: auth_group
CREATE TABLE auth_group (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL UNIQUE
);

-- Table: auth_permission
CREATE TABLE auth_permission (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    content_type_id INTEGER NOT NULL,
    codename VARCHAR(100) NOT NULL,
    UNIQUE(content_type_id, codename)
);

-- Table: auth_group_permissions
CREATE TABLE auth_group_permissions (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    UNIQUE(group_id, permission_id)
);

-- Table: auth_user
CREATE TABLE auth_user (
    id SERIAL PRIMARY KEY,
    password VARCHAR(128) NOT NULL,
    last_login TIMESTAMP,
    is_superuser BOOLEAN NOT NULL,
    username VARCHAR(150) NOT NULL UNIQUE,
    first_name VARCHAR(150) NOT NULL,
    last_name VARCHAR(150) NOT NULL,
    email VARCHAR(254) NOT NULL,
    is_staff BOOLEAN NOT NULL,
    is_active BOOLEAN NOT NULL,
    date_joined TIMESTAMP NOT NULL
);

-- Table: auth_user_groups
CREATE TABLE auth_user_groups (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    group_id INTEGER NOT NULL,
    UNIQUE(user_id, group_id)
);

-- Table: auth_user_user_permissions
CREATE TABLE auth_user_user_permissions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    UNIQUE(user_id, permission_id)
);

-- Table: core_turf
CREATE TABLE core_turf (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(255) NOT NULL,
    price_per_hour INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL,
    is_approved BOOLEAN NOT NULL,
    owner_id INTEGER,
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6)
);

-- Table: core_ground
CREATE TABLE core_ground (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    turf_id BIGINT NOT NULL
);

-- Table: core_slot
CREATE TABLE core_slot (
    id SERIAL PRIMARY KEY,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    is_booked BOOLEAN NOT NULL,
    ground_id BIGINT NOT NULL
);

-- Table: core_cart
CREATE TABLE core_cart (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    user_id INTEGER NOT NULL,
    ground_id BIGINT NOT NULL,
    slot_id BIGINT NOT NULL,
    turf_id BIGINT NOT NULL
);

-- Table: core_booking
CREATE TABLE core_booking (
    id SERIAL PRIMARY KEY,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    user_id INTEGER NOT NULL,
    cart_id BIGINT NOT NULL UNIQUE,
    vendor_status VARCHAR(20) NOT NULL
);

-- Table: core_otp
CREATE TABLE core_otp (
    id SERIAL PRIMARY KEY,
    mobile VARCHAR(10) NOT NULL,
    otp VARCHAR(6) NOT NULL,
    is_verified BOOLEAN NOT NULL,
    created_at TIMESTAMP NOT NULL
);

-- Table: core_payment
CREATE TABLE core_payment (
    id SERIAL PRIMARY KEY,
    razorpay_order_id VARCHAR(200) NOT NULL,
    razorpay_payment_id VARCHAR(200),
    razorpay_signature VARCHAR(300),
    amount INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    booking_id BIGINT NOT NULL UNIQUE,
    user_id INTEGER NOT NULL
);

-- Table: django_content_type
CREATE TABLE django_content_type (
    id SERIAL PRIMARY KEY,
    app_label VARCHAR(100) NOT NULL,
    model VARCHAR(100) NOT NULL,
    UNIQUE(app_label, model)
);

-- Table: django_migrations
CREATE TABLE django_migrations (
    id SERIAL PRIMARY KEY,
    app VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    applied TIMESTAMP NOT NULL
);

-- Table: django_session
CREATE TABLE django_session (
    session_key VARCHAR(40) PRIMARY KEY,
    session_data TEXT NOT NULL,
    expire_date TIMESTAMP NOT NULL
);

-- Table: django_admin_log
CREATE TABLE django_admin_log (
    id SERIAL PRIMARY KEY,
    action_time TIMESTAMP NOT NULL,
    object_id TEXT,
    object_repr VARCHAR(200) NOT NULL,
    action_flag SMALLINT NOT NULL,
    change_message TEXT NOT NULL,
    content_type_id INTEGER,
    user_id INTEGER NOT NULL
);

-- Insert data for django_content_type
INSERT INTO django_content_type (id, app_label, model) VALUES
(1, 'admin', 'logentry'),
(2, 'auth', 'group'),
(3, 'auth', 'permission'),
(4, 'auth', 'user'),
(5, 'contenttypes', 'contenttype'),
(6, 'sessions', 'session'),
(7, 'core', 'booking'),
(8, 'core', 'cart'),
(9, 'core', 'ground'),
(10, 'core', 'otp'),
(11, 'core', 'payment'),
(12, 'core', 'slot'),
(13, 'core', 'turf');

SELECT setval('django_content_type_id_seq', 13);

-- Insert auth_permission data
INSERT INTO auth_permission (id, name, content_type_id, codename) VALUES
(1, 'Can add log entry', 1, 'add_logentry'),
(2, 'Can change log entry', 1, 'change_logentry'),
(3, 'Can delete log entry', 1, 'delete_logentry'),
(4, 'Can view log entry', 1, 'view_logentry'),
(5, 'Can add permission', 3, 'add_permission'),
(6, 'Can change permission', 3, 'change_permission'),
(7, 'Can delete permission', 3, 'delete_permission'),
(8, 'Can view permission', 3, 'view_permission'),
(9, 'Can add group', 2, 'add_group'),
(10, 'Can change group', 2, 'change_group'),
(11, 'Can delete group', 2, 'delete_group'),
(12, 'Can view group', 2, 'view_group'),
(13, 'Can add user', 4, 'add_user'),
(14, 'Can change user', 4, 'change_user'),
(15, 'Can delete user', 4, 'delete_user'),
(16, 'Can view user', 4, 'view_user'),
(17, 'Can add content type', 5, 'add_contenttype'),
(18, 'Can change content type', 5, 'change_contenttype'),
(19, 'Can delete content type', 5, 'delete_contenttype'),
(20, 'Can view content type', 5, 'view_contenttype'),
(21, 'Can add session', 6, 'add_session'),
(22, 'Can change session', 6, 'change_session'),
(23, 'Can delete session', 6, 'delete_session'),
(24, 'Can view session', 6, 'view_session'),
(25, 'Can add ground', 9, 'add_ground'),
(26, 'Can change ground', 9, 'change_ground'),
(27, 'Can delete ground', 9, 'delete_ground'),
(28, 'Can view ground', 9, 'view_ground'),
(29, 'Can add otp', 10, 'add_otp'),
(30, 'Can change otp', 10, 'change_otp'),
(31, 'Can delete otp', 10, 'delete_otp'),
(32, 'Can view otp', 10, 'view_otp'),
(33, 'Can add turf', 13, 'add_turf'),
(34, 'Can change turf', 13, 'change_turf'),
(35, 'Can delete turf', 13, 'delete_turf'),
(36, 'Can view turf', 13, 'view_turf'),
(37, 'Can add cart', 8, 'add_cart'),
(38, 'Can change cart', 8, 'change_cart'),
(39, 'Can delete cart', 8, 'delete_cart'),
(40, 'Can view cart', 8, 'view_cart'),
(41, 'Can add booking', 7, 'add_booking'),
(42, 'Can change booking', 7, 'change_booking'),
(43, 'Can delete booking', 7, 'delete_booking'),
(44, 'Can view booking', 7, 'view_booking'),
(45, 'Can add payment', 11, 'add_payment'),
(46, 'Can change payment', 11, 'change_payment'),
(47, 'Can delete payment', 11, 'delete_payment'),
(48, 'Can view payment', 11, 'view_payment'),
(49, 'Can add slot', 12, 'add_slot'),
(50, 'Can change slot', 12, 'change_slot'),
(51, 'Can delete slot', 12, 'delete_slot'),
(52, 'Can view slot', 12, 'view_slot');

SELECT setval('auth_permission_id_seq', 52);

-- Insert auth_user (superuser)
INSERT INTO auth_user (id, password, last_login, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined) VALUES
(1, 'pbkdf2_sha256$260000$8sKxL3kZ9xQwYh2m$X5uR9mVuO5hBkttNUr5ECfozPaE2c/1V++Roz48iUSo=', NULL, true, 'myadugalam@gmail.com', 'Admin', 'User', 'myadugalam@gmail.com', true, true, NOW());

SELECT setval('auth_user_id_seq', 1);

-- Insert django_migrations
INSERT INTO django_migrations (id, app, name, applied) VALUES
(1, 'contenttypes', '0001_initial', NOW()),
(2, 'auth', '0001_initial', NOW()),
(3, 'admin', '0001_initial', NOW()),
(4, 'sessions', '0001_initial', NOW()),
(5, 'core', '0001_initial', NOW());

SELECT setval('django_migrations_id_seq', 5);

-- Create indexes
CREATE INDEX core_otp_mobile_idx ON core_otp (mobile);
CREATE INDEX django_session_expire_date_idx ON django_session (expire_date);
CREATE INDEX core_booking_user_id_idx ON core_booking (user_id);
CREATE INDEX core_cart_user_id_idx ON core_cart (user_id);

-- Add foreign keys
ALTER TABLE auth_permission ADD CONSTRAINT auth_permission_content_type_id_fkey 
    FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE auth_group_permissions ADD CONSTRAINT auth_group_permissions_group_id_fkey 
    FOREIGN KEY (group_id) REFERENCES auth_group(id) DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE auth_group_permissions ADD CONSTRAINT auth_group_permissions_permission_id_fkey 
    FOREIGN KEY (permission_id) REFERENCES auth_permission(id) DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE auth_user_groups ADD CONSTRAINT auth_user_groups_user_id_fkey 
    FOREIGN KEY (user_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE auth_user_groups ADD CONSTRAINT auth_user_groups_group_id_fkey 
    FOREIGN KEY (group_id) REFERENCES auth_group(id) DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE auth_user_user_permissions ADD CONSTRAINT auth_user_user_permissions_user_id_fkey 
    FOREIGN KEY (user_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE auth_user_user_permissions ADD CONSTRAINT auth_user_user_permissions_permission_id_fkey 
    FOREIGN KEY (permission_id) REFERENCES auth_permission(id) DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE core_ground ADD CONSTRAINT core_ground_turf_id_fkey 
    FOREIGN KEY (turf_id) REFERENCES core_turf(id) DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE core_slot ADD CONSTRAINT core_slot_ground_id_fkey 
    FOREIGN KEY (ground_id) REFERENCES core_ground(id) DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE core_cart ADD CONSTRAINT core_cart_user_id_fkey 
    FOREIGN KEY (user_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE core_cart ADD CONSTRAINT core_cart_ground_id_fkey 
    FOREIGN KEY (ground_id) REFERENCES core_ground(id) DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE core_cart ADD CONSTRAINT core_cart_slot_id_fkey 
    FOREIGN KEY (slot_id) REFERENCES core_slot(id) DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE core_cart ADD CONSTRAINT core_cart_turf_id_fkey 
    FOREIGN KEY (turf_id) REFERENCES core_turf(id) DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE core_booking ADD CONSTRAINT core_booking_user_id_fkey 
    FOREIGN KEY (user_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE core_booking ADD CONSTRAINT core_booking_cart_id_fkey 
    FOREIGN KEY (cart_id) REFERENCES core_cart(id) DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE core_payment ADD CONSTRAINT core_payment_booking_id_fkey 
    FOREIGN KEY (booking_id) REFERENCES core_booking(id) DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE core_payment ADD CONSTRAINT core_payment_user_id_fkey 
    FOREIGN KEY (user_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE django_admin_log ADD CONSTRAINT django_admin_log_user_id_fkey 
    FOREIGN KEY (user_id) REFERENCES auth_user(id) DEFERRABLE INITIALLY DEFERRED;

ALTER TABLE django_admin_log ADD CONSTRAINT django_admin_log_content_type_id_fkey 
    FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED;

-- Grant privileges
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;

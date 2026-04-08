CREATE DATABASE IF NOT EXISTS smart_reimbursement DEFAULT CHARACTER SET utf8mb4;
USE smart_reimbursement;

DROP TABLE IF EXISTS reimbursement;
DROP TABLE IF EXISTS invoice;
DROP TABLE IF EXISTS employee;

CREATE TABLE employee (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  employee_no VARCHAR(20) NOT NULL UNIQUE,
  name VARCHAR(50) NOT NULL,
  phone VARCHAR(20) DEFAULT '',
  password VARCHAR(128) NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE invoice (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  employee_id BIGINT NOT NULL,
  code_6 CHAR(6) UNIQUE,
  invoice_fingerprint VARCHAR(128) DEFAULT '',
  file VARCHAR(255) NOT NULL,
  verify_status VARCHAR(20) NOT NULL DEFAULT 'pending',
  verify_msg VARCHAR(255) DEFAULT '',
  invoice_code VARCHAR(32) DEFAULT '',
  invoice_num VARCHAR(32) DEFAULT '',
  invoice_date VARCHAR(20) DEFAULT '',
  check_code VARCHAR(32) DEFAULT '',
  amount DECIMAL(12,2) NULL,
  tax_amount DECIMAL(12,2) NULL,
  total_amount DECIMAL(12,2) NULL,
  buyer_name VARCHAR(100) DEFAULT '',
  seller_name VARCHAR(100) DEFAULT '',
  ocr_result JSON NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_invoice_employee FOREIGN KEY (employee_id) REFERENCES employee(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_invoice_fingerprint ON invoice(invoice_fingerprint);

CREATE TABLE reimbursement (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  employee_id BIGINT NOT NULL,
  invoice_id BIGINT NOT NULL UNIQUE,
  department VARCHAR(50) NOT NULL,
  reason VARCHAR(255) NOT NULL,
  expense_type VARCHAR(50) NOT NULL,
  reimbursement_date DATE NOT NULL,
  remark VARCHAR(255) DEFAULT '',
  amount DECIMAL(12,2) NOT NULL,
  amount_upper VARCHAR(100) NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'draft',
  submitted_at DATETIME NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_reim_employee FOREIGN KEY (employee_id) REFERENCES employee(id),
  CONSTRAINT fk_reim_invoice FOREIGN KEY (invoice_id) REFERENCES invoice(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

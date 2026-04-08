# ER图（Mermaid）

```mermaid
erDiagram
    EMPLOYEE ||--o{ INVOICE : uploads
    EMPLOYEE ||--o{ REIMBURSEMENT : creates
    INVOICE ||--|| REIMBURSEMENT : maps

    EMPLOYEE {
        bigint id PK
        varchar employee_no UK
        varchar name
        varchar phone
        varchar password
        datetime created_at
    }

    INVOICE {
        bigint id PK
        bigint employee_id FK
        char code_6 UK
        varchar file
        varchar verify_status
        varchar verify_msg
        varchar invoice_code
        varchar invoice_num
        varchar invoice_date
        varchar check_code
        decimal amount
        decimal tax_amount
        decimal total_amount
        json ocr_result
        datetime created_at
    }

    REIMBURSEMENT {
        bigint id PK
        bigint employee_id FK
        bigint invoice_id FK UK
        varchar department
        varchar reason
        varchar expense_type
        date reimbursement_date
        decimal amount
        varchar amount_upper
        varchar status
        datetime submitted_at
        datetime created_at
    }
```

Project Statement – Library Management System

## Problem Statement
Libraries often face challenges in managing book inventories and user transactions manually.
Common problems include:

- Difficulty tracking issued/returned books
- No real-time availability status
- Manual fine calculation, leading to errors
- Missing or duplicate records
- High workload for librarians

To address these issues, an automated Library Management System is required.

---

## Scope of the Project

The project covers:

✔ User Management

Add, store, and retrieve user information.

✔ Book Management

Maintain book details including author, stock, and availability.

✔ Book Issue / Return

Issue books with due dates, return tracking, and fine calculation.

✔ Database Management

Persistent storage of users, books, and issue history using SQLite.

---

## Target Users
The system is designed for:

Students – to borrow books

Teachers/Faculties – to issue academic materials

Librarians – to manage inventory and operations

Administrators – to generate reports and maintain records

---

## High-Level Features

1. User Module

- Add user
- View user list
- Role assignment
- Validation on issue

2. Book Module

- Add books
- Update book copies
- Search books
- Track availability

3. Issue/Return Module

- Issue a book
- Set due date
- Prevent issuing when copies are unavailable
- Return a book
- Auto-calculate fine

4. Reporting

- List of issued books
- Overdue books
- User-wise history

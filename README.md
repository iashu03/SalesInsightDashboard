# Sales Insight Dashboard

A near real-time data-driven web application built with Flask, SQLite, HTML, CSS, JavaScript, and Chart.js for managing sales records and generating business insights.

## Features

- Responsive web interface
- Add, view, search, and filter sales records
- SQLite database integration
- Python Flask backend
- Near real-time dashboard updates every 5 seconds
- Data analytics and visualization using Chart.js
- Summary cards for:
  - Total Revenue
  - Total Orders
  - Average Order Value
  - Top Product
- Insights charts for:
  - Monthly Revenue
  - Category-wise Revenue
  - Top Customers
  - Top Products

## Tech Stack

- Frontend: HTML, CSS, JavaScript
- Backend: Python, Flask
- Database: SQLite
- Charts: Chart.js

## Project Structure

```text
sales-insight-dashboard/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── LICENSE
├── database.db
│
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   └── records.html
│
├── static/
│   ├── style.css
│   └── script.js
│
└── screenshots/
    ├── dashboard.png
    ├── records.png
    └── analytics.png
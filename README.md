# Sales Forecasting & Inventory Optimization DSS

A practical Decision Support System (DSS) that helps retail decision-makers forecast demand and generate inventory recommendations using real sales data.

## 1. Problem Statement
Retail and supermarket managers often struggle with balancing stock availability and overstock risk. This system supports tactical decisions by:
- analyzing historical sales behavior,
- forecasting category-level demand,
- recommending reorder targets using reorder point and safety stock logic.

## 2. Decision-Makers and Decision Context
Primary decision-makers:
- Inventory managers
- Store operations managers
- Category managers

Decisions supported:
- Which categories should be reordered first
- How much stock should be reordered
- How demand is expected to change in the short term

## 3. DSS Theory and Decision Logic
This project combines multiple DSS components:
- Data-driven model: Prophet-based time-series forecasting for category demand.
- Rule-based logic: reorder recommendations using average demand, lead time, service level, and safety stock.
- KPI-based monitoring: revenue, quantity, and top-category metrics for management review.

Core formulas used:
- Reorder Point = Average Daily Demand x Lead Time
- Safety Stock = z x sigma_demand x sqrt(Lead Time)
- Target Stock = Reorder Point + Safety Stock

## 4. System Architecture
```mermaid
flowchart LR
    A[Raw Sales CSV] --> B[Cleaning Pipeline]
    B --> C[Cleaned Daily Sales Dataset]
    C --> D[Flask App]
    D --> E[Dashboard Route /]
    D --> F[EDA Route /eda]
    D --> G[Forecast Route /forecast]
    D --> M[Charts Route /charts]
    G --> H[Prophet Forecast Engine]
    G --> I[Inventory Recommendation Engine]
    G --> N[What-If Scenario Engine]
    E --> J[Decision Support KPIs]
    F --> K[Exploratory Visual Analysis]
    M --> O[Combined Visual Analytics]
    I --> L[Reorder and Safety Stock Outputs]
    N --> P[Scenario Comparison Outputs]
```

## 5. Data Source and Data Handling
Dataset files in this repository:
- `sales.csv` (raw transactional dataset)
- `sales_CLEANED.csv` (cleaned daily category-level data)
- `cleaned_monthly_sales.csv` (monthly aggregate)

Observed dataset scale:
- Raw rows: 286,392 lines (including header)
- Cleaned rows: 4,684 lines (including header)

Cleaning steps implemented in `cleaning.py`:
- Filter valid statuses (`received`, `complete`)
- Drop irrelevant/PII columns
- Remove missing values in essential fields
- Remove invalid qty/price values
- Convert dates to datetime
- Aggregate to category-date level
- Cap outliers per category
- Remove rare low-signal categories

## 6. Technologies Used
- Python 3
- Flask
- Pandas
- NumPy
- Prophet (forecasting)
- HTML/CSS/Chart.js (dashboard frontend)
- Pytest (test validation)

## 7. Features
- Login page (`/login`)
  - Username/password authentication with flask-login
  - All pages are login-protected
- Home dashboard (`/`)
  - Revenue, profit, transactions, quantity KPIs
  - Top categories by units and revenue
  - Quantity trend and revenue mix charts
  - DSS reorder recommendations table
- EDA dashboard (`/eda`)
  - Monthly trend charts
  - Weekday demand distribution
  - Price band analysis (polar area chart)
  - Category mix bubble chart
  - Top categories by quantity and revenue
- Forecast page (`/forecast`)
  - Category selection and forecast horizon
  - Adjustable lead time and service level inputs
  - Future demand projections with confidence bounds
  - Inventory recommendation (reorder point, safety stock, target stock)
  - **What-if scenario comparison**: change lead time or service level to see side-by-side impact on reorder point, safety stock, and target stock vs the base defaults
- Charts page (`/charts`)
  - Combined visualization hub with 8 chart types
  - Revenue trend, revenue mix doughnut, weekday demand bar, price band polar area
  - Volume vs SKU combo chart, category bubble chart
  - Forecast trend and confidence range charts
  - Filter by date range, category, top-N, and forecast days

## 8. Installation and Run
### Prerequisites
- Python 3.10+ recommended

### Setup
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install pytest
```

### Run the app
```bash
python app.py
```
Then open:
- http://127.0.0.1:5000/ (Home dashboard)
- http://127.0.0.1:5000/eda (EDA analysis)
- http://127.0.0.1:5000/forecast (Forecast + what-if scenarios)
- http://127.0.0.1:5000/charts (Combined charts page)

### Run tests
```bash
python -m pytest -q
```

## 9. Repository Structure
```text
app.py
cleaning.py
python_clean_file.py
generate_report.py
requirements.txt
sales.csv
sales_CLEANED.csv
cleaned_monthly_sales.csv
Templates/
  index.html
  eda.html
  forecast.html
  charts.html
  login.html
  home.html
static/
  styles.css
tests/
  test_app.py
```

## 10. Screenshots
Add screenshots before submission:
- Home KPI dashboard
- EDA dashboard
- Forecast output + inventory recommendation

## 11. Team Members and Contributions
Update this section with your actual team details before final submission.

- Brianna Mireri: Data collection, cleaning pipeline, EDA preparation, Flask integration, UI/dashboard
- David Baya: Forecast model implementation, inventory decision logic, testing and documentation

## 12. Evaluation, Challenges, and Limitations
### Evaluation
- Functional DSS workflow from raw data to decision outputs
- Forecast and recommendation outputs generated interactively by category
- Basic automated tests for metric and data-loading logic

### Challenges
- Data quality and outliers in transactional records
- Balancing model complexity with interpretability for decision-makers
- Integrating forecasting outputs with practical inventory rules

### Limitations
- Current forecast is category-level (not SKU-level)
- External factors (promotions, holidays, seasonality events) are not explicitly modeled

## 13. Conclusion and Recommendations
This project delivers a working DSS artifact that combines DSS theory, practical preprocessing, forecasting, rule-based inventory recommendations, and interactive what-if scenario analysis. It can be extended by:
- introducing SKU-level modeling,
- including richer exogenous variables for forecast improvement,
- adding multi-period scenario simulation with cost optimization.

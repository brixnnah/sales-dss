# Technical Report
## Sales Forecasting & Inventory Optimization Decision Support System

---

| | |
|---|---|
| **Project Title** | Sales Forecasting & Inventory Optimization DSS |
| **System Type** | Web-Based Decision Support System |
| **Technology Stack** | Python, Flask, Prophet, Pandas, Chart.js |
| **Date** | April 2026 |
| **Team Members** | Brianna Mireri · David Baya |

---

## Table of Contents

1. Introduction
2. Literature Background
3. Methodology
4. System Architecture
5. Decision Model Explanation
6. Results and Evaluation
7. Challenges and Limitations
8. Conclusion and Recommendations
9. References

---

## 1. Introduction

### 1.1 Background and Motivation

Retail and supermarket operations generate large volumes of transactional data daily. Despite this data richness, many managers continue to rely on intuition or static spreadsheets when making inventory replenishment decisions. Poor inventory decisions directly translate to lost revenue through stockouts or wasted capital through overstock. A structured, data-driven approach to these decisions is both feasible and necessary.

This project addresses this gap by designing and implementing a functional Decision Support System (DSS) specifically tailored to the domain of sales forecasting and inventory optimization. The system ingests historical sales transaction data, applies statistical forecasting to project future demand, and generates rule-based inventory recommendations that a manager can act on immediately.

### 1.2 Problem Statement

The core decision problem is:

> *Given historical sales data across multiple product categories, how can a retail manager determine how much of each category to reorder, and when, to minimize stockout risk while avoiding excess inventory?*

This is a recurring, semi-structured decision that benefits from system support. Without a DSS, managers must manually aggregate data, estimate trends, and apply arbitrary buffer rules — all of which are error-prone and inconsistent across periods.

### 1.3 Decision-Makers

The primary users of this system are:

- **Inventory Managers** — responsible for purchase order decisions
- **Store Operations Managers** — accountable for shelf availability and waste
- **Category Managers** — focused on performance of individual product groups

### 1.4 Scope and Objectives

The system achieves the following objectives:

1. Transform raw transactional sales data into a clean, analysis-ready dataset.
2. Provide an interactive dashboard visualizing key performance indicators (KPIs).
3. Perform exploratory demand analysis across categories and time periods.
4. Generate short-term (7–90 day) demand forecasts per product category.
5. Compute actionable inventory recommendations (reorder point, safety stock, target stock).
6. Secure access via user authentication so only authorized users interact with sensitive business data.

---

## 2. Literature Background

### 2.1 Decision Support Systems: Core Concepts

A Decision Support System (DSS) is an interactive information system that assists decision-makers in using data and models to solve semi-structured problems (Keen & Morton, 1978). Sprague and Carlson (1982) identified three fundamental components of any DSS:

- **Database Management Subsystem** — stores and retrieves relevant data
- **Model-Based Management Subsystem** — applies analytical or predictive logic
- **User Interface Subsystem** — presents outputs and accepts inputs from decision-makers

This project maps directly to this framework: the cleaned CSV dataset serves as the data layer, Prophet and the inventory formulas form the model layer, and the Flask web application provides the interactive interface.

### 2.2 DSS in Retail and Inventory Management

Retail DSS applications have been studied extensively (Coyle et al., 2013). Common models applied include:

- **Time Series Forecasting** — used to project future demand from historical patterns (Box & Jenkins, 1976; Taylor, 2018)
- **Reorder Point (ROP) Models** — classical inventory management formula that determines when to reorder based on lead time and average demand
- **Safety Stock Models** — statistical buffers based on demand variability and service level targets (Silver, Pyke & Thomas, 2017)

These models are established in operations management literature and represent the industry baseline for automated inventory decisions in retail environments.

### 2.3 Time Series Forecasting with Prophet

Prophet (Taylor & Letham, 2018), developed by Meta, is a decomposable time series forecasting model designed for business data. It models time series as:

$$y(t) = g(t) + s(t) + h(t) + \epsilon_t$$

Where:
- $g(t)$ is the trend component
- $s(t)$ is the seasonality component (weekly, yearly, or custom)
- $h(t)$ is a holiday/special event component
- $\epsilon_t$ is an error term assumed to be normally distributed

Prophet is particularly suited to business sales data because it is robust to missing data, handles multiple seasonality patterns, and provides uncertainty intervals that are meaningful for inventory planning.

### 2.4 Inventory Theory

The classical continuous-review inventory model underpins our recommendation engine:

**Reorder Point (ROP):**
$$ROP = \bar{d} \times L$$

**Safety Stock (SS):**
$$SS = z \times \sigma_d \times \sqrt{L}$$

**Target Stock (TS):**
$$TS = ROP + SS$$

Where $\bar{d}$ is average daily demand, $L$ is lead time in days, $\sigma_d$ is standard deviation of daily demand, and $z$ is the service-level z-score (1.65 for 95% service level).

These formulas allow the system to translate probabilistic forecast outputs into concrete, actionable replenishment quantities.

---

## 3. Methodology

### 3.1 Research Approach

This project follows a Design Science Research (DSR) methodology (Hevner et al., 2004), which emphasizes the creation and evaluation of a functional IT artifact. The five-step process followed was:

1. **Problem identification** — defined the inventory decision problem
2. **Data acquisition and cleaning** — collected and preprocessed real transaction data
3. **Model development** — implemented forecasting and inventory logic
4. **System construction** — integrated models into a usable web application
5. **Evaluation** — validated system outputs and tested routes

### 3.2 Dataset Description

The dataset used is a real-world online supermarket sales dataset sourced from a publicly available e-commerce transactions repository. It contains order-level transaction records covering multiple product categories over a 12-month period.

| Attribute | Value |
|---|---|
| Raw dataset rows | 286,392 |
| Time period | October 2020 – September 2021 |
| Key fields | `order_date`, `category`, `qty_ordered`, `price`, `status`, `sku` |
| Source format | CSV |

### 3.3 Data Cleaning Pipeline

The cleaning pipeline is implemented in `cleaning.py` and performs the following steps in sequence:

**Step 1 — Status Filtering**
Only orders with status `received` or `complete` are retained. Cancelled, refunded, or processing orders are excluded as they do not represent realized demand.

**Step 2 — PII and Irrelevant Column Removal**
Personally identifiable fields (name, email, SSN, phone, address, zip) and business-irrelevant columns (discount amounts, reference numbers) are dropped. This reduces noise and protects data privacy.

**Step 3 — Missing Value Removal**
Rows missing any of the four essential fields — `qty_ordered`, `price`, `order_date`, `category` — are dropped. These records cannot contribute to any analytical calculation.

**Step 4 — Invalid Value Removal**
Records where `qty_ordered ≤ 0` or `price ≤ 0` are removed. These represent data entry errors or returns that would distort demand signals.

**Step 5 — Date Conversion**
The `order_date` field is parsed from string to Python `datetime` format to enable time-based aggregation and filtering.

**Step 6 — Category-Day Aggregation**
Order-line records are aggregated to the category-date level, summing quantities and averaging prices. This produces a clean time series per category suitable for forecasting.

**Step 7 — Outlier Capping**
For each category, daily quantity values above the 99th percentile are capped. This prevents extreme spike events from distorting forecast models without discarding records entirely.

**Step 8 — Rare Category Removal**
Categories appearing on fewer than 5 distinct days are removed as insufficient for time series modeling.

**Cleaning Results:**

| Metric | Value |
|---|---|
| Rows after cleaning | 4,683 |
| Active categories | 15 |
| Date range (cleaned) | 2020-10-01 to 2021-09-29 |
| Reduction ratio | ~98.4% reduction in row count (aggregation effect) |

---

## 4. System Architecture

### 4.1 Overview

The system follows a three-tier Model-View-Controller (MVC) architecture deployed as a local Flask web application.

```
┌─────────────────────────────────────────────────────┐
│                   PRESENTATION LAYER                 │
│   HTML/CSS Templates  +  Chart.js Visualizations     │
│   index.html | eda.html | forecast.html | login.html │
└────────────────────────┬────────────────────────────┘
                         │ HTTP Request/Response
┌────────────────────────▼────────────────────────────┐
│                   APPLICATION LAYER                  │
│              Flask Web Application (app.py)          │
│  Routes: /login  /logout  /  /eda  /forecast         │
│  Auth:   Flask-Login session management              │
│  Logic:  Metric computation, EDA, forecast, DSS recs │
└────────────────────────┬────────────────────────────┘
                         │ pandas / Prophet calls
┌────────────────────────▼────────────────────────────┐
│                     DATA LAYER                       │
│  sales.csv (raw)  →  cleaning.py  →  sales_CLEANED   │
│  cleaned_monthly_sales.csv                           │
└─────────────────────────────────────────────────────┘
```

### 4.2 Component Description

| Component | File | Responsibility |
|---|---|---|
| Data Cleaning Pipeline | `cleaning.py` | Raw CSV → cleaned daily category sales |
| Flask Application | `app.py` | Route handling, data loading, model execution |
| Dashboard Template | `Templates/index.html` | KPI cards, charts, DSS recommendations table |
| EDA Template | `Templates/eda.html` | Statistical profile, trend charts, insights |
| Forecast Template | `Templates/forecast.html` | Forecast output, inventory recommendation table |
| Login Template | `Templates/login.html` | Authentication form |
| Stylesheet | `static/styles.css` | Unified design system for all pages |
| Tests | `tests/test_app.py` | Automated regression tests |

### 4.3 Navigation Flow

```
/login  ──► (authenticated) ──►  /          (Dashboard)
                                  ├──►  /eda       (EDA)
                                  └──►  /forecast  (Forecast)
                                              │
                               /logout ◄──────┘
```

### 4.4 Security Design

User authentication is implemented using Flask-Login with server-side session management. All three data routes (`/`, `/eda`, `/forecast`) are decorated with `@login_required`, ensuring unauthenticated requests are redirected to `/login` before any data is served. Two roles are supported: Administrator and Manager.

---

## 5. Decision Model Explanation

### 5.1 Model Overview

The DSS integrates two decision models:

1. **Predictive Model** — Prophet time series forecasting for future demand estimation
2. **Rule-Based Inventory Model** — classical reorder point and safety stock formulas for stock level recommendations

These two models are integrated so that forecast output directly feeds the inventory recommendation computation.

### 5.2 Prophet Forecasting Model

**Input:** A category-filtered time series of daily `qty_ordered` values.

**Configuration used:**
- Weekly seasonality enabled (business demand varies by day of week)
- Yearly seasonality disabled (dataset spans only 12 months — insufficient for annual pattern identification)
- Daily seasonality disabled (aggregated daily data)
- Confidence interval: 90% (`interval_width=0.90`)

**Minimum data requirement:** At least 7 days of history per category.

**Output per forecast horizon (default 30 days):**
- `date` — forecast date
- `forecast` (yhat) — point estimate of expected daily quantity
- `lower_bound` (yhat_lower) — 90% lower confidence bound
- `upper_bound` (yhat_upper) — 90% upper confidence bound

**Why Prophet?**
Prophet handles irregular business time series well, including gaps, trend changes, and weekly patterns. It requires minimal hyperparameter tuning and produces human-interpretable outputs, making it suited for decision-support applications where users need to trust and explain model outputs.

### 5.3 Inventory Recommendation Engine

Once forecast records are available, the inventory engine computes three critical stock metrics for the selected category:

**Average Daily Demand** ($\bar{d}$):
$$\bar{d} = \frac{\sum_{i=1}^{n} q_i}{n}$$
Computed from the forecast records (clamped at 0 for negative values).

**Reorder Point (ROP):**
$$ROP = \bar{d} \times L$$
Where $L = 14$ days (default lead time).

**Safety Stock (SS):**
$$SS = z \times \sigma_d \times \sqrt{L}$$
Where $z = 1.65$ for a 95% service level and $\sigma_d$ is the standard deviation of historical daily demand for the category.

**Target Stock (TS):**
$$TS = ROP + SS$$

**Dashboard Recommendation Labels (Home page):**

The home dashboard uses a simpler buffer-based rule for the top-N categories overview:

$$\text{Recommended Reorder} = \bar{Monthly\_Avg} \times (1 + 0.10 \times \text{Buffer Months})$$

This allows managers to scale aggressiveness of replenishment by adjusting the buffer months parameter (default: 2 months).

**Status Labels:**
| Condition | Label |
|---|---|
| Recommended Reorder > Monthly Avg × 1.5 | 🔴 Low Stock |
| Recommended Reorder > Monthly Avg × 1.2 | 🟡 Monitor |
| Otherwise | 🟢 Optimal |

### 5.4 EDA Decision Support

The EDA module contributes to the decision-making process by surfacing:

- **Demand concentration** — which categories dominate volume and revenue, informing capital allocation priorities
- **Temporal patterns** — weekday demand distribution, identifying peak replenishment scheduling windows
- **Month-over-month momentum** — signals whether demand is accelerating or contracting, which should modulate reorder aggressiveness

---

## 6. Results and Evaluation

### 6.1 Dataset Summary Statistics

| Metric | Value |
|---|---|
| Total observations (cleaned) | 4,683 rows |
| Active product categories | 15 |
| Analysis period | Oct 2020 – Sep 2021 (12 months) |
| Total gross revenue | $192,119,084 |
| Total units sold | 416,774 |
| Mean unit price | $334.86 |

### 6.2 Top Categories by Sales Volume

| Rank | Category | Total Units |
|---|---|---|
| 1 | Superstore | 61,139 |
| 2 | Mobiles & Tablets | 55,202 |
| 3 | Men's Fashion | 51,518 |
| 4 | Women's Fashion | 42,123 |
| 5 | Appliances | 40,860 |

### 6.3 Top Categories by Revenue

| Rank | Category | Total Revenue |
|---|---|---|
| 1 | Mobiles & Tablets | $86,357,322 |
| 2 | Appliances | $41,743,400 |
| 3 | Entertainment | $29,119,839 |
| 4 | Computing | $7,840,945 |
| 5 | Others | $6,319,471 |

**Key insight:** Mobiles & Tablets ranks 2nd in volume but 1st in revenue by a large margin, indicating high unit prices. This category should be prioritized for safety stock maintenance due to its disproportionate revenue contribution.

### 6.4 Sample Forecast Output — Appliances Category

Running a 30-day forecast on the Appliances category produced the following inventory recommendation:

| Metric | Value |
|---|---|
| Average Monthly Demand | 3,405 units |
| Lead Time | 14 days |
| Reorder Point | 1,598 units |
| Safety Stock | 1,474 units |
| Target Stock | 3,072 units |

This means a manager should initiate a reorder when current Appliances stock falls to 1,598 units, maintaining a buffer of 1,474 units to absorb demand variability during the replenishment lead time.

### 6.5 System Functionality Evaluation

| Feature | Status | Notes |
|---|---|---|
| Data loading and cleaning | ✅ Operational | 286,392 → 4,683 rows after aggregation |
| Dashboard KPI display | ✅ Operational | Revenue, profit, transactions, avg order value |
| Date range filtering | ✅ Operational | Applied across all three main routes |
| Category filtering (EDA) | ✅ Operational | 15 categories available |
| Prophet forecast | ✅ Operational | 7–90 day horizon, per category |
| Inventory recommendation | ✅ Operational | ROP, SS, target stock computed per category |
| User authentication | ✅ Operational | Login/logout with role display |
| Automated tests | ✅ Passing | 3 tests pass (metrics, DSS recs, data loading) |
| Print/export (EDA) | ✅ Operational | Print-friendly layout for report capture |

### 6.6 Test Results

Three automated tests were implemented and passed:

| Test | Description | Result |
|---|---|---|
| `test_compute_daily_metrics_uses_category` | Verifies metrics function returns category-level breakdown | ✅ PASS |
| `test_build_dss_recommendations` | Verifies reorder recommendations are computed correctly | ✅ PASS |
| `test_load_data_has_order_date` | Verifies data loader parses dates correctly | ✅ PASS |

---

## 7. Challenges and Limitations

### 7.1 Challenges Encountered

**Data Quality**
The raw dataset (286,392 rows) contained significant noise: cancelled orders, null values in key fields, negative quantities, and low-frequency categories. The cleaning pipeline required multiple iterations to produce a reliable aggregated time series. Identifying the right granularity (category-day level rather than SKU-day level) was critical to ensuring sufficient data density for Prophet to model seasonality.

**Forecast Horizon vs. Data Volume**
With only 12 months of historical data, yearly seasonality could not be reliably modeled. Prophet's yearly seasonality component was explicitly disabled to prevent the model from fitting spurious annual patterns. This limits the long-term reliability of forecasts beyond 30–60 days.

**Negative Confidence Intervals**
Prophet's uncertainty intervals can extend below zero for low-demand categories. Since demand cannot be negative, the system clamps lower bounds at zero in the inventory calculation. This is statistically expected but may confuse non-technical reviewers during presentation.

**Static User Store**
For this demonstration system, user credentials are stored in plain text in memory. This is appropriate for a course project prototype but would require a proper database-backed hashed credential store in a production deployment.

**Plotly Dependency Warning**
The Prophet library optionally imports Plotly for interactive plots. Since Plotly is not installed, a warning is emitted at startup. This does not affect functionality as the application uses Chart.js for all visualizations independently of Prophet's plotting utilities.

### 7.2 Limitations

| Limitation | Impact | Mitigation Applied |
|---|---|---|
| Category-level forecasting only | Cannot support SKU-level reorder decisions | Acknowledged; documented as future scope |
| Fixed lead time (14 days) | Does not reflect supplier variability | Lead time is exposed as a parameter in the forecast module |
| 95% service level fixed in UI | Manager cannot adjust risk tolerance | Service level logic is parameterized in backend functions |
| Single-year data | Long-term seasonal patterns undetectable | Yearly seasonality disabled in Prophet config |
| No actual inventory balance data | Recommendations assume stock starts at zero | System is advisory; manager supplies current stock context |

---

## 8. Conclusion and Recommendations

### 8.1 Conclusion

This project successfully delivered a functional Decision Support System for retail sales forecasting and inventory optimization. The system integrates all required DSS components: a data pipeline for preprocessing, a predictive model (Prophet) for demand forecasting, a rule-based inventory engine for replenishment decisions, and an interactive Flask web application for decision-maker engagement.

The system addresses a real and recurring semi-structured decision problem — inventory replenishment — where combinations of data-driven forecasting and business rules can meaningfully improve decision quality over unaided human judgment.

All three pages of the application (Dashboard, EDA, Forecast) are functional and provide complementary views: retrospective performance (Dashboard), statistical demand profiling (EDA), and forward-looking decision support (Forecast). User authentication ensures appropriate access control.

The automated test suite confirms that core decision logic functions correctly, and the print/export capability of the EDA page makes it directly usable for operational reporting.

### 8.2 Recommendations for Extension

**Short-term improvements:**
1. Introduce a database backend (SQLite or PostgreSQL) to replace the in-memory user store and enable audit logging of decisions made through the system.
2. Allow the manager to input the current stock on hand on the Forecast page so the recommendation can calculate days-of-stock-remaining rather than just target stock.
3. Add lead time and service level as user-editable inputs on the forecast form to enable scenario comparison.

**Medium-term improvements:**
4. Extend forecasting to SKU level by clustering SKUs into demand groups, enabling more granular replenishment decisions.
5. Incorporate external signals (promotions schedule, public holidays, seasonal events) as Prophet regressors to improve forecast accuracy around peaks.
6. Add a scenario simulator where managers can compare inventory costs under different reorder strategies (just-in-time vs. buffer-heavy).

**Long-term improvements:**
7. Connect the system to a live ERP or POS data feed for real-time decision support rather than batch CSV processing.
8. Implement an Economic Order Quantity (EOQ) model alongside ROP to also optimize order size, not just timing.
9. Add email or notification triggers when a category's projected stock is forecast to drop below the reorder point within the lead time window.

### 8.3 Final Statement

The Sales Forecasting & Inventory Optimization DSS demonstrates how DSS theory, statistical modeling, and practical software engineering can be combined into a system that directly supports managerial decision-making. It is functional, demonstrable, and extensible, fulfilling the objectives of a practical DSS course project.

---

## 9. References

Box, G. E. P., & Jenkins, G. M. (1976). *Time Series Analysis: Forecasting and Control*. Holden-Day.

Coyle, J. J., Langley, C. J., Novack, R. A., & Gibson, B. J. (2013). *Supply Chain Management: A Logistics Perspective* (9th ed.). Cengage Learning.

Hevner, A. R., March, S. T., Park, J., & Ram, S. (2004). Design science in information systems research. *MIS Quarterly, 28*(1), 75–105.

Keen, P. G. W., & Morton, M. S. S. (1978). *Decision Support Systems: An Organizational Perspective*. Addison-Wesley.

Silver, E. A., Pyke, D. F., & Thomas, D. J. (2017). *Inventory and Production Management in Supply Chains* (4th ed.). CRC Press.

Sprague, R. H., & Carlson, E. D. (1982). *Building Effective Decision Support Systems*. Prentice-Hall.

Taylor, S. J., & Letham, B. (2018). Forecasting at scale. *The American Statistician, 72*(1), 37–45.

---

*Report generated: April 2026 | System: Sales Forecasting & Inventory Optimization DSS | Framework: Flask + Prophet*

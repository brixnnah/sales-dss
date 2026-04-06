"""
FINAL CLEANING SCRIPT
For: Online Sales in USA dataset (order line level)
Output: Cleaned daily sales per SKU (time series ready for forecasting)
"""

import pandas as pd

# ==================== 1. LOAD DATA ====================
# Replace 'your_file.xlsx' with your actual file path
df = pd.read_csv('sales.csv')

print(f"Original rows: {len(df)}")

# ==================== 2. FILTER VALID ORDERS ====================
# Keep only orders that represent real sales (not canceled/refunded)
valid_status = ['received', 'complete']
df = df[df['status'].isin(valid_status)]

print(f"After filtering status: {len(df)} rows")

# ==================== 3. DROP IRRELEVANT COLUMNS ====================
# Personal info, location, and transactional noise – not needed for forecasting
cols_to_drop = [
    'Name Prefix', 'First Name', 'Middle Initial', 'Last Name', 'full_name',
    'E Mail', 'SSN', 'Phone No.', 'User Name', 'ref_num', 'bi_st',
    'Place Name', 'County', 'City', 'State', 'Zip', 'Region',
    'Discount_Percent', 'discount_amount'  # optional – remove for simplicity
]
df.drop(columns=[c for c in cols_to_drop if c in df.columns], inplace=True, errors='ignore')

# ==================== 4. REMOVE MISSING VALUES ====================
# Essential columns must have data
essential_cols = ['qty_ordered', 'price', 'order_date', 'sku']
df.dropna(subset=essential_cols, inplace=True)

print(f"After dropping missing values: {len(df)} rows")

# ==================== 5. REMOVE INVALID NUMBERS ====================
df = df[(df['qty_ordered'] > 0) & (df['price'] > 0)]

# ==================== 6. CONVERT DATE ====================
df['order_date'] = pd.to_datetime(df['order_date'])

# ==================== 7. AGGREGATE TO DAILY SALES PER SKU ====================
daily_sales = df.groupby(['sku', 'order_date'])['qty_ordered'].sum().reset_index()

print(f"Daily aggregated rows: {len(daily_sales)}")
print(f"Unique SKUs: {daily_sales['sku'].nunique()}")

# ==================== 8. (OPTIONAL) CAP OUTLIERS ====================
# Cap quantity at 99th percentile per SKU to prevent extreme spikes
def cap_outliers(group):
    upper = group['qty_ordered'].quantile(0.99)
    group['qty_ordered'] = group['qty_ordered'].clip(upper=upper)
    return group

daily_sales = daily_sales.groupby('sku').apply(cap_outliers).reset_index(drop=True)

# ==================== 9. (OPTIONAL) REMOVE RARE SKUS ====================
# Only keep SKUs that appear on at least 5 different days
sku_days = daily_sales.groupby('sku')['order_date'].nunique()
active_skus = sku_days[sku_days >= 5].index
daily_sales = daily_sales[daily_sales['sku'].isin(active_skus)]

print(f"After removing rare SKUs: {daily_sales['sku'].nunique()} SKUs left")

# ==================== 10. SAVE CLEANED DATA ====================
daily_sales.to_csv('sales_CLEANED.csv', index=False)
print("✅ Cleaned data saved as 'sales_CLEANED.csv'")

# Optional: also save a summary of total sales per SKU per month (easier for some forecasts)
daily_sales['year_month'] = daily_sales['order_date'].dt.to_period('M')
monthly_sales = daily_sales.groupby(['sku', 'year_month'])['qty_ordered'].sum().reset_index()
monthly_sales.to_csv('cleaned_monthly_sales.csv', index=False)
print("✅ Monthly aggregated data saved as 'cleaned_monthly_sales.csv'")














































































































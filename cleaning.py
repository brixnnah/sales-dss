"""
Data Cleaning Module for Sales Data
Handles loading, cleaning, and aggregating sales data for forecasting
"""

import pandas as pd


def load_and_clean_data(input_file='sales.csv', output_file='sales_CLEANED.csv'):
    """
    Main cleaning function: loads raw CSV and returns cleaned DataFrame
    
    Parameters:
        input_file (str): Path to raw CSV file
        output_file (str): Path to save cleaned CSV
        
    Returns:
        pd.DataFrame: Cleaned daily sales data
    """
    
    print(f"🔄 Loading data from {input_file}...")
    df = pd.read_csv(input_file)
    print(f"📊 Original rows: {len(df):,}")
    
    # ==================== STEP 1: Filter Valid Orders ====================
    print("\n1️⃣ Filtering valid orders (received/complete status)...")
    valid_status = ['received', 'complete']
    df = df[df['status'].isin(valid_status)]
    print(f"   ✓ Rows after status filter: {len(df):,}")
    
    # ==================== STEP 2: Drop Irrelevant Columns ====================
    print("\n2️⃣ Removing unnecessary columns (PII, location, discounts)...")
    cols_to_drop = [
        'Name Prefix', 'First Name', 'Middle Initial', 'Last Name', 'full_name',
        'E Mail', 'SSN', 'Phone No.', 'User Name', 'ref_num', 'bi_st',
        'Place Name', 'County', 'City', 'State', 'Zip', 'Region',
        'Discount_Percent', 'discount_amount'
    ]
    df.drop(columns=[c for c in cols_to_drop if c in df.columns], inplace=True, errors='ignore')
    print(f"   ✓ Columns reduced: {df.shape[1]} columns remaining")
    
    # ==================== STEP 3: Remove Missing Values ====================
    print("\n3️⃣ Removing rows with missing essential data...")
    essential_cols = ['qty_ordered', 'price', 'order_date', 'category']
    missing_before = len(df)
    df.dropna(subset=essential_cols, inplace=True)
    print(f"   ✓ Removed {missing_before - len(df):,} incomplete rows")
    
    # ==================== STEP 4: Remove Invalid Numbers ====================
    print("\n4️⃣ Removing invalid quantities and prices...")
    invalid_before = len(df)
    df = df[(df['qty_ordered'] > 0) & (df['price'] > 0)]
    print(f"   ✓ Removed {invalid_before - len(df):,} rows with zero/negative values")
    
    # ==================== STEP 5: Convert Date ====================
    print("\n5️⃣ Converting dates to datetime format...")
    df['order_date'] = pd.to_datetime(df['order_date'])
    print(f"   ✓ Date range: {df['order_date'].min().date()} to {df['order_date'].max().date()}")
    
# ==================== 7. AGGREGATE TO DAILY SALES PER CATEGORY ====================
    print("\n6️⃣ Aggregating to daily sales per category...")
    daily_sales = df.groupby(['category', 'order_date']).agg({
        'qty_ordered': 'sum',
        'price': 'mean',
        'sku': 'nunique'  # Count of unique SKUs per category
    }).reset_index()
    daily_sales.rename(columns={'sku': 'unique_skus'}, inplace=True)
    print(f"   ✓ Daily records: {len(daily_sales):,}")
    print(f"   ✓ Unique categories: {daily_sales['category'].nunique()}")
    
# ==================== 8. CAP OUTLIERS ====================
    print("\n7️⃣ Capping outliers at 99th percentile per category...")
    for cat in daily_sales['category'].unique():
        upper = daily_sales[daily_sales['category'] == cat]['qty_ordered'].quantile(0.99)
        daily_sales.loc[daily_sales['category'] == cat, 'qty_ordered'] = \
            daily_sales.loc[daily_sales['category'] == cat, 'qty_ordered'].clip(upper=upper)
    # ==================== 9. REMOVE RARE CATEGORIES ====================
    print("\n8️⃣ Removing categories with < 5 sales days (potential noise)...")
    category_days = daily_sales.groupby('category')['order_date'].nunique()
    active_categories = category_days[category_days >= 5].index
    rare_categories_removed = len(category_days) - len(active_categories)
    daily_sales = daily_sales[daily_sales['category'].isin(active_categories)]
    print(f"   ✓ Removed {rare_categories_removed} rare categories")
    print(f"   ✓ {len(active_categories)} active categories remaining")
    
    print(f"\n✅ CLEANING COMPLETE!")
    print(f"   Final rows: {len(daily_sales):,}")
    print(f"   Final categories: {daily_sales['category'].nunique()}")
    
    return daily_sales


def save_cleaned_data(daily_sales, daily_output='sales_CLEANED.csv', monthly_output='cleaned_monthly_sales.csv'):
    """
    Save cleaned data as daily and monthly aggregates
    
    Parameters:
        daily_sales (pd.DataFrame): Cleaned daily sales data
        daily_output (str): Path to save daily CSV
        monthly_output (str): Path to save monthly CSV
    """
    
    print(f"\n📁 Saving daily data to {daily_output}...")
    daily_sales.to_csv(daily_output, index=False)
    print(f"   ✓ Saved")
    
    print(f"📁 Saving monthly data to {monthly_output}...")
    daily_sales['year_month'] = daily_sales['order_date'].dt.to_period('M')
    monthly_sales = daily_sales.groupby(['category', 'year_month']).agg({
        'qty_ordered': 'sum',
        'price': 'mean',
        'unique_skus': 'max'
    }).reset_index()
    monthly_sales.to_csv(monthly_output, index=False)
    print(f"   ✓ Saved")


if __name__ == '__main__':
    # Run as standalone script
    print("="*60)
    print("SALES DATA CLEANING PIPELINE")
    print("="*60)
    
    try:
        cleaned_data = load_and_clean_data('sales.csv', 'sales_CLEANED.csv')
        save_cleaned_data(cleaned_data)
        print("\n" + "="*60)
        print("✅ ALL DONE! Ready for forecasting.")
        print("="*60)
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("   Make sure 'sales.csv' exists in the current directory")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

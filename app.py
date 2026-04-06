from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import pandas as pd
import numpy as np
from prophet import Prophet
import warnings

warnings.filterwarnings('ignore')

app = Flask(__name__, template_folder='Templates', static_folder='static')
app.secret_key = 'dss-sales-secret-2026'
CSV_PATH = 'sales_CLEANED.csv'

# ── Auth setup ──────────────────────────────────────────────
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access the DSS.'

# Simple in-memory user store (username -> password plain text for demo)
USERS = {
    'admin':   {'password': 'admin123',   'role': 'Administrator'},
    'manager': {'password': 'manager123', 'role': 'Manager'},
}

class User(UserMixin):
    def __init__(self, username):
        self.id = username
        self.role = USERS[username]['role']

@login_manager.user_loader
def load_user(username):
    if username in USERS:
        return User(username)
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user_data = USERS.get(username)
        if user_data and user_data['password'] == password:
            login_user(User(username))
            return redirect(request.args.get('next') or url_for('home'))
        error = 'Invalid username or password.'
    return render_template('login.html', error=error)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


def load_data(csv_path=CSV_PATH):
    """Load cleaned CSV file."""
    df = pd.read_csv(csv_path)
    df['order_date'] = pd.to_datetime(df['order_date'])
    return df.sort_values('order_date')


def build_dss_recommendations(top_products, top_values, buffer_months=2):
    """Create simple reorder recommendations from top monthly demand."""
    recommendations = []
    for product, monthly_avg in zip(top_products, top_values):
        monthly_avg = float(monthly_avg)
        recommended_reorder = int(round(monthly_avg * (1 + (0.10 * buffer_months))))
        recommendations.append({
            'product': str(product),
            'monthly_average': round(monthly_avg, 2),
            'recommended_reorder': recommended_reorder
        })
    return recommendations


def compute_daily_metrics(df, start_date=None, end_date=None, top_n=10):
    """Compute sales metrics aggregated by category."""
    filtered = df.copy()

    if start_date:
        filtered = filtered[filtered['order_date'] >= pd.to_datetime(start_date)]
    if end_date:
        filtered = filtered[filtered['order_date'] <= pd.to_datetime(end_date)]

    if filtered.empty:
        return None

    filtered['sales'] = filtered['qty_ordered'] * filtered['price']
    monthly = filtered.set_index('order_date').resample('ME').agg({
        'qty_ordered': 'sum',
        'sales': 'sum'
    }).reset_index()

    top_qty_products = filtered.groupby('category')['qty_ordered'].sum().nlargest(top_n)
    top_revenue_products = filtered.groupby('category')['sales'].sum().nlargest(top_n)

    sales_values = [float(v) for v in monthly['sales'].tolist()]
    return {
        'total_transactions': int(len(filtered)),
        'total_revenue': float(filtered['sales'].sum()),
        'total_quantity': int(filtered['qty_ordered'].sum()),
        'months': [d.strftime('%Y-%m') for d in monthly['order_date']],
        'revenue_values': sales_values,
        'profit_values': [round(v * 0.30, 2) for v in sales_values],
        'quantity_values': [int(v) for v in monthly['qty_ordered'].tolist()],
        'top_qty_products': top_qty_products.index.astype(str).tolist(),
        'top_qty_values': [int(v) for v in top_qty_products.tolist()],
        'top_revenue_products': top_revenue_products.index.astype(str).tolist(),
        'top_revenue_values': [int(v) for v in top_revenue_products.tolist()]
    }


def compute_eda(df, start_date=None, end_date=None, category=None):
    """Compute exploratory data analysis metrics for the dataset."""
    filtered = df.copy()
    if start_date:
        filtered = filtered[filtered['order_date'] >= pd.to_datetime(start_date)]
    if end_date:
        filtered = filtered[filtered['order_date'] <= pd.to_datetime(end_date)]
    if category:
        filtered = filtered[filtered['category'] == category]

    if filtered.empty:
        return None

    filtered['sales'] = filtered['qty_ordered'] * filtered['price']
    daily = filtered.groupby('order_date').agg({
        'qty_ordered': 'sum',
        'sales': 'sum'
    }).reset_index()

    monthly = filtered.set_index('order_date').resample('ME').agg({
        'qty_ordered': 'sum',
        'sales': 'sum'
    }).reset_index()

    category_qty = filtered.groupby('category')['qty_ordered'].sum().nlargest(10)
    category_sales = filtered.groupby('category')['sales'].sum().nlargest(10)
    weekday = filtered.groupby(filtered['order_date'].dt.day_name())['qty_ordered'].sum()
    weekday = weekday.reindex(['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']).fillna(0)

    price_band_labels = ['< $50', '$50-$150', '$150-$300', '$300-$600', '$600+']
    price_bands = pd.cut(
        filtered['price'],
        bins=[-np.inf, 50, 150, 300, 600, np.inf],
        labels=price_band_labels,
        include_lowest=True,
    )
    price_distribution = (
        filtered.assign(price_band=price_bands)
        .groupby('price_band', observed=False)['qty_ordered']
        .sum()
        .reindex(price_band_labels, fill_value=0)
    )

    category_mix = (
        filtered.groupby('category')
        .agg(
            total_quantity=('qty_ordered', 'sum'),
            total_revenue=('sales', 'sum'),
            avg_price=('price', 'mean'),
        )
        .sort_values('total_revenue', ascending=False)
        .head(8)
        .reset_index()
    )

    sku_values = []
    if 'unique_skus' in filtered.columns:
        monthly_sku = (
            filtered.set_index('order_date')
            .resample('ME')['unique_skus']
            .mean()
            .fillna(0)
            .reset_index()
        )
        sku_values = [int(round(v)) for v in monthly_sku['unique_skus'].tolist()]

    monthly_growth_pct = 0.0
    if len(monthly) >= 2 and float(monthly['sales'].iloc[-2]) != 0:
        monthly_growth_pct = ((float(monthly['sales'].iloc[-1]) - float(monthly['sales'].iloc[-2])) / float(monthly['sales'].iloc[-2])) * 100.0

    busiest_weekday = str(weekday.idxmax()) if not weekday.empty else 'N/A'

    return {
        'date_range': f"{filtered['order_date'].min().date()} - {filtered['order_date'].max().date()}",
        'total_rows': int(len(filtered)),
        'total_categories': int(filtered['category'].nunique()),
        'total_revenue': float(filtered['sales'].sum()),
        'total_quantity': int(filtered['qty_ordered'].sum()),
        'avg_order_value': float((filtered['sales'] / filtered['qty_ordered']).mean()),
        'min_price': float(filtered['price'].min()),
        'median_price': float(filtered['price'].median()),
        'max_price': float(filtered['price'].max()),
        'daily_dates': [d.strftime('%Y-%m-%d') for d in daily['order_date'].tolist()],
        'daily_quantity': [int(v) for v in daily['qty_ordered'].tolist()],
        'daily_revenue': [float(v) for v in daily['sales'].tolist()],
        'monthly_dates': [d.strftime('%Y-%m') for d in monthly['order_date'].tolist()],
        'monthly_quantity': [int(v) for v in monthly['qty_ordered'].tolist()],
        'monthly_revenue': [float(v) for v in monthly['sales'].tolist()],
        'monthly_sku_values': sku_values,
        'top_qty_categories': category_qty.index.astype(str).tolist(),
        'top_qty_values': [int(v) for v in category_qty.tolist()],
        'top_revenue_categories': category_sales.index.astype(str).tolist(),
        'top_revenue_values': [float(v) for v in category_sales.tolist()],
        'weekday_names': weekday.index.tolist(),
        'weekday_values': [int(v) for v in weekday.tolist()],
        'price_band_labels': price_band_labels,
        'price_band_values': [int(v) for v in price_distribution.tolist()],
        'category_mix_labels': category_mix['category'].astype(str).tolist(),
        'category_mix_revenue': [float(v) for v in category_mix['total_revenue'].tolist()],
        'category_mix_quantity': [int(v) for v in category_mix['total_quantity'].tolist()],
        'category_mix_avg_price': [round(float(v), 2) for v in category_mix['avg_price'].tolist()],
        'monthly_growth_pct': round(float(monthly_growth_pct), 2),
        'busiest_weekday': busiest_weekday
    }


def forecast_category_sales(df, category, periods=30):
    """Forecast future daily demand for a category with Prophet."""
    category_data = df[df['category'] == category].copy()
    if len(category_data) < 7:
        return None, 'Need at least 7 days of category history.'

    prophet_df = category_data[['order_date', 'qty_ordered']].rename(
        columns={'order_date': 'ds', 'qty_ordered': 'y'}
    ).reset_index(drop=True)

    model = Prophet(
        yearly_seasonality=False,
        weekly_seasonality=True,
        daily_seasonality=False,
        interval_width=0.90
    )
    model.fit(prophet_df)

    future = model.make_future_dataframe(periods=periods)
    forecast = model.predict(future)

    output = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(periods).copy()
    output['ds'] = output['ds'].dt.strftime('%Y-%m-%d')
    output = output.rename(columns={
        'ds': 'date',
        'yhat': 'forecast',
        'yhat_lower': 'lower_bound',
        'yhat_upper': 'upper_bound'
    })

    return output.to_dict('records'), None


def calculate_reorder_point(df, category, lead_time_days=14):
    """Estimate reorder point from average daily demand."""
    category_data = df[df['category'] == category]
    if category_data.empty:
        return 0

    daily_qty = category_data.groupby(category_data['order_date'].dt.to_period('D'))['qty_ordered'].sum()
    avg_daily = daily_qty.mean()
    return int(round(avg_daily * lead_time_days))


def calculate_safety_stock(df, category, lead_time_days=14, service_level=0.95):
    """Estimate safety stock from demand variability."""
    category_data = df[df['category'] == category]
    if category_data.empty:
        return 0

    daily_qty = category_data.groupby(category_data['order_date'].dt.to_period('D'))['qty_ordered'].sum()
    std_daily = daily_qty.std(ddof=0)
    z_score = 1.65 if service_level >= 0.95 else 1.28
    safety_stock = z_score * std_daily * np.sqrt(lead_time_days)
    return int(round(max(safety_stock, 1)))


def calculate_inventory_recommendation(df, category, forecast_records=None, lead_time_days=14, service_level=0.95):
    """Build a simple inventory recommendation for a category."""
    category_data = df[df['category'] == category]
    if category_data.empty:
        return None

    monthly_avg = category_data.set_index('order_date').resample('ME')['qty_ordered'].sum().mean()
    if forecast_records:
        forecast_avg = float(np.mean([max(0.0, record['forecast']) for record in forecast_records]))
    else:
        forecast_avg = float(category_data.groupby(category_data['order_date'].dt.to_period('D'))['qty_ordered'].sum().mean())

    reorder_point = calculate_reorder_point(df, category, lead_time_days)
    safety_stock = calculate_safety_stock(df, category, lead_time_days, service_level)
    target_stock = int(round(reorder_point + safety_stock))

    return {
        'category': str(category),
        'avg_monthly_demand': round(float(monthly_avg), 2),
        'forecast_daily_avg': round(float(forecast_avg), 2),
        'lead_time_days': int(lead_time_days),
        'service_level': float(service_level),
        'reorder_point': reorder_point,
        'safety_stock': safety_stock,
        'target_stock': target_stock
    }


def build_forecast_visual_context(df, category, forecast_days):
    """Prepare forecast history and projection data for chart rendering."""
    forecast_records = None
    error = None
    history_dates = []
    history_values = []
    forecast_dates = []
    forecast_values = []
    forecast_lower = []
    forecast_upper = []

    if category:
        category_history = (
            df[df['category'] == category]
            .groupby('order_date', as_index=False)['qty_ordered']
            .sum()
            .sort_values('order_date')
        )
        recent_history = category_history.tail(45)
        history_dates = [d.strftime('%Y-%m-%d') for d in recent_history['order_date'].tolist()]
        history_values = [float(v) for v in recent_history['qty_ordered'].tolist()]

        forecast_records, error = forecast_category_sales(df, category, periods=forecast_days)
        if not error:
            forecast_dates = [record['date'] for record in forecast_records]
            forecast_values = [round(float(record['forecast']), 2) for record in forecast_records]
            forecast_lower = [round(float(record['lower_bound']), 2) for record in forecast_records]
            forecast_upper = [round(float(record['upper_bound']), 2) for record in forecast_records]

    return {
        'forecast': forecast_records,
        'error': error,
        'history_dates': history_dates,
        'history_values': history_values,
        'forecast_dates': forecast_dates,
        'forecast_values': forecast_values,
        'forecast_lower': forecast_lower,
        'forecast_upper': forecast_upper,
    }


@app.route('/')
@login_required
def home():
    df = load_data()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    top_n = int(request.args.get('top_n', 10))
    buffer_months = int(request.args.get('buffer_months', 2))

    metrics = compute_daily_metrics(df, start_date, end_date, top_n)
    if metrics is None:
        return render_template(
            'index.html',
            error='No data for selected filters.',
            total_transactions=0,
            total_revenue=0,
            total_profit=0,
            total_quantity=0,
            months=[],
            revenue_values=[],
            profit_values=[],
            quantity_values=[],
            top_qty_products=[],
            top_qty_values=[],
            top_revenue_products=[],
            top_revenue_values=[],
            start_date=start_date,
            end_date=end_date,
            top_n=top_n,
            status_options=[],
            selected_status=[],
            buffer_months=buffer_months,
            dss_recommendations=[],
            current_date=pd.Timestamp.today().strftime('%Y-%m-%d')
        )

    total_profit = metrics['total_revenue'] * 0.30
    dss_recommendations = build_dss_recommendations(
        metrics['top_qty_products'],
        metrics['top_qty_values'],
        buffer_months=buffer_months
    )

    return render_template(
        'index.html',
        error=None,        current_user=current_user,        total_transactions=metrics['total_transactions'],
        total_revenue=round(metrics['total_revenue'], 2),
        total_profit=round(total_profit, 2),
        total_quantity=metrics['total_quantity'],
        months=metrics['months'],
        revenue_values=metrics['revenue_values'],
        profit_values=metrics['profit_values'],
        quantity_values=metrics['quantity_values'],
        top_qty_products=metrics['top_qty_products'],
        top_qty_values=metrics['top_qty_values'],
        top_revenue_products=metrics['top_revenue_products'],
        top_revenue_values=metrics['top_revenue_values'],
        start_date=start_date,
        end_date=end_date,
        top_n=top_n,
        status_options=[],
        selected_status=[],
        buffer_months=buffer_months,
        dss_recommendations=dss_recommendations,
        current_date=pd.Timestamp.today().strftime('%Y-%m-%d')
    )


@app.route('/eda')
@login_required
def eda():
    df = load_data()
    categories = sorted(df['category'].astype(str).unique().tolist())
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    selected_category = request.args.get('category', '')

    summary = compute_eda(df, start_date, end_date, selected_category or None)
    if summary is None:
        return render_template(
            'eda.html',
            error='No data for selected filters.',
            date_range='',
            total_rows=0,
            total_categories=0,
            total_revenue=0,
            total_quantity=0,
            avg_order_value=0,
            min_price=0,
            median_price=0,
            max_price=0,
            monthly_dates=[],
            monthly_quantity=[],
            monthly_revenue=[],
            monthly_sku_values=[],
            top_qty_categories=[],
            top_qty_values=[],
            top_revenue_categories=[],
            top_revenue_values=[],
            weekday_names=[],
            weekday_values=[],
            price_band_labels=[],
            price_band_values=[],
            category_mix_labels=[],
            category_mix_revenue=[],
            category_mix_quantity=[],
            category_mix_avg_price=[],
            monthly_growth_pct=0,
            busiest_weekday='N/A',
            start_date=start_date,
            end_date=end_date,
            categories=categories,
            selected_category=selected_category,
            current_date=pd.Timestamp.today().strftime('%Y-%m-%d')
        )

    return render_template(
        'eda.html',
        error=None,
        date_range=summary['date_range'],
        total_rows=summary['total_rows'],
        total_categories=summary['total_categories'],
        total_revenue=round(summary['total_revenue'], 2),
        total_quantity=summary['total_quantity'],
        avg_order_value=round(summary['avg_order_value'], 2),
        min_price=round(summary['min_price'], 2),
        median_price=round(summary['median_price'], 2),
        max_price=round(summary['max_price'], 2),
        monthly_dates=summary['monthly_dates'],
        monthly_quantity=summary['monthly_quantity'],
        monthly_revenue=summary['monthly_revenue'],
        monthly_sku_values=summary['monthly_sku_values'],
        top_qty_categories=summary['top_qty_categories'],
        top_qty_values=summary['top_qty_values'],
        top_revenue_categories=summary['top_revenue_categories'],
        top_revenue_values=summary['top_revenue_values'],
        weekday_names=summary['weekday_names'],
        weekday_values=summary['weekday_values'],
        price_band_labels=summary['price_band_labels'],
        price_band_values=summary['price_band_values'],
        category_mix_labels=summary['category_mix_labels'],
        category_mix_revenue=summary['category_mix_revenue'],
        category_mix_quantity=summary['category_mix_quantity'],
        category_mix_avg_price=summary['category_mix_avg_price'],
        monthly_growth_pct=summary['monthly_growth_pct'],
        busiest_weekday=summary['busiest_weekday'],
        start_date=start_date,
        end_date=end_date,
        categories=categories,
        selected_category=selected_category,
        current_date=pd.Timestamp.today().strftime('%Y-%m-%d')
    )


@app.route('/forecast')
@login_required
def forecast():
    df = load_data()
    categories = sorted(df['category'].unique().tolist())
    selected_category = request.args.get('category', categories[0] if categories else '')
    forecast_days = int(request.args.get('days', 30))
    forecast_context = build_forecast_visual_context(df, selected_category, forecast_days)
    recommendation = None

    if not forecast_context['error'] and forecast_context['forecast']:
        recommendation = calculate_inventory_recommendation(
            df,
            selected_category,
            forecast_records=forecast_context['forecast'],
            lead_time_days=14,
            service_level=0.95
        )

    return render_template(
        'forecast.html',
        categories=categories,
        selected_category=selected_category,
        days=forecast_days,
        forecast=forecast_context['forecast'],
        recommendation=recommendation,
        error=forecast_context['error'],
        history_dates=forecast_context['history_dates'],
        history_values=forecast_context['history_values'],
        forecast_dates=forecast_context['forecast_dates'],
        forecast_values=forecast_context['forecast_values'],
        forecast_lower=forecast_context['forecast_lower'],
        forecast_upper=forecast_context['forecast_upper'],
        current_date=pd.Timestamp.today().strftime('%Y-%m-%d')
    )


@app.route('/charts')
@login_required
def charts():
    df = load_data()
    categories = sorted(df['category'].astype(str).unique().tolist())
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    top_n = int(request.args.get('top_n', 10))
    forecast_days = int(request.args.get('days', 30))
    selected_category = request.args.get('category', categories[0] if categories else '')

    metrics = compute_daily_metrics(df, start_date, end_date, top_n)
    summary = compute_eda(df, start_date, end_date, selected_category or None)
    forecast_context = build_forecast_visual_context(df, selected_category, forecast_days)

    error = None
    if metrics is None or summary is None:
        error = 'No data for the selected filters.'

    return render_template(
        'charts.html',
        error=error or forecast_context['error'],
        categories=categories,
        selected_category=selected_category,
        start_date=start_date,
        end_date=end_date,
        top_n=top_n,
        days=forecast_days,
        months=[] if metrics is None else metrics['months'],
        revenue_values=[] if metrics is None else metrics['revenue_values'],
        profit_values=[] if metrics is None else metrics['profit_values'],
        quantity_values=[] if metrics is None else metrics['quantity_values'],
        top_qty_products=[] if metrics is None else metrics['top_qty_products'],
        top_qty_values=[] if metrics is None else metrics['top_qty_values'],
        top_revenue_products=[] if metrics is None else metrics['top_revenue_products'],
        top_revenue_values=[] if metrics is None else metrics['top_revenue_values'],
        monthly_dates=[] if summary is None else summary['monthly_dates'],
        monthly_quantity=[] if summary is None else summary['monthly_quantity'],
        monthly_revenue=[] if summary is None else summary['monthly_revenue'],
        monthly_sku_values=[] if summary is None else summary['monthly_sku_values'],
        weekday_names=[] if summary is None else summary['weekday_names'],
        weekday_values=[] if summary is None else summary['weekday_values'],
        price_band_labels=[] if summary is None else summary['price_band_labels'],
        price_band_values=[] if summary is None else summary['price_band_values'],
        category_mix_labels=[] if summary is None else summary['category_mix_labels'],
        category_mix_revenue=[] if summary is None else summary['category_mix_revenue'],
        category_mix_quantity=[] if summary is None else summary['category_mix_quantity'],
        category_mix_avg_price=[] if summary is None else summary['category_mix_avg_price'],
        history_dates=forecast_context['history_dates'],
        history_values=forecast_context['history_values'],
        forecast_dates=forecast_context['forecast_dates'],
        forecast_values=forecast_context['forecast_values'],
        forecast_lower=forecast_context['forecast_lower'],
        forecast_upper=forecast_context['forecast_upper'],
        current_date=pd.Timestamp.today().strftime('%Y-%m-%d')
    )


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sqlite3
from datetime import datetime

# Подключение к базе данных
@st.cache_data
def load_data():
    conn = sqlite3.connect('sales.db')
    sales = pd.read_sql("SELECT * FROM sales", conn)
    goods = pd.read_sql("SELECT * FROM goods", conn)
    categs = pd.read_sql("SELECT * FROM categs", conn)
    stocks = pd.read_sql("SELECT * FROM stocks", conn)
    conn.close()
    
    # Объединение данных с учетом вашей структуры
    df = sales.merge(goods, on='GoodNum') \
              .merge(categs, on='ProductCatNum') \
              .merge(stocks, on='StockNum')
    
    # Преобразование даты и расчет суммы продаж
    df['DocDate'] = pd.to_datetime(df['DocDate'])
    df['SalesSum'] = df['Quant'] * df['Price']
    
    return df

# Загрузка данных
df = load_data()

# Настройка страницы
st.set_page_config(layout="wide", page_title="Анализ продаж")
st.title("📊 Анализ продаж (новая структура)")

# Сайдбар с фильтрами
with st.sidebar:
    st.header("Фильтры")
    
    # Выбор периода
    min_date = df['DocDate'].min().date()
    max_date = df['DocDate'].max().date()
    date_range = st.date_input(
        "Период анализа",
        [min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )
    
    # Выбор аптек
    all_stores = st.checkbox("Все аптеки", value=True)
    if not all_stores:
        selected_stores = st.multiselect(
            "Выберите аптеки",
            df['StockDesc'].unique()
        )
    else:
        selected_stores = df['StockDesc'].unique()

# Фильтрация данных
filtered_df = df[
    (df['DocDate'].dt.date >= date_range[0]) & 
    (df['DocDate'].dt.date <= date_range[1]) &
    (df['StockDesc'].isin(selected_stores))
]

# Визуализации
tab1, tab2, tab3 = st.tabs(["Динамика продаж", "Распределение по категориям", "Топ товары"])

with tab1:
    st.header("Динамика продаж по месяцам для топ-3 категорий")
    
    # Определяем топ-3 категории
    top_categories = filtered_df.groupby('ProductCatDesc')['SalesSum'].sum().nlargest(3).index
    
    # Группировка по месяцам и категориям
    monthly_sales = filtered_df[filtered_df['ProductCatDesc'].isin(top_categories)].groupby(
        [pd.Grouper(key='DocDate', freq='M'), 'ProductCatDesc']
    )['SalesSum'].sum().reset_index()
    
    # Построение графика
    plt.figure(figsize=(12, 6))
    sns.lineplot(
        data=monthly_sales,
        x='DocDate',
        y='SalesSum',
        hue='ProductCatDesc',
        marker='o',
        linewidth=2.5
    )
    plt.title("Динамика продаж топ-3 категорий")
    plt.xlabel("Месяц")
    plt.ylabel("Сумма продаж")
    plt.xticks(rotation=45)
    plt.grid(True, linestyle='--', alpha=0.7)
    st.pyplot(plt)

with tab2:
    st.header("Распределение продаж по категориям")
    
    # Данные для диаграммы
    category_sales = filtered_df.groupby('ProductCatDesc')['SalesSum'].sum().reset_index()
    
    # Построение диаграммы
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.pie(
        category_sales['SalesSum'],
        labels=category_sales['ProductCatDesc'],
        autopct='%1.1f%%',
        startangle=90,
        textprops={'fontsize': 10}
    )
    ax.set_title("Доля категорий в общем объеме продаж", pad=20)
    ax.axis('equal')
    st.pyplot(fig)

with tab3:
    st.header("Топ-5 товаров по выручке")
    
    # Топ товаров
    top_products = filtered_df.groupby('GoodDesc')['SalesSum'].sum().nlargest(5).reset_index()
    
    # Построение графика
    plt.figure(figsize=(12, 6))
    sns.barplot(
        data=top_products,
        x='GoodDesc',
        y='SalesSum',
        palette='viridis'
    )
    plt.title("Топ-5 товаров по выручке")
    plt.xlabel("Товар")
    plt.ylabel("Сумма продаж")
    plt.xticks(rotation=45)
    st.pyplot(plt)

# Дополнительная информация
st.sidebar.markdown("---")
st.sidebar.markdown(f"""
**Статистика за период:**
- Начало: {date_range[0]}
- Конец: {date_range[1]}
- Кол-во аптек: {len(selected_stores)}
- Общая выручка: {filtered_df['SalesSum'].sum():,.2f} руб.
- Всего продаж: {filtered_df['Quant'].sum():,} ед.
""")

# Скачивание отфильтрованных данных
st.sidebar.download_button(
    label="Скачать данные",
    data=filtered_df.to_csv(index=False).encode('utf-8'),
    file_name=f"sales_data_{datetime.now().strftime('%Y%m%d')}.csv",
    mime='text/csv'
)

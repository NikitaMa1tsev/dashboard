import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sqlite3
from datetime import datetime

# Настройка страницы
st.set_page_config(
    layout="wide",
    page_title="📊 Sales Analytics Dashboard",
    page_icon="📊"
)

# Загрузка данных
@st.cache_data
def load_data():
    conn = sqlite3.connect('data/sales.db')
    
    # Чтение таблиц с учетом вашей структуры
    sales = pd.read_sql("SELECT * FROM sales", conn)
    goods = pd.read_sql("SELECT * FROM goods", conn)
    categs = pd.read_sql("SELECT * FROM categs", conn)
    stocks = pd.read_sql("SELECT * FROM stocks", conn)
    conn.close()
    
    # Объединение данных
    df = sales.merge(goods, on='GoodNum') \
             .merge(categs, on='ProductCatNum') \
             .merge(stocks, on='StockNum')
    
    # Преобразование данных
    df['DocDate'] = pd.to_datetime(df['DocDate'])
    df['SalesSum'] = df['Quant'] * df['Price']
    
    return df

# Основное приложение
def main():
    st.title("📊 Анализ продаж аптек")
    df = load_data()
    
    # Сайдбар с фильтрами
    with st.sidebar:
        st.header("Фильтры")
        
        # Выбор периода
        date_range = st.date_input(
            "Период анализа",
            [df['DocDate'].min().date(), df['DocDate'].max().date()],
            min_value=df['DocDate'].min().date(),
            max_value=df['DocDate'].max().date()
        )
        
        # Выбор аптек
        selected_stores = st.multiselect(
            "Выберите аптеки",
            df['StockDesc'].unique(),
            default=df['StockDesc'].unique()[0]
        )
    
    # Фильтрация данных
    filtered_df = df[
        (df['DocDate'].dt.date >= date_range[0]) & 
        (df['DocDate'].dt.date <= date_range[1]) &
        (df['StockDesc'].isin(selected_stores))
    ]
    
    # Визуализации
    tab1, tab2, tab3 = st.tabs(["📈 Динамика", "🍕 Доли", "🏆 Топы"])
    
    with tab1:
        st.header("Динамика продаж")
        top_cats = filtered_df.groupby('ProductCatDesc')['SalesSum'].sum().nlargest(3).index
        monthly_data = filtered_df[filtered_df['ProductCatDesc'].isin(top_cats)].groupby(
            [pd.Grouper(key='DocDate', freq='M'), 'ProductCatDesc']
        )['SalesSum'].sum().reset_index()
        
        fig, ax = plt.subplots(figsize=(12, 6))
        sns.lineplot(
            data=monthly_data,
            x='DocDate',
            y='SalesSum',
            hue='ProductCatDesc',
            marker='o'
        )
        plt.title("Топ-3 категорий по месяцам")
        plt.xticks(rotation=45)
        st.pyplot(fig)
    
    with tab2:
        st.header("Распределение по категориям")
        cat_sales = filtered_df.groupby('ProductCatDesc')['SalesSum'].sum()
        
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.pie(
            cat_sales,
            labels=cat_sales.index,
            autopct='%1.1f%%',
            startangle=90
        )
        st.pyplot(fig)
    
    with tab3:
        st.header("Топ-5 товаров")
        top_products = filtered_df.groupby('GoodDesc')['SalesSum'].sum().nlargest(5)
        
        fig, ax = plt.subplots(figsize=(12, 6))
        sns.barplot(
            x=top_products.values,
            y=top_products.index,
            palette="viridis"
        )
        plt.title("Лучшие товары по выручке")
        st.pyplot(fig)
    
    # Статистика
    st.sidebar.markdown("---")
    st.sidebar.metric("Общая выручка", f"{filtered_df['SalesSum'].sum():,.2f} руб.")
    st.sidebar.metric("Кол-во продаж", filtered_df['Quant'].sum())

if __name__ == "__main__":
    main()

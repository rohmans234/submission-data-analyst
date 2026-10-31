# Proyek Analisis Data: E-Commerce Public Dataset (Olist)

Analisis data pesanan *delivered* Olist (Jan 2017 - Agu 2018) untuk menjawab tiga pertanyaan bisnis:
1. Kategori produk dengan revenue tertinggi dan terendah.
2. State dengan keterlambatan pengiriman tertinggi dan dampaknya pada review score.
3. Segmentasi pelanggan dengan RFM Analysis.

## Struktur Direktori
```
submission
├── dashboard
│   ├── main_data.csv
│   └── dashboard.py
├── data
│   ├── customers_dataset.csv
│   ├── order_items_dataset.csv
│   ├── order_reviews_dataset.csv
│   ├── orders_dataset.csv
│   ├── product_category_name_translation.csv
│   └── products_dataset.csv
├── notebook.ipynb
├── README.md
├── requirements.txt
└── url.txt
```

## Setup Environment
```
python -m venv venv
# Windows: venv\Scripts\activate    |  Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
```

## Menjalankan Dashboard
```
streamlit run dashboard/dashboard.py
```
Dashboard terbuka di http://localhost:8501.

## Menjalankan Notebook
Buka `notebook.ipynb` dari folder `submission` (agar path `data/` terbaca), lalu jalankan semua cell. Cell Cleaning akan menghasilkan ulang `dashboard/main_data.csv`.

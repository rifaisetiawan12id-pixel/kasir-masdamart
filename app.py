import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from streamlit_barcode_scanner import st_barcode_scanner

# Fungsi koneksi ke Google Sheets
def init_connection():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    # Mengambil data dari Streamlit Secrets
    creds_info = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_info, scopes=scope)
    return gspread.authorize(creds)

client = init_connection()

# Membuka Spreadsheet (Pastikan nama file di Google Drive sama persis)
try:
    sh = client.open("Database_MasdaMart")
    sheet_produk = sh.worksheet("Produk")
    sheet_transaksi = sh.worksheet("Transaksi")
except Exception as e:
    st.error(f"Gagal koneksi ke database: {e}")

st.set_page_config(page_title="Kasir Masda Mart", layout="centered")
st.title("🛒 Kasir Masda Mart")

# Menu Navigasi
menu = st.sidebar.selectbox("Menu", ["Kasir (Scan)", "Stok Barang", "Riwayat Transaksi"])

if menu == "Kasir (Scan)":
    st.subheader("Scan Barcode Produk")
    barcode_data = st_barcode_scanner()

    if barcode_data:
        df_produk = pd.DataFrame(sheet_produk.get_all_records())
        # Mencari produk berdasarkan barcode
        item = df_produk[df_produk['barcode'].astype(str) == str(barcode_data)]

        if not item.empty:
            nama = item.iloc[0]['nama_barang']
            harga = item.iloc[0]['harga']
            stok_sekarang = item.iloc[0]['stok']
            
            st.info(f"**Produk:** {nama} | **Harga:** Rp{harga:,}")
            st.write(f"Stok tersedia: {stok_sekarang}")

            if st.button("Bayar & Potong Stok"):
                if stok_sekarang > 0:
                    # Update Stok di Google Sheets
                    idx = item.index[0] + 2 # +2 karena header dan index 0
                    sheet_produk.update_cell(idx, 4, int(stok_sekarang - 1))
                    
                    # Catat Transaksi
                    from datetime import datetime
                    sheet_transaksi.append_row([str(datetime.now()), nama, 1, int(harga)])
                    
                    st.success(f"Transaksi {nama} Berhasil!")
                else:
                    st.error("Stok Habis!")
        else:
            st.warning("Produk tidak terdaftar di database.")

elif menu == "Stok Barang":
    st.subheader("Daftar Stok Masda Mart")
    df_produk = pd.DataFrame(sheet_produk.get_all_records())
    st.table(df_produk)

elif menu == "Riwayat Transaksi":
    st.subheader("Data Penjualan")
    df_transaksi = pd.DataFrame(sheet_transaksi.get_all_records())
    st.dataframe(df_transaksi)

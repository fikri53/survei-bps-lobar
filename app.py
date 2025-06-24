import streamlit as st
st.balloons() # <--- TAMBAHKAN BARIS INI
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Survei Budaya Organisasi BPS Lobar",
    page_icon="📊",
    layout="wide"
)

# --- DAFTAR NILAI (WAJIB DILENGKAPI SESUAI KEBUTUHAN) ---
# Tambahkan opsi kosong di awal agar default-nya tidak terisi
DEFAULT_OPTION = [None]

# Daftar untuk pertanyaan Nilai Pribadi
NILAI_PRIBADI_LIST = DEFAULT_OPTION + [
    'Konsisten', 'Mengutamakan kebersamaan', 'Berani Mengambil Risiko', 
    'Berdedikasi', 'Berprestasi', 'Mengutamakan Kesehatan', 'Kontribusi', 
    'Menyeimbangkan antara urusan Pekerjaan dan pribadi', 'Gigih', 'Peduli'
    # ... LENGKAPI DENGAN SEMUA OPSI NILAI PRIBADI ANDA
]

# Daftar untuk pertanyaan Unit Kerja dan Instansi
NILAI_ORGANISASI_LIST = DEFAULT_OPTION + [
    'Berorientasi kepada kepuasan pelanggan', 'Berani Mengambil Risiko', 
    'Pasif terhadap Perubahan', 'Dapat Diandalkan', 'Ramah', 
    'Melayani Sepenuh Hati', 'Saling Menyalahkan', 'Sharing Knowledge', 
    'Bersikap Positif', 'Berprestasi'
    # ... LENGKAPI DENGAN SEMUA OPSI NILAI ORGANISASI ANDA
]


# --- KONEKSI KE GOOGLE SHEETS ---
try:
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_info(
        st.secrets["google_credentials"], scopes=scopes
    )
    client = gspread.authorize(creds)
    # GANTI NAMA FILE DENGAN NAMA GOOGLE SHEET ANDA
    spreadsheet = client.open("Data Survei Budaya Organisasi BPS Lobar") 
    worksheet = spreadsheet.sheet1
except Exception as e:
    st.error(f"Gagal terhubung ke Google Sheets. Pastikan 'secrets.toml' sudah benar. Error: {e}")
    st.stop()


# --- FUNGSI REUSABLE UNTUK EDITOR PERINGKAT ---
def create_ranking_editor(label, options, key):
    """Membuat widget st.data_editor untuk memilih dan merangking 10 nilai."""
    st.subheader(label)
    st.info(
        "Petunjuk: Pilih 10 nilai dari daftar, kemudian berikan peringkat dari 1 "
        "(paling menggambarkan/penting) hingga 10."
    )
    
    # Buat dataframe awal untuk diisi pengguna
    df_template = pd.DataFrame([{"Pilihan Nilai": None, "Ranking": 0} for _ in range(10)])
    
    # Kembalikan widget data_editor
    return st.data_editor(
        df_template,
        column_config={
            "Pilihan Nilai": st.column_config.SelectboxColumn(
                options=options, required=True
            ),
            "Ranking": st.column_config.NumberColumn(
                "Ranking (1-10)", min_value=1, max_value=10, step=1, required=True
            ),
        },
        hide_index=True,
        num_rows="fixed",
        key=key
    )

# --- FUNGSI REUSABLE UNTUK VALIDASI ---
def validate_editor_data(df, section_name):
    """Memvalidasi sebuah dataframe dari data_editor."""
    errors = []
    if df['Pilihan Nilai'].isnull().any():
        errors.append(f"Di bagian '{section_name}', mohon lengkapi semua 10 pilihan nilai.")
    
    if df['Pilihan Nilai'].duplicated().any():
        errors.append(f"Di bagian '{section_name}', ada duplikasi pilihan nilai. Mohon pilih 10 nilai yang berbeda.")

    expected_ranks = set(range(1, 11))
    actual_ranks = set(df['Ranking'])
    if actual_ranks != expected_ranks:
        errors.append(f"Di bagian '{section_name}', ranking harus unik dari 1 hingga 10.")
        
    return errors


# --- TAMPILAN UTAMA APLIKASI ---
st.title("SIMULASI SURVEI BUDAYA ORGANISASI BPS LOBAR")
st.markdown("---")

with st.form("main_survey_form"):
    # --- BAGIAN INFORMASI RESPONDEN ---
    st.header("Informasi Responden")
    tim_kerja = st.selectbox(
        "1. Tim Kerja", 
        [
            None, 'Umum', 'Hansos dan Analisis', 'Kesra dan Duknaker', 'Neraca',
            'Ekonomi', 'Pertanian', 'Harga', 'IPDS', 'PSS', 'RB dan ZI'
        ]
    )
    jenis_kelamin = st.radio("2. Jenis Kelamin", ["Laki-laki", "Perempuan"], horizontal=True)
    jabatan = st.radio("3. Jabatan", ["Ketua Tim", "Anggota Tim"], horizontal=True)
    st.markdown("---")

    # --- BAGIAN PERTANYAAN PERINGKAT ---
    # Menggunakan fungsi reusable untuk setiap bagian
    
    # 4. NILAI PRIBADI
    df_pribadi = create_ranking_editor(
        "4. NILAI PRIBADI", NILAI_PRIBADI_LIST, "editor_pribadi"
    )
    
    # 5. KONDISI UNIT KERJA SAAT INI
    df_unit_sekarang = create_ranking_editor(
        "5. Kerja Unit Kerja Saat Ini (BPS Lobar)", NILAI_ORGANISASI_LIST, "editor_unit_sekarang"
    )
    
    # 6. BUDAYA UNIT KERJA DIHARAPKAN
    df_unit_harapan = create_ranking_editor(
        "6. Budaya Kerja Unit Kerja yang Diharapkan", NILAI_ORGANISASI_LIST, "editor_unit_harapan"
    )
    
    # 7. KONDISI INSTANSI SAAT INI
    df_instansi_sekarang = create_ranking_editor(
        "7. Budaya Instansi (BPS Secara Keseluruhan) Saat Ini", NILAI_ORGANISASI_LIST, "editor_instansi_sekarang"
    )

    # 8. BUDAYA INSTANSI DIHARAPKAN
    df_instansi_harapan = create_ranking_editor(
        "8. Budaya Instansi (BPS Secara Keseluruhan) yang Diharapkan", NILAI_ORGANISASI_LIST, "editor_instansi_harapan"
    )

    st.markdown("---")
    submitted = st.form_submit_button("Kirim Jawaban", type="primary")


# --- LOGIKA SETELAH SUBMIT ---
if submitted:
    all_errors = []
    
    # Validasi Informasi Responden
    if not tim_kerja:
        all_errors.append("Mohon pilih Tim Kerja Anda.")

    # Validasi setiap editor
    all_errors.extend(validate_editor_data(df_pribadi, "4. Nilai Pribadi"))
    all_errors.extend(validate_editor_data(df_unit_sekarang, "5. Unit Kerja Saat Ini"))
    all_errors.extend(validate_editor_data(df_unit_harapan, "6. Unit Kerja Diharapkan"))
    all_errors.extend(validate_editor_data(df_instansi_sekarang, "7. Instansi Saat Ini"))
    all_errors.extend(validate_editor_data(df_instansi_harapan, "8. Instansi Diharapkan"))

    if all_errors:
        for error in all_errors:
            st.warning(error)
    else:
        # JIKA SEMUA VALID, PROSES DAN KIRIM DATA
        with st.spinner("Sedang mengirim data Anda..."):
            try:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Menyiapkan dataframes dengan kolom kategori
                df_pribadi['Kategori Survei'] = 'Nilai Pribadi'
                df_unit_sekarang['Kategori Survei'] = 'Unit Kerja Saat Ini'
                df_unit_harapan['Kategori Survei'] = 'Unit Kerja Diharapkan'
                df_instansi_sekarang['Kategori Survei'] = 'Instansi Saat Ini'
                df_instansi_harapan['Kategori Survei'] = 'Instansi Diharapkan'
                
                # Menggabungkan semua data menjadi satu dataframe besar
                final_df = pd.concat([
                    df_pribadi, df_unit_sekarang, df_unit_harapan,
                    df_instansi_sekarang, df_instansi_harapan
                ], ignore_index=True)

                # Menambahkan informasi responden
                final_df['Timestamp'] = timestamp
                final_df['Nama Tim'] = tim_kerja
                final_df['Jenis Kelamin'] = jenis_kelamin
                final_df['Jabatan'] = jabatan
                
                # Mengurutkan kolom sesuai header di Google Sheet
                final_df = final_df[[
                    'Timestamp', 'Nama Tim', 'Jenis Kelamin', 'Jabatan', 
                    'Kategori Survei', 'Pilihan Nilai', 'Ranking'
                ]]
                # Mengganti nama kolom agar sesuai
                final_df.rename(columns={'Pilihan Nilai': 'Nilai Budaya'}, inplace=True)
                
                # Mengirim data ke Google Sheets
                rows_to_append = final_df.values.tolist()
                worksheet.append_rows(rows_to_append, value_input_option='USER_ENTERED')

                st.success("Survei berhasil dikirim! Terima kasih atas partisipasi Anda.")
                st.balloons()
                
            except Exception as e:
                st.error("Terjadi kesalahan saat mengirim data. Silakan coba lagi.")
                st.error(f"Detail Error: {e}")
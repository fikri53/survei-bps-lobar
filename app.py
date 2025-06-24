import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Survei Budaya Organisasi BPS Lobar",
    page_icon="📊",
    layout="wide"
)

# --- Inisialisasi Session State ---
if 'survey_submitted' not in st.session_state:
    st.session_state.survey_submitted = False

# --- DAFTAR NILAI ---
DEFAULT_OPTION = [None]
NILAI_PRIBADI_LIST = DEFAULT_OPTION + [
    'Akuntabilitas', 'Adaptif', 'Adil', 'Amanah', 'Ambisius', 'Analitis', 'Asertif', 'Baik Hati', 'Bahagia', 
    'Belas Kasih', 'Berani', 'Berani Mengambil Risiko', 'Berdedikasi', 'Berintegritas', 'Berorientasi pada Hasil', 
    'Berorientasi pada Detail', 'Berorientasi pada Kepuasan Pelanggan', 'Berpikir Terbuka', 'Berpikiran Jauh ke Depan', 
    'Berprestasi', 'Bersahabat', 'Bersikap Hormat', 'Bersikap Positif', 'Bekerja Keras', 'Bekerja Sama dalam Tim', 
    'Bertanggung Jawab secara Sosial', 'Bertanya', 'Bijaksana', 'Cepat', 'Dapat Diandalkan', 'Dapat Dipercaya', 
    'Demokratis', 'Disiplin', 'Efisiensi', 'Efisien', 'Ekspresif', 'Empati', 'Fleksibilitas', 'Fokus pada Masa Depan', 
    'Gigih', 'Hati-hati', 'Humor/Menyenangkan', 'Independen', 'Inisiatif', 'Inovasi', 'Inovatif', 'Inspiratif', 
    'Intuitif', 'Keunggulan', 'Keadilan', 'Keandalan', 'Keaslian', 'Keberagaman', 'Keberanian', 'Kebersamaan', 
    'Kecepatan', 'Kecerdasan', 'Kedermawanan', 'Kegembiraan', 'Kejujuran', 'Kemandirian', 'Kemudahan', 'Kemitraan', 
    'Kepemimpinan', 'Kepastian', 'Kepatuhan', 'Kepedulian', 'Keseimbangan', 
    'Keseimbangan antara Kehidupan dan Pekerjaan', 'Kesehatan', 'Kesinambungan', 'Kesopanan', 'Kestabilan', 
    'Ketangkasan', 'Keterbukaan', 'Ketulusan', 'Kewaspadaan', 'Keyakinan', 'Kolaborasi', 'Kompeten', 'Kompetitif', 
    'Konsisten', 'Kontinuitas', 'Kontribusi', 'Kreatif', 'Kreativitas', 'Kualitas', 'Loyalitas', 'Menghargai', 
    'Menghargai Sesama', 'Mengutamakan Kebersamaan', 'Optimis', 'Otonomi', 'Peduli', 'Pemecahan Masalah', 
    'Pembelajaran', 'Pemberdayaan', 'Penuh Gairah', 'Pengembangan Diri', 'Pengetahuan', 'Penting', 'Percaya Diri', 
    'Perdamaian', 'Perencanaan', 'Persahabatan', 'Profesionalisme', 'Ramah', 'Rasa Hormat', 'Rendah Hati', 'Sabar', 
    'Saling Menghormati', 'Saling Percaya', 'Sederhana', 'Semangat', 'Sharing Knowledge', 'Spiritualitas', 
    'Sportivitas', 'Stabilitas', 'Tepat Waktu', 'Teratur', 'Terbuka', 'Toleransi'
]
NILAI_ORGANISASI_LIST = DEFAULT_OPTION + [
    'Berorientasi kepada kepuasan pelanggan', 'Berani Mengambil Risiko', 'Pasif terhadap Perubahan', 
    'Dapat Diandalkan', 'Ramah', 'Melayani Sepenuh Hati', 'Saling Menyalahkan', 'Sharing Knowledge', 
    'Bersikap Positif', 'Berprestasi'
]

# --- KONEKSI KE GOOGLE SHEETS ---
try:
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(st.secrets["google_credentials"], scopes=scopes)
    client = gspread.authorize(creds)
    spreadsheet = client.open("Data Survei Budaya Organisasi BPS Lobar")
    worksheet = spreadsheet.sheet1
except Exception as e:
    st.error(f"Gagal terhubung ke Google Sheets. Pastikan 'secrets.toml' sudah benar. Error: {e}")
    st.stop()

# --- FUNGSI REUSABLE UNTUK EDITOR PERINGKAT (DENGAN PERUBAHAN) ---
def create_ranking_editor(label, options, key):
    st.subheader(label)
    st.info("Petunjuk: Pilih 10 nilai dari daftar, kemudian berikan peringkat dari 1 (paling menggambarkan/penting) hingga 10.")
    df_template = pd.DataFrame([{"Pilihan Nilai": None, "Ranking": None} for _ in range(10)]) # Mengubah default ranking ke None
    return st.data_editor(
        df_template,
        column_config={
            "Pilihan Nilai": st.column_config.SelectboxColumn(
                "Pilih Nilai Budaya",
                options=options,
                required=True
            ),
            # --- INI BAGIAN YANG DIPERBARUI ---
            "Ranking": st.column_config.SelectboxColumn(
                "Ranking (1-10)",
                help="Beri peringkat dari 1 hingga 10.",
                options=list(range(1, 11)), # Membuat daftar pilihan [1, 2, ..., 10]
                required=True
            ),
        },
        hide_index=True,
        num_rows="fixed",
        key=key
    )

# --- FUNGSI REUSABLE UNTUK VALIDASI ---
def validate_editor_data(df, section_name):
    errors = []
    if df['Pilihan Nilai'].isnull().any():
        errors.append(f"Di bagian '{section_name}', mohon lengkapi semua 10 pilihan nilai.")
    if df['Pilihan Nilai'].duplicated().any():
        errors.append(f"Di bagian '{section_name}', ada duplikasi pilihan nilai. Mohon pilih 10 nilai yang berbeda.")
    
    # Validasi untuk Ranking, pastikan tidak ada yang kosong sebelum divalidasi
    if df['Ranking'].isnull().any():
        errors.append(f"Di bagian '{section_name}', mohon lengkapi semua 10 peringkat.")
    else:
        expected_ranks = set(range(1, 11))
        actual_ranks = set(df['Ranking'].astype(int)) # Konversi ke int untuk perbandingan
        if actual_ranks != expected_ranks:
            errors.append(f"Di bagian '{section_name}', ranking harus unik dari 1 hingga 10.")
            
    return errors

# --- KONDISI TAMPILAN APLIKASI ---
if not st.session_state.survey_submitted:
    st.title("SIMULASI SURVEI BUDAYA ORGANISASI BPS LOBAR")
    st.markdown("---")

    with st.form("main_survey_form"):
        st.header("Informasi Responden")
        tim_kerja = st.selectbox("1. Tim Kerja", [None, 'Umum', 'Hansos dan Analisis', 'Kesra dan Duknaker', 'Neraca', 'Ekonomi', 'Pertanian', 'Harga', 'IPDS', 'PSS', 'RB dan ZI'])
        jenis_kelamin = st.radio("2. Jenis Kelamin", ["Laki-laki", "Perempuan"], horizontal=True)
        jabatan = st.radio("3. Jabatan", ["Ketua Tim", "Anggota Tim"], horizontal=True)
        email_responden = st.text_input("4. Alamat Email Anda (opsional)", placeholder="nama@email.com")
        st.markdown("---")
        st.header("Peringkat Nilai Budaya")

        df_pribadi = create_ranking_editor("5. NILAI PRIBADI", NILAI_PRIBADI_LIST, "editor_pribadi")
        df_unit_sekarang = create_ranking_editor("6. Kerja Unit Kerja Saat Ini (BPS Lobar)", NILAI_ORGANISASI_LIST, "editor_unit_sekarang")
        df_unit_harapan = create_ranking_editor("7. Budaya Kerja Unit Kerja yang Diharapkan", NILAI_ORGANISASI_LIST, "editor_unit_harapan")
        df_instansi_sekarang = create_ranking_editor("8. Budaya Instansi (BPS Secara Keseluruhan) Saat Ini", NILAI_ORGANISASI_LIST, "editor_instansi_sekarang")
        df_instansi_harapan = create_ranking_editor("9. Budaya Instansi (BPS Secara Keseluruhan) yang Diharapkan", NILAI_ORGANISASI_LIST, "editor_instansi_harapan")

        st.markdown("---")
        submitted = st.form_submit_button("Kirim Jawaban", type="primary")

    if submitted:
        all_errors = []
        if not tim_kerja:
            all_errors.append("Mohon pilih Tim Kerja Anda.")
        all_errors.extend(validate_editor_data(df_pribadi, "5. Nilai Pribadi"))
        all_errors.extend(validate_editor_data(df_unit_sekarang, "6. Unit Kerja Saat Ini"))
        all_errors.extend(validate_editor_data(df_unit_harapan, "7. Unit Kerja Diharapkan"))
        all_errors.extend(validate_editor_data(df_instansi_sekarang, "8. Instansi Saat Ini"))
        all_errors.extend(validate_editor_data(df_instansi_harapan, "9. Instansi Diharapkan"))

        if all_errors:
            for error in all_errors:
                st.warning(error)
        else:
            with st.spinner("Sedang merekam jawaban Anda..."):
                try:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    df_pribadi['Kategori Survei'] = 'Nilai Pribadi'
                    df_unit_sekarang['Kategori Survei'] = 'Unit Kerja Saat Ini'
                    df_unit_harapan['Kategori Survei'] = 'Unit Kerja Diharapkan'
                    df_instansi_sekarang['Kategori Survei'] = 'Instansi Saat Ini'
                    df_instansi_harapan['Kategori Survei'] = 'Instansi Diharapkan'
                    
                    final_df = pd.concat([df_pribadi, df_unit_sekarang, df_unit_harapan, df_instansi_sekarang, df_instansi_harapan], ignore_index=True)

                    final_df['Timestamp'] = timestamp
                    final_df['Nama Tim'] = tim_kerja
                    final_df['Jenis Kelamin'] = jenis_kelamin
                    final_df['Jabatan'] = jabatan
                    final_df['Email'] = email_responden
                    
                    final_df = final_df[['Timestamp', 'Nama Tim', 'Jenis Kelamin', 'Jabatan', 'Email', 'Kategori Survei', 'Pilihan Nilai', 'Ranking']]
                    final_df.rename(columns={'Pilihan Nilai': 'Nilai Budaya'}, inplace=True)
                    
                    rows_to_append = final_df.values.tolist()
                    worksheet.append_rows(rows_to_append, value_input_option='USER_ENTERED')
                    
                    st.success("Survei berhasil dikirim! Terima kasih.")
                    st.balloons()
                    time.sleep(2)
                    st.session_state.survey_submitted = True
                    st.rerun()
                    
                except Exception as e:
                    st.error("Terjadi kesalahan saat mengirim data. Silakan coba lagi.")
                    st.error(f"Detail Error: {e}")

else:
    st.title("Terima Kasih! 🙏")
    st.balloons()
    st.markdown("---")
    st.success("Jawaban Anda telah berhasil kami rekam.")
    st.info("Partisipasi Anda sangat berarti untuk kemajuan organisasi kita.")
    
    if st.button("Isi Survei Lagi"):
        st.session_state.survey_submitted = False
        st.rerun()
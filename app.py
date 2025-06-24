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

# --- PERUBAHAN DI SINI: Daftar Nilai Pribadi diperbarui sesuai teks yang Anda berikan ---
RAW_NILAI_PRIBADI = [
    'Konsisten', 'Mengutamakan kebersamaan', 'Berani Mengambil Risiko', 'Berdedikasi', 'Berprestasi',
    'Mengutamakan Kesehatan', 'Kontribusi', 'Menyeimbangkan antara urusan Pekerjaan dan pribadi',
    'Gigih', 'Peduli', 'Visioner', 'Setia', 'Dapat Dipercaya', 'Solutif', 'Berintegritas',
    'Berinisiatif/Proaktif', 'Pendengar yang Baik', 'Memiliki Motivasi', 'Mengutamakan Keamanan',
    'Bijaksana', 'Kreatif', 'Efisien', 'Mandiri', 'Logis', 'Mengutamakan Kualitas', 'Pembelajar',
    'Berpuas Diri', 'Mengutamakan keluarga', 'Materialistis', 'Menyelesaikan Perselisihan',
    'Disiplin', 'Membuat Perubahan', 'Bekerjasama', 'Beretika', 'Pemaaf', 'Efektif',
    'Mampu Mengambil keputusan', 'Sejahtera', 'Otoriter', 'Menjaga Nama Baik', 'Penolong',
    'Memberdayakan', 'Berjiwa Pemimpin', 'Mengutamakan Keselamatan', 'Siap Menghadapi ketidakpastian',
    'Mengelola keuangan', 'Adil', 'Ingin Disukai', 'Antusias', 'Konflik Kepentingan',
    'Humoris/Menyenangkan', 'Pemalas', 'Produktif', 'Bersahabat', 'Unggul', 'Rendah Hati',
    'Tertutup', 'Bertanggung Jawab', 'Interaktif/Komunikatif', 'Toleransi'
]


# Daftar Nilai Organisasi (TETAP SAMA)
RAW_NILAI_ORGANISASI = [
    'Berorientasi kepada kepuasan pelanggan', 'Berani Mengambil Risiko', 'Pasif terhadap Perubahan', 
    'Dapat Diandalkan', 'Ramah', 'Melayani Sepenuh Hati', 'Saling Menyalahkan', 'Sharing Knowledge', 
    'Bersikap Positif', 'Berprestasi', 'Menjaga Kualitas', 'memiliki Tanggung jawab Sosial', 
    'Mengeksploitasi', 'memanipulasi', 'Mengutamakan keamanan', 'terbuka dalam Komunikasi', 
    'berkontribusi', 'Saling Menotong', 'Koruptif', 'Menaati aturan dan kebijakan', 'Birokratis', 
    'memberikan Jaminan Kesejahteraan', 'Menyeimbangkan antara Urusan pekerjaan pribadi', 'Produktif', 
    'Mengapresiasi Karyawan', 'Transparan', 'Memiliki rasa ingin tahu', 'Mendapatkan kejelasan', 
    'mengembangkan kepemimpinan', 'kreatif dan inovatif', 'kepemimpinan yang kurang efektif', 
    'Memenuhi kebutuhan kepegawaian', 'memahami tugas&fungsi pekerjaan', 'Pembelajar', 
    'Menghindati risiko', 'Saling menghargai', 'Memberikan kinerja terbaik', 'memberi dorongan', 
    'melakukan perbaikan berkelanjutan', 'terbuka memberikan masukan', 'Kesediaan mendengarkan', 
    'melempar tanggung jawab', 'lembur', 'bertoleran:', 'berintegritas', 
    'mengkomunikasikan nilai organisasi', 'professional', 'bekerjasama', 'berorientasi pada tujuan', 
    'konsisten', 'kompetitif', 'menyelesaikan perselisihan', 'Jujur', 
    'Menjaga rahasiajabatan &negara', 'merangkul Keberagaman', 'Memegang teguh ideologi Pancasila', 
    'Pemimpin sebagai teladan', 'fokus pada pertumbuhan organisasi', 'memberdayakan SDM (empowering)', 
    'Mengutamakan keselamatan', 'Solutif', 'Berpikir menyeluruh', 'Cermat', 'Disiptin', 
    'Mengelola Sumber daya', 'Silo', 'Bertanggung Jawab', 'Mentoring', 'Adil', 'Peduli', 
    'Konflik Kepentingan', 'efektif dan efisien', 'mengelola sumber daya', 'Berfokus jangka Panjang', 
    'memahami tugas dan fungsi pekerjaan', 'otoriter', 'beretika', 'terbuka menerima masukan', 
    'berbagiinformasi', 'berorientasi pada pencapaian realisasi', 'menaati aturan kebijakan', 
    'melakukan pengembangan profesi', 'melempar tanggungjawab', 'berhati-hati', 
    'siap menghadapi ketidakpastian', 'Antusias', 'fokus pada pengurangan biaya', 'Mendapatkan kejelasan', 
    'menjaga rahasia jabatan dan negara', 'menjaga nama baik ASN instansi dan negara', 
    'tidak menyalahgunakan kewenangan jabatan'
]


# Membuat daftar baru dengan penomoran
NILAI_PRIBADI_LIST = DEFAULT_OPTION + [f"{i+1}. {nilai}" for i, nilai in enumerate(RAW_NILAI_PRIBADI)]
NILAI_ORGANISASI_LIST = DEFAULT_OPTION + [f"{i+1}. {nilai}" for i, nilai in enumerate(RAW_NILAI_ORGANISASI)]


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

# --- FUNGSI REUSABLE UNTUK EDITOR PERINGKAT ---
def create_ranking_editor(label, options, key):
    st.subheader(label)
    st.info("Petunjuk: Pilih 10 nilai dari daftar, kemudian berikan peringkat dari 1 (paling menggambarkan/penting) hingga 10.")
    df_template = pd.DataFrame([{"Pilihan Nilai": None, "Ranking": None} for _ in range(10)])
    return st.data_editor(
        df_template,
        column_config={
            "Pilihan Nilai": st.column_config.SelectboxColumn("Pilih Nilai Budaya", options=options, required=True),
            "Ranking": st.column_config.SelectboxColumn("Ranking (1-10)", help="Beri peringkat dari 1 hingga 10.", options=list(range(1, 11)), required=True),
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
    if df['Ranking'].isnull().any():
        errors.append(f"Di bagian '{section_name}', mohon lengkapi semua 10 peringkat.")
    else:
        expected_ranks = set(range(1, 11))
        actual_ranks = set(df['Ranking'].astype(int))
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
        st.markdown("---")
        st.header("Peringkat Nilai Budaya")

        df_pribadi = create_ranking_editor("4. NILAI PRIBADI", NILAI_PRIBADI_LIST, "editor_pribadi")
        df_unit_sekarang = create_ranking_editor("5. Kerja Unit Kerja Saat Ini (BPS Lobar)", NILAI_ORGANISASI_LIST, "editor_unit_sekarang")
        df_unit_harapan = create_ranking_editor("6. Budaya Kerja Unit Kerja yang Diharapkan", NILAI_ORGANISASI_LIST, "editor_unit_harapan")
        df_instansi_sekarang = create_ranking_editor("7. Budaya Instansi (BPS Secara Keseluruhan) Saat Ini", NILAI_ORGANISASI_LIST, "editor_instansi_sekarang")
        df_instansi_harapan = create_ranking_editor("8. Budaya Instansi (BPS Secara Keseluruhan) yang Diharapkan", NILAI_ORGANISASI_LIST, "editor_instansi_harapan")

        st.markdown("---")
        submitted = st.form_submit_button("Kirim Jawaban", type="primary")

    if submitted:
        all_errors = []
        if not tim_kerja:
            all_errors.append("Mohon pilih Tim Kerja Anda.")
        all_errors.extend(validate_editor_data(df_pribadi, "4. Nilai Pribadi"))
        all_errors.extend(validate_editor_data(df_unit_sekarang, "5. Unit Kerja Saat Ini"))
        all_errors.extend(validate_editor_data(df_unit_harapan, "6. Budaya Kerja Diharapkan"))
        all_errors.extend(validate_editor_data(df_instansi_sekarang, "7. Instansi Saat Ini"))
        all_errors.extend(validate_editor_data(df_instansi_harapan, "8. Instansi Diharapkan"))

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
                    
                    final_df = final_df[['Timestamp', 'Nama Tim', 'Jenis Kelamin', 'Jabatan', 'Kategori Survei', 'Pilihan Nilai', 'Ranking']]
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
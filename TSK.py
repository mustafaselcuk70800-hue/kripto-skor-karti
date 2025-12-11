import streamlit as st
import ccxt
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="Kripto Skor Kartı + İşlem Takip", layout="wide")
st.title("Kripto Skor Kartı + Canlı İşlem Takip")

# ------------------- KRİTERLER -------------------
kriterler = {
    "Alçalan Trend Üstünde": +10, "Alçalan Trend Altında": -10,
    "Alçalan Trend Üstten ReTest (Olumlu)": +5, "Alçalan Trend Alttan ReTest (Olumsuz)": -15,
    "Yükselen Trend Üstünde": +10, "Yükselen Trend Altında": -10,
    "Yükselen Trend Üstten Retest (Olumlu)": +10, "Yükselen Trend Alttan ReTest (Olumsuz)": -15,
    "Yatay Trend Üstünde": +10, "Yatay Trend Altında": -10,
    "Yatay Trend Üstten Retest (Olumlu)": +10, "Yatay Trend Alttan ReTest (Olumsuz)": -15,
    "Tillson T3 MA 200 Üstünde": +5, "Tillson T3 MA 200 Altında": -5,
    "Tillson T3 MA 200 Üstten ReTest (Olumlu)": +5, "Tillson T3 MA 200 Alttan ReTest (Olumsuz)": -5,
    "EMA 200 Üstünde": +5, "EMA 200 Altında": -5,
    "EMA 200 Üstten ReTest (Olumlu)": +5, "EMA 200 Alttan ReTest (Olumsuz)": -5,
    "Yükselen Tepe": +10, "Alçalan Tepe": -10,
    "Yükselen Dip": +10, "Alçalan Dip": -10,
    "Alçalan Trend Üstten Başarılı ReTest (Olumlu)": +15,"Yükselen Trend Alttan Başarılı ReTest (Olumsuz)": -15,
}

# Genel exchange listesi
exchange_options = ['mexc', 'binance', 'gateio', 'bybit']

# ------------------- FİYAT ÇEKME -------------------
@st.cache_data(ttl=10, show_spinner=False)
def get_coin_price(symbol, exchange_name):
    try:
        exchange_class = getattr(ccxt, exchange_name)
        exchange = exchange_class({
            'enableRateLimit': True,
            'timeout': 10000
        })
        ticker = exchange.fetch_ticker(symbol.upper())
        return float(ticker['last'])
    except Exception as e:
        return None

# ------------------- SESSION STATE -------------------
if 'secilenler' not in st.session_state:
    st.session_state.secilenler = {k: False for k in kriterler.keys()}
if "islemde" not in st.session_state:
    st.session_state.islemde = False
if "kayitlar" not in st.session_state:
    st.session_state.kayitlar = []
if "reset_kriterler" not in st.session_state:
    st.session_state.reset_kriterler = False
if "mevcut_fiyat_cache" not in st.session_state:
    st.session_state.mevcut_fiyat_cache = 0.0
if "symbol" not in st.session_state:
    st.session_state.symbol = "BTCUSDT"
if "selected_exchange" not in st.session_state:
    st.session_state.selected_exchange = "binance"
if "giris_fiyat" not in st.session_state:
    st.session_state.giris_fiyat = 0.0
if "adet" not in st.session_state:
    st.session_state.adet = 0.0

# Önceki reset isteğini uygula
if st.session_state.reset_kriterler:
    for k in kriterler.keys():
        st.session_state[f"cb_{k}"] = False
    st.session_state.secilenler = {k: False for k in kriterler.keys()}
    st.session_state.reset_kriterler = False
    st.rerun()

col1, col2 = st.columns([1, 1])

# ------------------- SOL: KRİTERLER -------------------
with col1:
    pozitifler = {k: v for k, v in kriterler.items() if v > 0}
    negatifer = {k: v for k, v in kriterler.items() if v < 0}

    col_poz, col_neg = st.columns(2)

    with col_poz:
        st.markdown("#### Pozitif Etkenler")
        with st.container(border=True):
            for kriter, puan in pozitifler.items():
                checked = st.checkbox(
                    f"{kriter} → **{puan:+}**",
                    value=st.session_state.secilenler[kriter],
                    key=f"cb_{kriter}",
                )
                st.session_state.secilenler[kriter] = checked

    with col_neg:
        st.markdown("#### Negatif Etkenler")
        with st.container(border=True):
            for kriter, puan in negatifer.items():
                checked = st.checkbox(
                    f"{kriter} → **{puan:+}**",
                    value=st.session_state.secilenler[kriter],
                    key=f"cb_{kriter}",
                )
                st.session_state.secilenler[kriter] = checked

    toplam = sum(puan for kriter, puan in kriterler.items() if st.session_state.secilenler.get(kriter, False))
    renk = "green" if toplam > 0 else "red" if toplam < 0 else "gray"
    risk_col, reset_col, save_col = st.columns([3, 1, 1])
    with risk_col:
        st.markdown(f"# RİSK PUANI: <span style='color:{renk}; font-size:60px'>{toplam:+}</span>", unsafe_allow_html=True)
    with reset_col:
        if st.button("Kriterleri Sıfırla"):
            st.session_state.reset_kriterler = True
            st.rerun()
    with save_col:
        if st.button("Verileri Kaydet"):
            secili_exchange = st.session_state.selected_exchange
            fiyat = get_coin_price(st.session_state.symbol, secili_exchange)
            st.session_state.kayitlar.append({
                "Sembol": st.session_state.symbol,
                "Risk Puanı": toplam,
                "Fiyat": fiyat,
                "Tarih": datetime.now(),
            })
            st.success("Kayıt eklendi!")

# ------------------- SAĞ: İŞLEM PANELİ -------------------
with col2:
    st.markdown("### İşlem Takip Paneli")

    col_ex, col_sym = st.columns(2)
    with col_ex:
        selected_exchange = st.selectbox("Exchange Seç", exchange_options, index=exchange_options.index(st.session_state.selected_exchange))
        st.session_state.selected_exchange = selected_exchange
    with col_sym:
        symbol = st.text_input("Sembol Gir", value=st.session_state.symbol).upper()
        st.session_state.symbol = symbol

    # İşlem aç/kapat
    islem_toggle = st.checkbox("İşlem Aç/Kapat", value=st.session_state.islemde)
    st.session_state.islemde = islem_toggle

    with st.container(border=True):
        if st.session_state.islemde:
            st.success("**İŞLEM AÇIK**")
        else:
            st.error("**İŞLEM KAPALI**")

    # Fiyat ve adet bloğu
    with st.container(border=True):
        giris_fiyat = st.number_input(
            "Giriş Noktası Fiyatı (USDT)",
            min_value=0.0,
            value=st.session_state.giris_fiyat,
            step=0.00000001,
            key="giris_fiyat"
        )
        adet = st.number_input(
            "Adet",
            min_value=0.0,
            value=st.session_state.adet,
            step=0.00000001,
            key="adet"
        )

        col_fiyat, col_yenile = st.columns([3, 1])
        mevcut_fiyat = st.session_state.mevcut_fiyat_cache

        with col_fiyat:
            # 🔄 BURASI GÜNCEL: Salt okunur olarak göster
            st.text_input(
                "Mevcut Fiyat (USDT)",
                value=f"{mevcut_fiyat:.10f}",
                disabled=True
            )

        with col_yenile:
            if st.button("Fiyat Yenile"):
                with st.spinner("Fiyat çekiliyor..."):
                    fiyat = get_coin_price(symbol, selected_exchange)
                    if fiyat is not None:
                        st.session_state.mevcut_fiyat_cache = float(fiyat)
                        st.rerun()
                    else:
                        st.warning(f"❌ {symbol} fiyatı alınamadı. Sembolü veya exchange’i kontrol edin.")

    st.info(f"Son güncelleme: {datetime.now().strftime('%H:%M:%S')} | {selected_exchange.upper()}")

    # Kar/Zarar Hesaplama
    if st.session_state.islemde and giris_fiyat > 0 and adet > 0:
        mevcut_fiyat = st.session_state.mevcut_fiyat_cache
        kz_yuzde = ((mevcut_fiyat - giris_fiyat) / giris_fiyat) * 100
        kz_usdt = (mevcut_fiyat - giris_fiyat) * adet

        c1, c2 = st.columns(2)
        with c1:
            renk = "green" if kz_yuzde >= 0 else "red"
            st.markdown(f"### Kar/Zarar %  \n<span style='color:{renk}; font-size:50px'>{kz_yuzde:+.3f}%</span>", unsafe_allow_html=True)
        with c2:
            renk = "green" if kz_usdt >= 0 else "red"
            st.markdown(f"### Kar/Zarar (USDT)  \n<span style='color:{renk}; font-size:50px'>{kz_usdt:+.4f}</span>", unsafe_allow_html=True)

    st.markdown("---")
    cikis_fiyat = st.number_input("Çıkış Noktası Fiyatı (USDT)", min_value=0.0, step=0.00000001, key="cikis")

    if st.button("İşlemi Kapat ve Sonuçları Gör"):
        if st.session_state.islemde and giris_fiyat > 0 and adet > 0 and cikis_fiyat > 0:
            son_yuzde = ((cikis_fiyat - giris_fiyat) / giris_fiyat) * 100
            son_usdt = (cikis_fiyat - giris_fiyat) * adet
            st.success(f"İŞLEM KAPANDI! → {son_yuzde:+.3f}% | {son_usdt:+.4f} USDT")
            st.session_state.islemde = False
            # İsteğe bağlı: işlem bilgilerini sıfırla
        else:
            st.error("İşlem açık değil veya bilgiler eksik!")

# ------------------- KAYITLAR -------------------
st.markdown("---")
if st.session_state.kayitlar:
    df = pd.DataFrame(st.session_state.kayitlar)
    st.subheader("Kayıtlar")
    st.dataframe(df, use_container_width=True)

    if len(df) >= 2:
        st.subheader("Fiyat ve Risk Puanı Grafiği")
        chart_df = df.set_index("Tarih")[["Fiyat", "Risk Puanı"]]
        st.line_chart(chart_df)

st.sidebar.title("Ayarlar")
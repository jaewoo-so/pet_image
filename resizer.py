import io
from datetime import datetime

import cv2
import numpy as np
import streamlit as st
from PIL import Image

# ---------------------------
# App / Performance Settings
# ---------------------------
DPI = 200
MAX_UPLOAD_MB = 15
MAX_OUTPUT_PIXELS = 40_000_000  # hard guardrail for memory safety

st.set_page_config(
    page_title="Pastel Image Resizer",
    page_icon="🖼️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------
# Style (Pastel UI)
# ---------------------------
st.markdown(
    """
    <style>
      :root {
        --bg: #f8f7ff;
        --bg-soft: #fffdf8;
        --card: #ffffff;
        --line: #e7e3ff;
        --mint: #d9f5ee;
        --lavender: #e5ddff;
        --sky: #dff3ff;
        --peach: #ffe7d9;
        --text: #37324d;
        --text-soft: #655f84;
        --primary: #8d7dff;
      }

      .stApp {
        background: linear-gradient(140deg, var(--bg), var(--bg-soft));
        color: var(--text);
      }

      .main .block-container {
        padding-top: 1.4rem;
        padding-bottom: 2rem;
      }

      h1, h2, h3 {
        color: var(--text);
        letter-spacing: 0.01em;
      }

      .app-card {
        background: var(--card);
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 1rem 1.1rem;
        box-shadow: 0 6px 22px rgba(109, 99, 180, 0.08);
      }

      .pill {
        display: inline-block;
        padding: .22rem .7rem;
        border-radius: 999px;
        margin-right: .4rem;
        font-size: 0.85rem;
        font-weight: 600;
      }

      .pill-mint { background: var(--mint); color: #2f6b5a; }
      .pill-sky { background: var(--sky); color: #245d79; }
      .pill-peach { background: var(--peach); color: #845437; }

      .hint {
        color: var(--text-soft);
        font-size: 0.92rem;
      }

      [data-testid="stDownloadButton"] button,
      [data-testid="baseButton-secondary"] {
        border-radius: 12px !important;
      }

      [data-testid="baseButton-primary"] {
        border-radius: 12px !important;
        border: none !important;
        background: linear-gradient(90deg, #9b8cff, #7caefc) !important;
      }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------
# Session bootstrap
# ---------------------------
if "resized_image" not in st.session_state:
    st.session_state["resized_image"] = None
if "uploaded_file_name" not in st.session_state:
    st.session_state["uploaded_file_name"] = ""


# ---------------------------
# Helper functions
# ---------------------------
@st.cache_data(show_spinner=False)
def open_image_from_bytes(raw_bytes: bytes) -> Image.Image:
    return Image.open(io.BytesIO(raw_bytes)).convert("RGB")


@st.cache_data(show_spinner=False)
def resize_image_array(
    image_array: np.ndarray,
    new_width: int,
    new_height: int,
) -> np.ndarray:
    return cv2.resize(image_array, (new_width, new_height), interpolation=cv2.INTER_AREA)


def cm_to_px(length_cm: float, dpi: int) -> int:
    return round(length_cm / 2.54 * dpi)


def safe_filename(raw_name: str) -> str:
    keep = "-_.() "
    cleaned = "".join(ch for ch in raw_name if ch.isalnum() or ch in keep).strip()
    return cleaned or "image"


# ---------------------------
# Header
# ---------------------------
st.title("🖼️ 파스텔 이미지 리사이저")
st.markdown(
    """
    <div class="app-card">
      <span class="pill pill-mint">비율 유지 리사이즈</span>
      <span class="pill pill-sky">고정 DPI 200</span>
      <span class="pill pill-peach">서버 친화적 가드레일</span>
      <p class="hint" style="margin-top:.7rem;">
        업로드한 이미지를 인쇄 기준(cm)으로 손쉽게 맞추고, 리사이즈 후 즉시 다운로드할 수 있습니다.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.write("")


# ---------------------------
# Sidebar controls
# ---------------------------
st.sidebar.header("⚙️ 리사이즈 옵션")
direction = st.sidebar.radio("기준 축", ("가로 기준", "세로 기준"), index=0)
length_cm = st.sidebar.number_input("목표 길이 (cm)", min_value=1.0, max_value=300.0, value=10.0, step=0.5)
file_name_option = st.sidebar.radio(
    "파일 이름 규칙",
    ("원본 앞에 붙이기", "원본 뒤에 붙이기", "원본 유지"),
    index=1,
)
additional_text = st.sidebar.text_input("추가 문자열", value="resized")

st.sidebar.markdown("---")
st.sidebar.caption(f"최대 업로드 크기: {MAX_UPLOAD_MB}MB")
st.sidebar.caption(f"최대 출력 픽셀 수: {MAX_OUTPUT_PIXELS:,} px")


# ---------------------------
# Main content
# ---------------------------
uploaded_file = st.file_uploader("이미지 업로드 (JPG/PNG)", type=["jpg", "jpeg", "png"])

if uploaded_file is None:
    st.info("이미지를 업로드하면 원본/결과를 나란히 볼 수 있어요.")
else:
    file_size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
    if file_size_mb > MAX_UPLOAD_MB:
        st.error(f"파일 크기가 {MAX_UPLOAD_MB}MB를 초과했습니다. 더 작은 파일을 업로드해주세요.")
        st.stop()

    original_image = open_image_from_bytes(uploaded_file.getvalue())
    original_width, original_height = original_image.size
    original_ratio = original_width / original_height if original_height else 1

    if direction == "가로 기준":
        new_width = cm_to_px(length_cm, DPI)
        new_height = max(1, round(new_width / original_ratio))
    else:
        new_height = cm_to_px(length_cm, DPI)
        new_width = max(1, round(new_height * original_ratio))

    total_pixels = new_width * new_height
    if total_pixels > MAX_OUTPUT_PIXELS:
        st.error(
            "요청한 크기가 너무 커서 서버 안정성에 영향을 줄 수 있습니다. "
            "길이(cm)를 줄여 다시 시도해주세요."
        )
        st.stop()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("원본")
        st.image(original_image, use_container_width=True)
        st.caption(f"{original_width} x {original_height} px")

    with col2:
        st.subheader("리사이즈 결과")
        if st.button("리사이즈 실행", type="primary", use_container_width=True):
            with st.spinner("이미지 처리 중..."):
                arr = np.array(original_image)
                resized = resize_image_array(arr, new_width, new_height)
                st.session_state["resized_image"] = resized
                st.session_state["uploaded_file_name"] = uploaded_file.name

        if st.session_state["resized_image"] is not None:
            st.image(st.session_state["resized_image"], channels="RGB", use_container_width=True)
            w_real_cm = new_width / DPI * 2.54
            h_real_cm = new_height / DPI * 2.54
            st.success(f"출력 크기: 가로 {w_real_cm:.2f}cm × 세로 {h_real_cm:.2f}cm")
        else:
            st.warning("'리사이즈 실행' 버튼을 눌러 결과를 생성하세요.")

    if st.session_state["resized_image"] is not None:
        img_pil = Image.fromarray(st.session_state["resized_image"])
        buf = io.BytesIO()
        img_pil.save(buf, format="JPEG", dpi=(DPI, DPI), quality=92, optimize=True)
        buf.seek(0)

        original_filename = safe_filename(st.session_state["uploaded_file_name"])
        name_body = original_filename.rsplit(".", 1)[0]
        safe_text = safe_filename(additional_text)

        if file_name_option == "원본 앞에 붙이기":
            download_filename = f"{safe_text}_{name_body}.jpg"
        elif file_name_option == "원본 뒤에 붙이기":
            download_filename = f"{name_body}_{safe_text}.jpg"
        else:
            download_filename = f"{name_body}.jpg"

        st.download_button(
            label="📥 이미지 다운로드",
            data=buf,
            file_name=download_filename,
            mime="image/jpeg",
            use_container_width=True,
        )

st.caption(f"Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")

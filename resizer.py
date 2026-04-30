import streamlit as st
import cv2
import numpy as np
from PIL import Image
import io
import base64

dpi = 200

# 앱 타이틀 및 구분선
st.title('이미지 리사이저')
st.markdown('---')  # 구분선

# 세션 상태 초기화
if 'resized_image' not in st.session_state:
    st.session_state['resized_image'] = None
if 'original_image' not in st.session_state:
    st.session_state['original_image'] = None
if 'original_width' not in st.session_state:
    st.session_state['original_width'] = None
if 'original_height' not in st.session_state:
    st.session_state['original_height'] = None
if 'uploaded_file' not in st.session_state:
    st.session_state['uploaded_file'] = None
if 'additional_text' not in st.session_state:
    st.session_state['additional_text'] = ''



# 사용자 입력 받기
direction = st.radio('사이즈 지정', ('가로 지정', '세로 지정'))
length_cm = st.number_input('길이(cm): ', min_value=0.0, step=0.5)
st.session_state['uploaded_file'] = st.file_uploader("이미지 업로드", type=["jpg", "png"])

if st.session_state['uploaded_file'] is not None:
    bytes_data = st.session_state['uploaded_file'].getvalue()
    st.session_state['original_image'] = Image.open(io.BytesIO(bytes_data))
    st.session_state['original_width'], st.session_state['original_height'] = st.session_state['original_image'].size
    st.session_state['original_image'] = Image.open(io.BytesIO(bytes_data))
    st.image(st.session_state['original_image'], caption='업로드된 이미지', use_column_width=True)
else:
    st.write("이미지를 업로드해주세요.")

# 리사이즈 처리
r_btn = st.button('리사이즈')
if r_btn and st.session_state['uploaded_file'] is not None:
    # 비율에 따른 리사이즈
    if direction == '가로 지정':
        new_width = round(length_cm / 2.54 * dpi)
        resize_ratio = new_width / st.session_state['original_width']
        new_height = round(st.session_state['original_height'] * resize_ratio)
        
    else:  # '세로 지정'
        new_height = round(length_cm / 2.54 * dpi)
        resize_ratio = new_height / st.session_state['original_height']
        new_width = round(st.session_state['original_width'] * resize_ratio)
    w_real_result = new_width / dpi * 2.54
    h_real_result = new_height / dpi * 2.54
    st.write(f"실제 출력 크기: 가로 {w_real_result:.2f} cm |  세로 {h_real_result:.2f} cm ")

    resized_image = np.array(st.session_state['original_image'].convert('RGB'))
    st.session_state['resized_image'] = cv2.resize(resized_image, (int(new_width), int(new_height)))
    st.image(st.session_state['resized_image'], caption='리사이즈된 이미지', channels="RGB", use_column_width=True)
else:
    if r_btn and not st.session_state['uploaded_file']:
        st.warning('이미지를 업로드해주세요.')

# 파일 이름 설정 옵션
file_name_option = st.radio("파일 이름 변경 옵션:",
                            ('원본파일명 앞에 붙이기', '원본파일명 뒤에 붙이기', '아무것도 안붙이기'))
st.session_state.additional_text = st.text_input("저장시 추가될 문자:")

# 다운로드 버튼 생성
if st.session_state['resized_image'] is not None:
    # PIL 이미지로 변환
    img_pil = Image.fromarray(st.session_state['resized_image'])
    # 버퍼에 이미지 저장
    buf = io.BytesIO()
    img_pil.save(buf, format="JPEG",dpi=(200, 200))
    # 버퍼를 처음으로 되돌리기
    buf.seek(0)

    # 파일 이름 정의
    original_filename = st.session_state['uploaded_file'].name
    if file_name_option == '원본파일명 앞에 붙이기':
        download_filename = f"{st.session_state.additional_text}_{original_filename}"
    elif file_name_option == '원본파일명 뒤에 붙이기':
        download_filename = f"{original_filename.split('.')[0]}_{st.session_state.additional_text}.jpg"
    else:
        download_filename = original_filename  # 아무것도 안 붙이기

    # 다운로드 버튼
    st.download_button(
        label="이미지 다운로드",
        data=buf,
        file_name=download_filename,
        mime="image/jpeg"
    )
else:
    st.warning('이미지를 먼저 리사이즈 해주세요.')
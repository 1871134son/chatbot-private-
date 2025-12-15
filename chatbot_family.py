import streamlit as st
import google.generativeai as genai
import base64
import os

# 1. 페이지 설정
st.set_page_config(
    page_title="우리 가족 사랑방 🏠",
    page_icon="👨‍👩‍👦‍👦",
    layout="centered"
)

# 2. API 키 설정
if "MY_API_KEY" in st.secrets:
    MY_API_KEY = st.secrets["MY_API_KEY"]
else:
    st.error("🚨 API 키가 없습니다! Secrets 설정을 확인해주세요.")
    st.stop()

genai.configure(api_key=MY_API_KEY)

# 3. 모델 찾기 (캐싱)
@st.cache_resource
def find_best_model():
    try:
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        preferred_order = [
            "models/gemini-1.5-flash",
            "models/gemini-1.5-flash-latest",
            "models/gemini-1.5-pro",
            "models/gemini-pro"
        ]
        
        for p in preferred_order:
            if p in available_models:
                return p
        
        for m in available_models:
            if "gemini" in m:
                return m
        return None
    except:
        return None

# 4. 배경 및 스타일 설정 (여기가 핵심 수정!)
@st.cache_data
def get_base64_image(image_file):
    if not os.path.exists(image_file):
        return None
    with open(image_file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_bg(image_file):
    b64 = get_base64_image(image_file)
    bg_style = f'background-image: linear-gradient(rgba(255,255,255,0.5), rgba(255,255,255,0.5)), url("data:image/jpeg;base64,{b64}");' if b64 else 'background-color: #f0f2f6;'

    page_bg_img = f'''
    <style>
    [data-testid="stAppViewContainer"] {{
        {bg_style}
        background-size: 50%;
        background-position: center center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    
    /* [핵심] 채팅 말풍선: 무조건 흰색 배경에 검은 글씨 */
    [data-testid="stChatMessage"] {{
        background-color: #ffffff !important; /* 배경은 완전 흰색 */
        border: 1px solid #e0e0e0 !important; /* 테두리 살짝 */
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        border-radius: 15px;
    }}

    /* [초강력 수정] 말풍선 안의 모든 요소를 강제로 검은색으로 고정 */
    [data-testid="stChatMessage"] * {{
        color: #000000 !important; /* 일반 글씨 검은색 */
        -webkit-text-fill-color: #000000 !important; /* 모바일 브라우저 강제 색칠 방지 */
    }}

    /* [안전장치] 혹시 몰라 태그별로 한 번 더 지정 */
    [data-testid="stChatMessage"] p, 
    [data-testid="stChatMessage"] div, 
    [data-testid="stChatMessage"] span, 
    [data-testid="stChatMessage"] li {{
        color: #000000 !important;
    }}
    
    /* 사용자 이름(아이콘 옆)도 검게 */
    [data-testid="stChatMessage"] .stMarkdown h1, 
    [data-testid="stChatMessage"] .stMarkdown h2, 
    [data-testid="stChatMessage"] .stMarkdown h3 {{
        color: #000000 !important;
    }}
    
    /* 입력창 글씨 설정 */
    .stChatInput textarea {{
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        caret-color: #000000 !important; /* 커서 깜빡임도 검게 */
    }}

    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    </style>
    '''
    st.markdown(page_bg_img, unsafe_allow_html=True)

set_bg('family.jpg') 

# 5. 사이드바
with st.sidebar:
    st.title("👨‍👩‍👦‍👦 가족 선택")
    selected_user = st.radio(
        "누구랑 대화하시겠어요?",
        ("아버지 (손기혁)", "어머니 (김영숙)", "막내 (손준호)"),
        index=0
    )

user_name = selected_user.split('(')[1].replace(')', '')

def get_system_instruction(user):
    base = "너는 이 가족을 끔찍이 아끼는 AI 비서야. 한국어로 따뜻하게 대답해."
    if "손기혁" in user:
        return base + " (대상: 손기혁님 - 71년생 부친, 국방과학연구소, 암투병, 시 문학, 존댓말)"
    elif "김영숙" in user:
        return base + " (대상: 김영숙님 - 71년생 모친, 어린이집 교사, 감수성, 요리/건강, 공감 대화)"
    else:
        return base + " (대상: 손준호님 - 03년생 남동생, 보안전공, 재테크, 멘탈케어, 반존대)"

# 6. 채팅 로직
if "current_user" not in st.session_state:
    st.session_state.current_user = selected_user

if st.session_state.current_user != selected_user:
    st.session_state.messages = [] 
    st.session_state.chat_session = None 
    st.session_state.current_user = selected_user
    st.rerun()

if "chat_session" not in st.session_state or st.session_state.chat_session is None:
    best_model_name = find_best_model()
    if best_model_name:
        try:
            model = genai.GenerativeModel(best_model_name, system_instruction=get_system_instruction(selected_user))
            st.session_state.chat_session = model.start_chat(history=[])
            greeting = f"{user_name}님! 오늘도 행복한 하루 보내세요 🍀"
            st.session_state.messages = [{"role": "assistant", "content": greeting}]
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.error("모델 연결 실패")

# 7. 화면 출력
st.title(f"{user_name}님 전용 상담소 💬")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if prompt := st.chat_input("메시지를 입력하세요..."):
    with st.chat_message("user"):
        st.write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    if st.session_state.chat_session:
        try:
            response = st.session_state.chat_session.send_message(prompt)
            with st.chat_message("assistant"):
                st.write(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except:
            st.error("응답 오류")

import streamlit as st
import openai
import json
from datetime import datetime

openai.api_key = st.secrets["openai_api_key"]

st.set_page_config(page_title="종민 GPT 자금비서", page_icon="💸", layout="centered")

st.title("💸 종민 GPT 자금비서")

menu = st.sidebar.selectbox("메뉴 선택", ["지출 입력", "생활비 확인", "대출 기록", "카드 정보"])

def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

expenses = load_json("expenses.json", [])
loans = load_json("loan_log.json", [])
cards = load_json("card_info.json", {})
config = load_json("config.json", {"fixed": {}, "extra": {}, "loan_info": {}})

if menu == "지출 입력":
    st.subheader("📝 오늘 쓴 돈 기록하기")
    text = st.text_input("예: 오늘 커피 5천원 썼어")
    if st.button("GPT로 분류하고 저장"):
        prompt = f"다음 문장에서 날짜, 항목, 금액을 JSON 형식으로 분리해줘: "{text}""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            parsed = json.loads(response.choices[0].message.content)
            expenses.append(parsed)
            save_json("expenses.json", expenses)
            st.success(f"저장 완료: {parsed}")
        except Exception as e:
            st.error(f"GPT 처리 오류: {e}")

elif menu == "생활비 확인":
    st.subheader("📊 생활비 잔액 및 지출")
    fixed_total = sum(config["fixed"].values()) + sum(config["extra"].values())
    total_spent = sum([e["amount"] for e in expenses])
    income = st.number_input("이번 달 예상 수입", value=1900000)
    remaining = income - fixed_total - total_spent
    st.metric("💰 남은 생활비", f"{remaining:,} 원")
    st.bar_chart({e["item"]: e["amount"] for e in expenses})

elif menu == "대출 기록":
    st.subheader("🏦 대출 납부 기록")
    loan_name = st.selectbox("대출명", list(config["loan_info"].keys()))
    payment = st.number_input("납부한 금액", min_value=0)
    if st.button("납부 기록 저장"):
        rate = config["loan_info"][loan_name]["rate"]
        balance = config["loan_info"][loan_name]["balance"]
        interest = int(balance * (rate / 100 / 12))
        principal = max(0, payment - interest)
        config["loan_info"][loan_name]["balance"] -= principal
        log = {"date": datetime.today().strftime("%Y-%m-%d"), "payment": payment, "principal": principal, "interest": interest}
        loans.append(log)
        save_json("loan_log.json", loans)
        save_json("config.json", config)
        st.success(f"기록 저장됨: {log}")

elif menu == "카드 정보":
    st.subheader("💳 카드 정보 조회")
    if not cards:
        st.info("카드 정보가 없습니다.")
    else:
        for card, info in cards.items():
            st.write(f"**{card}**: {info['number']} / {info['expiry']}")

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from google import genai

# GitHub Secrets에서 환경 변수 불러오기
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL")

def fetch_duty_free_events():
    """면세점 이벤트 페이지 스크래핑"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    url = "https://www.shilladfs.com/estore/kr/ko/event"
    events_summary = []
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        items = soup.select(".event_list li, .event-item, a[href*='event']")[:8]
        for item in items:
            text = item.get_text(strip=True)
            if len(text) > 10:
                events_summary.append(text)
    except Exception as e:
        events_summary.append(f"이벤트 데이터 수집 대체 요약: {e}")
        
    return "\n".join(events_summary) if events_summary else "현재 진행 중인 주요 제휴카드/적립금 이벤트 요약본"

def generate_blog_post(event_text):
    """Gemini API를 이용해 티스토리용 글 생성"""
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = f"""
당신은 여행 및 면세 쇼핑 전문 블로그 '듀티프리 랩'의 전문 에디터입니다.
아래 수집된 최신 면세점 이벤트 정보를 바탕으로 티스토리에 바로 올릴 수 있는 알찬 포스팅을 작성해 주세요.

[수집된 이벤트 데이터]:
{event_text}

[포스팅 필수 구성]:
1. 매력적인 제목 3가지 추천
2. 핵심 혜택 한눈에 보기 (마크다운 표 형식: 구분 / 내용 / 혜택 조건)
3. 상세 할인 & 참여 방법 (결제수단별 페이백, 적립금 다운로드 팁)
4. 에디터 꿀팁 (주류/화장품 등 실전 적용 요령)
5. 추천 해시태그 (쉼표 구분)
"""
    response = client.models.generate_content(
        model="models/gemini-3.6-flash",
        contents=prompt
    )
    return response.text

def send_email(subject, content):
    """SMTP를 이용해 이메일 발송"""
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = subject

    msg.attach(MIMEText(content, 'plain', 'utf-8'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("이메일 발송 성공!")
    except Exception as e:
        print(f"이메일 발송 실패: {e}")
        raise e

def main():
    print("1. 면세점 이벤트 수집 시작...")
    events = fetch_duty_free_events()
    
    print("2. AI 원고 생성 중...")
    post_content = generate_blog_post(events)
    
    today_str = datetime.now().strftime('%Y-%m-%d')
    subject = f"✈️ [듀티프리 랩] {today_str} 면세점 할인 이벤트 포스팅 초안"
    
    print("3. 이메일 발송 중...")
    send_email(subject, post_content)
    print("전체 프로세스 완료!")

if __name__ == "__main__":
    main()

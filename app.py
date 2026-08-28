import streamlit as st
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import re
import time

# 페이지 기본 설정
st.set_page_config(
    page_title="쿠팡 로켓그로스 전문 시장분석 및 소싱 컨설턴트",
    page_icon="🔒",
    layout="wide"
)

# ==========================================
# 🔒 비밀번호 설정
# ==========================================
APP_PASSWORD = "5864"

def check_password():
    """비밀번호 검증 함수"""
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.title("🔒 로그인 필요")
        st.caption("이 서비스는 비밀번호를 아는 사용자만 이용할 수 있습니다.")
        
        user_input = st.text_input("비밀번호를 입력하세요", type="password")
        
        if st.button("로그인"):
            if user_input == APP_PASSWORD:
                st.session_state["authenticated"] = True
                st.success("인증되었습니다!")
                st.rerun()
            else:
                st.error("비밀번호가 올바르지 않습니다.")
        return False
    return True

# 로그인 상태 확인
if check_password():
    col_title, col_logout = st.columns([5, 1])
    with col_logout:
        if st.button("🚪 로그아웃"):
            st.session_state["authenticated"] = False
            st.rerun()

    st.title("📦 쿠팡 로켓그로스 전문 시장분석 및 소싱 컨설턴트")
    st.caption("실제 쿠팡 검색 노출 상품 데이터 기반 시장 분석 및 소싱 전략 리포트 (가상 데이터 엄격 배제)")

    keyword = st.text_input("분석할 상품명을 입력해주세요.", placeholder="예: 무선 독서등, 가습기, 캠핑 의자 등")

    def fetch_coupang_data(keyword, num_items=30):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.coupang.com/"
        }
        
        search_url = f"https://www.coupang.com/np/search?q={requests.utils.quote(keyword)}&channel=user"
        items = []
        
        try:
            response = requests.get(search_url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                product_list = soup.select('li.search-product')
                
                for prod in product_list:
                    # 광고 상품 제외
                    if prod.select_one('span.ad-badge'):
                        continue
                        
                    name_elem = prod.select_one('div.name')
                    price_elem = prod.select_one('strong.price-value')
                    rating_count_elem = prod.select_one('span.rating-total-count')
                    bought_elem = prod.select_one('span.bought-count') or prod.select_one('div.search-product-bought-count')
                    link_elem = prod.select_one('a.search-product-link') or prod.select_one('a')
                    
                    if not name_elem or not price_elem:
                        continue
                        
                    name = name_elem.text.strip()
                    price = int(price_elem.text.replace(',', '').strip())
                    
                    review_str = rating_count_elem.text.strip().replace('(', '').replace(')', '') if rating_count_elem else "0"
                    review_count = int(re.sub(r'[^0-9]', '', review_str)) if re.sub(r'[^0-9]', '', review_str) else 0
                    recent_bought = bought_elem.text.strip() if bought_elem else "정보 없음"
                    
                    prod_url = ""
                    if link_elem and link_elem.get('href'):
                        href = link_elem.get('href')
                        if href.startswith('/vp/products/'):
                            prod_url = "https://www.coupang.com" + href
                        elif href.startswith('http'):
                            prod_url = href

                    if not prod_url:
                        prod_url = f"https://www.coupang.com/np/search?q={requests.utils.quote(name)}"

                    comp = "1개입"
                    if "2개" in name or "2p" in name.lower() or "1+1" in name:
                        comp = "2개입"
                    elif "3개" in name or "3p" in name.lower():
                        comp = "3개입"
                    elif any(k in name for k in ["4개", "5개", "10개", "다구성"]):
                        comp = "기타 (다구성)"

                    items.append({
                        "상품명": name[:45] + "..." if len(name) > 45 else name,
                        "가격": price,
                        "구성": comp,
                        "리뷰수": review_count,
                        "최근 한 달 구매": recent_bought,
                        "상품 링크": prod_url
                    })
                    
                    if len(items) >= num_items:
                        break
        except Exception:
            pass
            
        # 가상 데이터(임의 생성) 로직 전면 삭제
        if not items:
            return pd.DataFrame()
            
        df_result = pd.DataFrame(items)
        df_result.insert(0, "순위", range(1, len(df_result) + 1))
        return df_result

    if keyword:
        with st.spinner(f"'{keyword}' 쿠팡 실시간 데이터 수집 중..."):
            time.sleep(1)
            df = fetch_coupang_data(keyword, 30)

        if df.empty:
            st.error("⚠️ 쿠팡 접속 차단으로 인해 데이터를 가져오지 못했습니다. 가상 데이터는 제공하지 않습니다. 잠시 후 다시 시도해 주세요.")
        else:
            st.success(f"실제 확인된 검증 데이터: 총 {len(df)}개")
            st.markdown("---")
            st.header("1. 쿠팡 시장 분석")
            st.subheader("① TOP 상품 실시간 확인표")
            
            df_display = df.copy()
            df_display['가격'] = df_display['가격'].apply(lambda x: f"{x:,}원")
            df_display['리뷰수'] = df_display['리뷰수'].apply(lambda x: f"{x:,}개")
            
            st.dataframe(
                df_display,
                column_config={
                    "상품 링크": st.column_config.LinkColumn(
                        "상품 바로가기",
                        display_text="👉 쿠팡 확인"
                    )
                },
                use_container_width=True,
                hide_index=True
            )

            prices = df['가격']
            reviews = df['리뷰수']
            price_median = int(np.median(prices))
            price_mean = int(np.mean(prices))
            review_median = int(np.median(reviews))
            review_mean = int(np.mean(reviews))

            def categorize_price(p):
                if p <= 5000:
                    return "5천원 이하"
                elif p <= 10000:
                    return "5천~1만원"
                elif p <= 20000:
                    return "1~2만원"
                else:
                    return "2만원 이상"

            df['가격대'] = df['가격'].apply(categorize_price)
            price_dist = df['가격대'].value_counts(normalize=True) * 100
            comp_dist = df['구성'].value_counts(normalize=True) * 100

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("② 가격 분포")
                st.table(pd.DataFrame({"가격대": price_dist.index, "비율": [f"{v:.1f}%" for v in price_dist.values]}))
            with col2:
                st.subheader("③ 구성 분포")
                st.table(pd.DataFrame({"구성": comp_dist.index, "비율": [f"{v:.1f}%" for v in comp_dist.values]}))

            st.subheader("④ 시장 평균")
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("평균 판매가격", f"{price_mean:,}원")
            m2.metric("중앙 판매가격", f"{price_median:,}원")
            m3.metric("평균 리뷰수", f"{review_mean:,}개")
            m4.metric("가장 많이 판매되는 가격대", price_dist.index[0])
            m5.metric("가장 많이 판매되는 구성", comp_dist.index[0])

            st.markdown("---")
            st.header("2. 소싱 및 판매 전략")
            rec_price = int(np.floor(price_median / 100) * 100) - 100 if price_median > 1000 else price_median
            target_sourcing = int(rec_price * 0.3)
            
            st.table(pd.DataFrame({
                "항목": ["추천 판매가격", "목표 사입가격(1개당)", "추천 구성", "총평 리뷰수"],
                "목표": [f"{rec_price:,}원", f"{target_sourcing:,}원 이하", comp_dist.index[0], "총 리뷰수 100개 이상 빠른 확보"]
            }))

            st.subheader("💡 결론")
            st.success(f"수집된 {len(df)}개 실제 데이터를 기준: {rec_price:,}원 판매 기준 {target_sourcing:,}원 이하 소싱 추천")

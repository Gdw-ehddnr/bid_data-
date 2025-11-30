"""
리콜 데이터 파서
상세 페이지에서 필드 추출 및 정규화
"""
import re
import logging
from typing import Dict, Optional
from scrapy.http import Response
from common.utils import parse_date


logger = logging.getLogger(__name__)


class RecallParser:
    """리콜 데이터 파서"""
    
    # 결함부위 표준화 매핑
    DEFECT_PART_MAPPING = {
        '제동': 'brake',
        '제동장치': 'brake',
        '브레이크': 'brake',
        '엔진': 'engine',
        '변속기': 'transmission',
        '서스펜션': 'suspension',
        '타이어': 'tire',
        '에어백': 'airbag',
        '전기': 'electrical',
        '전자장치': 'electrical',
        '연료': 'fuel',
        '배기': 'exhaust',
        '시트': 'seat',
        '도어': 'door',
        '라이트': 'light',
        '와이퍼': 'wiper',
    }
    
    def parse(self, response: Response, url: str, title: str) -> Dict:
        """
        상세 페이지에서 리콜 데이터 추출
        
        Args:
            response: Scrapy Response 객체
            url: 페이지 URL
            title: 제목
        
        Returns:
            파싱된 데이터 딕셔너리
        """
        # 테이블 기반 데이터 추출 (한국 정부 사이트에서 흔한 패턴)
        table_data = self._extract_from_table(response)
        
        # 제조사 추출 - 여러 패턴 시도
        maker = (
            table_data.get('제조사') or
            table_data.get('제조사명') or
            self._extract_text(response, [
                'td:contains("제조사") + td::text',
                'th:contains("제조사") + td::text',
                'dt:contains("제조사") + dd::text',
                '.maker::text',
                '#maker::text'
            ]) or ''
        )
        
        # 모델 추출 - 여러 패턴 시도
        model = (
            table_data.get('모델') or
            table_data.get('차종') or
            table_data.get('모델명') or
            self._extract_text(response, [
                'td:contains("모델") + td::text',
                'th:contains("모델") + td::text',
                'th:contains("차종") + td::text',
                'dt:contains("모델") + dd::text',
                '.model::text',
                '#model::text'
            ]) or ''
        )
        
        # 연식 추출 및 분리
        model_year = self._extract_model_year(model)
        
        # 결함부위 추출 - 여러 패턴 시도
        defect_part = (
            table_data.get('결함부위') or
            table_data.get('결함내용') or
            table_data.get('결함부품') or
            self._extract_text(response, [
                'td:contains("결함부위") + td::text',
                'td:contains("결함내용") + td::text',
                'th:contains("결함부위") + td::text',
                'dt:contains("결함부위") + dd::text',
                '.defect-part::text',
                '#defect-part::text'
            ]) or ''
        )
        
        # 표준부위 매핑
        defect_part_std = self._map_defect_part(defect_part)
        
        # 증상 추출 - 여러 패턴 시도
        symptom = (
            table_data.get('증상') or
            table_data.get('결함증상') or
            self._extract_text(response, [
                'td:contains("증상") + td::text',
                'th:contains("증상") + td::text',
                'dt:contains("증상") + dd::text',
                '.symptom::text',
                '#symptom::text',
                '.symptom'
            ]) or ''
        )
        
        # 시정조치 추출 - 여러 패턴 시도
        action = (
            table_data.get('시정조치') or
            table_data.get('조치내용') or
            table_data.get('시정방법') or
            self._extract_text(response, [
                'td:contains("시정조치") + td::text',
                'td:contains("조치내용") + td::text',
                'th:contains("시정조치") + td::text',
                'dt:contains("시정조치") + dd::text',
                '.action::text',
                '#action::text',
                '.action'
            ]) or ''
        )
        
        # 시정개시일 추출
        start_date_str = (
            table_data.get('시정개시') or
            table_data.get('시정개시일') or
            self._extract_text(response, [
                'td:contains("시정개시") + td::text',
                'th:contains("시정개시") + td::text',
                'dt:contains("시정개시") + dd::text',
                '.start-date::text',
                '#start-date::text'
            ])
        )
        start_date = parse_date(start_date_str) if start_date_str else None
        
        # 대상대수 추출
        qty_str = (
            table_data.get('대상대수') or
            table_data.get('대상차량수') or
            table_data.get('대상수') or
            self._extract_text(response, [
                'td:contains("대상대수") + td::text',
                'td:contains("대상차량수") + td::text',
                'th:contains("대상대수") + td::text',
                'dt:contains("대상대수") + dd::text',
                '.qty::text',
                '#qty::text'
            ])
        )
        qty = self._extract_number(qty_str) if qty_str else None
        
        # 공지일 추출
        notice_date_str = (
            table_data.get('공지일') or
            table_data.get('등록일') or
            self._extract_text(response, [
                'td:contains("공지일") + td::text',
                'td:contains("등록일") + td::text',
                'th:contains("공지일") + td::text',
                'dt:contains("공지일") + dd::text',
                '.notice-date::text',
                '#notice-date::text'
            ])
        )
        notice_date = parse_date(notice_date_str) if notice_date_str else None
        
        return {
            'maker': maker.strip(),
            'model': model.strip(),
            'model_year': model_year,
            'defect_part': defect_part.strip(),
            'defect_part_std': defect_part_std,
            'symptom': symptom.strip(),
            'action': action.strip(),
            'start_date': start_date,
            'qty': qty,
            'notice_date': notice_date,
            'url': url,
            'title': title.strip()
        }
    
    def _extract_from_table(self, response: Response) -> Dict[str, str]:
        """
        테이블에서 키-값 쌍 추출
        한국 정부 사이트에서 흔한 테이블 구조 파싱
        """
        table_data = {}
        
        # 패턴 1: th/td 구조 (가장 흔한 패턴)
        rows = response.css('table tr')
        for row in rows:
            th = row.css('th::text').get()
            td = row.css('td::text').getall()
            if th and td:
                key = th.strip()
                value = ' '.join([t.strip() for t in td if t.strip()])
                if key and value:
                    table_data[key] = value
        
        # 패턴 2: 첫 번째 td가 라벨, 두 번째 td가 값
        if not table_data:
            rows = response.css('table tr')
            for row in rows:
                tds = row.css('td::text').getall()
                if len(tds) >= 2:
                    key = tds[0].strip()
                    value = ' '.join([t.strip() for t in tds[1:] if t.strip()])
                    if key and value:
                        table_data[key] = value
        
        # 패턴 3: dl/dt/dd 구조
        dts = response.css('dl dt::text').getall()
        dds = response.css('dl dd::text').getall()
        for dt, dd in zip(dts, dds):
            key = dt.strip()
            value = dd.strip()
            if key and value:
                table_data[key] = value
        
        return table_data
    
    def _extract_text(self, response: Response, selectors: list) -> Optional[str]:
        """여러 선택자로 텍스트 추출 시도"""
        for selector in selectors:
            try:
                # CSS 선택자 처리
                if '::text' in selector:
                    # 단일 텍스트 추출
                    text = response.css(selector).get()
                    if text:
                        return text.strip()
                elif 'contains(' in selector:
                    # XPath 기반 contains 사용
                    # CSS 선택자에서 XPath로 변환
                    if 'td:contains(' in selector:
                        # td:contains("라벨") + td::text -> XPath 변환
                        label_match = re.search(r'contains\("([^"]+)"\)', selector)
                        if label_match:
                            label = label_match.group(1)
                            xpath = f'//td[contains(text(), "{label}")]/following-sibling::td[1]//text()'
                            text = response.xpath(xpath).get()
                            if text:
                                return text.strip()
                    elif 'th:contains(' in selector:
                        # th:contains("라벨") + td::text -> XPath 변환
                        label_match = re.search(r'contains\("([^"]+)"\)', selector)
                        if label_match:
                            label = label_match.group(1)
                            xpath = f'//th[contains(text(), "{label}")]/following-sibling::td[1]//text()'
                            text = response.xpath(xpath).get()
                            if text:
                                return text.strip()
                    elif 'dt:contains(' in selector:
                        # dt:contains("라벨") + dd::text -> XPath 변환
                        label_match = re.search(r'contains\("([^"]+)"\)', selector)
                        if label_match:
                            label = label_match.group(1)
                            xpath = f'//dt[contains(text(), "{label}")]/following-sibling::dd[1]//text()'
                            text = response.xpath(xpath).get()
                            if text:
                                return text.strip()
                else:
                    # 여러 텍스트 추출 후 결합
                    texts = response.css(selector + '::text').getall()
                    if texts:
                        text = ' '.join([t.strip() for t in texts if t.strip()])
                        if text:
                            return text.strip()
            except Exception as e:
                logger.debug(f"선택자 '{selector}' 실패: {e}")
                continue
        return None
    
    def _extract_model_year(self, model: str) -> Optional[int]:
        """모델명에서 연식 추출"""
        if not model:
            return None
        
        # 괄호 안의 연도 추출: "아반떼(2020)" -> 2020
        match = re.search(r'\((\d{4})\)', model)
        if match:
            try:
                year = int(match.group(1))
                if 1900 <= year <= 2100:
                    return year
            except:
                pass
        
        # 연도 패턴 직접 검색: "2020년", "2020"
        match = re.search(r'(\d{4})', model)
        if match:
            try:
                year = int(match.group(1))
                if 1900 <= year <= 2100:
                    return year
            except:
                pass
        
        return None
    
    def _map_defect_part(self, defect_part: str) -> Optional[str]:
        """결함부위를 표준 값으로 매핑"""
        if not defect_part:
            return None
        
        defect_part_lower = defect_part.lower()
        
        for key, value in self.DEFECT_PART_MAPPING.items():
            if key in defect_part:
                return value
        
        return None
    
    def _extract_number(self, text: str) -> Optional[int]:
        """텍스트에서 숫자만 추출"""
        if not text:
            return None
        
        # 숫자만 추출
        numbers = re.findall(r'\d+', text.replace(',', ''))
        if numbers:
            try:
                return int(''.join(numbers))
            except:
                pass
        
        return None
    
    def parse_simple(self, soup, url: str, title: str) -> Dict:
        """
        BeautifulSoup 객체에서 파싱 (간단한 버전)
        실제 구현 시 Scrapy Response 사용 권장
        """
        # BeautifulSoup 기반 파싱 (임시 구현)
        # 실제로는 Scrapy Response를 사용하는 것이 좋습니다
        
        def get_text(selectors):
            for selector in selectors:
                try:
                    elem = soup.select_one(selector)
                    if elem:
                        return elem.get_text(strip=True)
                except:
                    continue
            return None
        
        maker = get_text(['.maker', '#maker', 'td:contains("제조사")']) or ''
        model = get_text(['.model', '#model', 'td:contains("모델")']) or ''
        model_year = self._extract_model_year(model)
        defect_part = get_text(['.defect-part', '#defect-part', 'td:contains("결함부위")']) or ''
        defect_part_std = self._map_defect_part(defect_part)
        symptom = get_text(['.symptom', '#symptom', 'td:contains("증상")']) or ''
        action = get_text(['.action', '#action', 'td:contains("시정조치")']) or ''
        
        start_date_str = get_text(['.start-date', '#start-date', 'td:contains("시정개시")'])
        start_date = parse_date(start_date_str) if start_date_str else None
        
        qty_str = get_text(['.qty', '#qty', 'td:contains("대상대수")'])
        qty = self._extract_number(qty_str) if qty_str else None
        
        notice_date_str = get_text(['.notice-date', '#notice-date', 'td:contains("공지일")'])
        notice_date = parse_date(notice_date_str) if notice_date_str else None
        
        return {
            'maker': maker.strip(),
            'model': model.strip(),
            'model_year': model_year,
            'defect_part': defect_part.strip(),
            'defect_part_std': defect_part_std,
            'symptom': symptom.strip(),
            'action': action.strip(),
            'start_date': start_date,
            'qty': qty,
            'notice_date': notice_date,
            'url': url,
            'title': title.strip()
        }
    
    def parse_from_text(self, text: str, url: str, title: str, notice_date: str = None) -> Dict:
        """
        보도자료 본문 텍스트에서 리콜 정보 추출
        보도자료 형식: "(제조사) 차종명 차종 N대는 결함내용로 인해 증상으로, 날짜부터 시정조치를 진행하고 있다."
        
        Args:
            text: 보도자료 본문 텍스트
            url: 페이지 URL
            title: 제목
            notice_date: 공지일
        
        Returns:
            파싱된 데이터 딕셔너리 (첫 번째 리콜 정보)
        """
        import re
        
        # 제조사 추출 (예: "메르세데스-벤츠코리아㈜", "현대자동차㈜")
        maker_patterns = [
            r'([가-힣]+(?:자동차|코리아|㈜))',
            r'\(([^)]+)\)',  # 괄호 안의 제조사 (예: "(벤츠)", "(현대)")
        ]
        
        maker = ''
        for pattern in maker_patterns:
            matches = re.findall(pattern, text)
            if matches:
                # 첫 번째 제조사 사용 (보통 본문 시작 부분에 나옴)
                maker = matches[0].replace('㈜', '').replace('코리아', '').strip()
                if '벤츠' in maker or '메르세데스' in maker:
                    maker = '벤츠'
                elif '현대' in maker:
                    maker = '현대자동차'
                elif '기아' in maker:
                    maker = '기아'
                break
        
        # 차종 추출 (예: "E 350 4MATIC 차종", "쏠라티 등 2개 차종")
        model_patterns = [
            r'([A-Z0-9\s]+)\s*차종',  # "E 350 4MATIC 차종"
            r'([가-힣]+)\s*등\s*\d+개\s*차종',  # "쏠라티 등 2개 차종"
            r'([가-힣]+)\s*차종',  # "아반떼 차종"
            r'\([^)]+\)\s*([A-Z0-9\s]+)',  # "(벤츠) E 350 4MATIC"
            r'\([^)]+\)\s*([가-힣]+)',  # "(현대) 쏠라티"
        ]
        
        model = ''
        for pattern in model_patterns:
            matches = re.findall(pattern, text)
            if matches:
                model = matches[0].replace('차종', '').replace('대', '').strip()
                if model and len(model) > 1:
                    break
        
        # 연식 추출
        model_year = self._extract_model_year(model)
        
        # 결함부위 추출 (예: "엔진제어장치", "제동장치", "휠 고정용 너트")
        defect_keywords = {
            '엔진': '엔진',
            '제동': '제동장치',
            '브레이크': '제동장치',
            '에어백': '에어백',
            '변속기': '변속기',
            '서스펜션': '서스펜션',
            '타이어': '타이어',
            '휠': '휠',
            '배터리': '배터리',
            '소프트웨어': '소프트웨어',
        }
        
        defect_part = ''
        for keyword, defect in defect_keywords.items():
            if keyword in text[:500]:  # 앞부분만 확인
                defect_part = defect
                break
        
        defect_part_std = self._map_defect_part(defect_part)
        
        # 증상 추출 (예: "시동이 꺼질 가능성", "너트 풀림 및 휠 이탈 발생 가능성")
        symptom_patterns = [
            r'로\s*인해\s*([^로]+(?:가능성|발생|위험))',
            r'인해\s*([^로]+(?:가능성|발생))',
        ]
        
        symptom = ''
        for pattern in symptom_patterns:
            matches = re.findall(pattern, text)
            if matches:
                symptom = matches[0].strip()
                break
        
        # 시정조치 추출 (예: "시정조치를 진행하고 있다", "시정조치에 들어간다")
        action = '시정조치 진행'
        if '시정조치' in text:
            # 시정조치 관련 문구 추출
            action_match = re.search(r'시정조치[^다]*다', text)
            if action_match:
                action = action_match.group(0)
        
        # 시정개시일 추출 (예: "7월 25일부터", "8월 11일부터")
        start_date = None
        date_patterns = [
            r'(\d{1,2}월\s*\d{1,2}일)\s*부터',
            r'(\d{4}[.-]\d{1,2}[.-]\d{1,2})\s*부터',
            r'(\d{1,2}월\s*\d{1,2}일)',  # "부터" 없이도
        ]
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            if matches:
                date_str = matches[0]
                # 연도가 없으면 공지일의 연도 사용
                if notice_date and '월' in date_str:
                    year = notice_date[:4] if notice_date else '2025'
                    date_str = f"{year}년 {date_str}"
                start_date = parse_date(date_str)
                if start_date:
                    break
        
        # 대상대수 추출 (예: "24,555대", "16,957대")
        qty = None
        qty_matches = re.findall(r'(\d{1,3}(?:,\d{3})*)\s*대', text)
        if qty_matches:
            qty_str = qty_matches[0].replace(',', '')
            qty = self._extract_number(qty_str)
        
        return {
            'maker': maker or '알 수 없음',
            'model': model or '알 수 없음',
            'model_year': model_year,
            'defect_part': defect_part or '알 수 없음',
            'defect_part_std': defect_part_std,
            'symptom': symptom or '알 수 없음',
            'action': action,
            'start_date': start_date,
            'qty': qty,
            'notice_date': notice_date,
            'url': url,
            'title': title.strip()
        }


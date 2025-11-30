# 웹사이트 구조 문서

## 리콜보도자료 목록 페이지

**URL**: https://www.car.go.kr/sd/newsDta/list.do

### HTML 구조

```html
<ul class="board-hrznt-list">
  <li>
    <a class="" href="javascript:void(0);" onclick="$main.event.detailView('2483');">
      <strong>벤츠·현대 등 자발적 시정조치(리콜)</strong>
      <p>내용...</p>
    </a>
    <ol>
      <li>강찬우</li>      <!-- 작성자 -->
      <li>2025-08-12</li>  <!-- 날짜 -->
      <li>조회수 : 959</li> <!-- 조회수 -->
    </ol>
  </li>
  ...
</ul>
```

### 선택자

- **리스트 컨테이너**: `ul.board-hrznt-list`
- **각 항목**: `ul.board-hrznt-list li`
- **제목**: `a strong::text`
- **상세 페이지 ID**: `onclick` 속성에서 `detailView('ID')` 추출
- **상세 페이지 URL**: `/sd/newsDta/view.do?newsSeq={ID}`
- **날짜**: `ol li::text` (두 번째 항목)

### 페이징

- URL 패턴: `/sd/newsDta/list.do?page={페이지번호}`
- 페이지 정보: "전체 470건 (페이지 1/118)" 형태로 표시

## 상세 페이지

**URL 패턴**: https://www.car.go.kr/sd/newsDta/view.do?newsSeq={ID}

### 예상 구조

상세 페이지는 보도자료 형태이므로, 리콜 정보가 텍스트로 포함되어 있을 것입니다.
실제 구조는 상세 페이지를 크롤링하여 확인해야 합니다.

## 크롤링 전략

1. **목록 페이지**: `/sd/newsDta/list.do`에서 모든 항목 수집
2. **상세 페이지**: 각 항목의 `newsSeq` ID를 사용하여 `/sd/newsDta/view.do?newsSeq={ID}` 접근
3. **데이터 추출**: 상세 페이지에서 리콜 정보 파싱

## 주의사항

- JavaScript 기반 링크이므로 `onclick` 이벤트에서 ID 추출 필요
- 페이징 처리 필요 (총 118페이지)
- 요청 간 지연 시간 설정 권장 (서버 부하 방지)


# Black-Scholes 옵션 계산기

사용자가 정의한 페이오프 식을 입력하면 Black-Scholes 가정(로그정규 수익률) 하에서 몬테카를로 시뮬레이션을 통해 옵션 가치를 계산하는 간단한 웹 애플리케이션입니다.

## 설치 및 실행

1. 의존성 설치

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. 개발 서버 실행

   ```bash
   flask --app app run --port 5000 --debug
   ```

3. 브라우저에서 `http://127.0.0.1:5000`으로 접속합니다.

## 사용 방법

- 입력값
  - Spot price (S₀), Strike (K), Risk-free rate (r), Volatility (σ), Maturity (T, 연 단위), Simulations(시뮬레이션 횟수)
  - Payoff expression: 만기 기초자산 가격 `S_T`와 입력된 `K`, `S0`, `r`를 이용해 직접 수식을 작성합니다.
- 사용 가능한 주요 함수: `maximum`, `minimum`, `max`, `min`, `abs`, `exp`, `log`, `sqrt`, `clip`
- 예시 페이오프 식
  - 유럽형 콜: `maximum(S_T - K, 0)`
  - 유럽형 풋: `maximum(K - S_T, 0)`
  - 디지털 콜: `(S_T > K) * 1`
  - 베리어(soft floor): `maximum(S_T - K, 0) - maximum(S_T - 1.2*K, 0)`

계산 버튼을 누르면 할인된 옵션 가격과 입력값이 페이지에 표시됩니다. 오류가 발생하면 에러 메시지를 함께 확인할 수 있습니다.

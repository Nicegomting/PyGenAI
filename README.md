# 💻 PyGenAI

Gemini API의 함수 호출(Function Calling) 기능을 활용하여 다단계(Multi-step) API 호출을 수행하는 Python 예제 프로젝트 입니다. 사용자의 요청을 처리하기 위해 두 개의 외부 API 함수([OpenCage](https://opencagedata.com/), [OpenWeatherMap](https://openweathermap.org/))를 순차적으로 연결하여 실행하는 로직을 보여줍니다.

## 🧰 Requirements
    언어: Python
    라이브러리: google-genai, requests
    API Key (환경 변수 필요):
        GEMINI_API_KEY
        OPENCAGE_API_KEY (좌표 조회용)
        OPENWEATHER_API_KEY (날씨 조회용)

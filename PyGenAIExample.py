import os
from google import genai
from google.genai import types
'''		
* Gemini 2.5 Flash
└ 일일 요청 한도 (RPD: Requests Per Day): 250
└ 분당 요청 한도 (RPM: Requests Per Minute): 10
└ 분당 토큰 한도 (TPM: Tokens Per Minute): 250,000
'''
# GEMINI_API_KEY를 환경변수에 정의
try:

    with genai.Client() as client:
        config = types.GenerateContentConfig()
        response = client.models.generate_content(model="gemini-2.5-flash", contents="현재 서울의 날씨를 알려줄래?", config=config)
        print(response.text)
except Exception as e:
    print(e)
    exit()
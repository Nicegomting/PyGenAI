import os
from urllib import response
from httpx import request
import requests
import json
from google import genai
from google.genai import types
from sympy import content

# 도시 이름에 해당하는 좌표 조회 기능 정의
get_lat_lon_from_city_declare = {
    "name": "get_lat_lon_from_city",
    "description": "OpenCage API를 사용하여 도시 이름에 대한 위도(lat)와 경도(lon)를 조회합니다.",
    "parameters": {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "좌표를 조회할 도시의 이름입니다. (예: '서울', '런던', '파리')"
            }
        },
        "required": ["city"]
    }
}
def get_lat_lon_from_city(city: str) -> dict:
    """
    OpenCage API를 사용하여 도시 이름의 위도(lat)와 경도(lon)를 조회합니다.

    Args:
        city: 좌표를 조회할 도시의 이름 (예: "런던", "서울")

    Returns:
        {'lat': float, 'lon': float} 형태의 좌표 딕셔너리 또는 오류 메시지
    """
    api_key = os.environ.get("OPENCAGE_API_KEY")
    if not api_key:
        return {"error": "OPENCAGE_API_KEY 환경 변수가 설정되지 않았습니다."}
    url = "https://api.opencagedata.com/geocode/v1/json"
    params = {
        "q": city,
        "key": api_key,
        "limit": 1,
        "language": "ko"
    }

    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()

        if data['results']:
            geometry = data['results'][0]['geometry']
            return {'lat': geometry['lat'], 'lon': geometry['lng']}
        else:
            return {"error": f"도시 '{city}'의 좌표를 찾을 수 없습니다."}
        
    except request.exceptions.RequestException as e:
        return {"error": f"OpenCage API 호출 오류: {e}"}
# 좌표에 해당하는 날씨 조회 기능 정의
get_weather_by_coords_declare = {
    "name": "get_weather_by_coords",
    "description": "위도와 경도 좌표를 사용하여 해당 위치의 현재 날씨 정보(온도, 습도, 설명 등)를 조회합니다.",
    "parameters": {
        "type": "object",
        "properties": {
            "lat": {
                "type": "number",
                "description": "날씨를 조회할 위치의 위도(Latitude)."
            },
            "lon": {
                "type": "number",
                "description": "날씨를 조회할 위치의 경도(Longitude)."
            }
        },
        "required": ["lat", "lon"]
    }
}
def get_weather_by_coords(lat: float, lon: float) -> dict:
    """
    위도와 경도 좌표를 사용하여 해당 위치의 현재 날씨 정보(온도, 습도, 설명 등)를 조회합니다.

    Args:
        lat: 날씨를 조회할 위치의 위도(Latitude)
        lon: 날씨를 조회할 위치의 경도(Longitude)

    Returns:
        날씨 정보(온도, 설명)가 포함된 딕셔너리
    """
    api_key = os.environ.get("OPENWEATHER_API_KEY")
    if not api_key:
        return {"error": "OPENWEATHER_API_KEY 환경 변수가 설정되지 않았습니다."}

    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": "metric",
        "lang": "kr"
    }

    try:
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()

        return {
            "city_name": data.get("name"),
            "temp_celsius": data["main"]["temp"],
            "description": data["weather"][0]["description"],
            "humidity": data["main"]["humidity"]
        }
    except requests.exceptions.RequestException as e:
        return {"error": f"OpenWeatherMap API 호출 오류: {e}"}

# MCP 호출 테스트 함수
async def run_mcp(prompt: str):
    print(f"🙂 사용자 요청: {prompt}")

    if not os.environ.get("GEMINI_API_KEY")or not os.environ.get("OPENCAGE_API_KEY") or not os.environ.get("OPENWEATHER_API_KEY"):
        print("⚠️ 오류: 모든 API Key 환경 변수를 설정해야 합니다.")
        return
    
    with genai.Client() as client:
        tools = types.Tool(function_declarations=[get_lat_lon_from_city_declare, get_weather_by_coords_declare])
        config = types.GenerateContentConfig(tools=[tools])

        response_1 = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=config,
        )

        if not response_1.function_calls:
            print("\n✅ Gemini 최종 답변 (함수 호출 없음):")
            print(response_1.text)
            return

        call_1 = response_1.function_calls[0]
        func_name_1 = call_1.name
        func_args_1 = dict(call_1.args)

        print("\n①단계: 좌표 조회 MCP 호출 요청 감지!")
        print(f"- 함수명: {func_name_1}")
        print(f"- 인자: {func_args_1}")

        if func_name_1 == "get_lat_lon_from_city":
            coords = get_lat_lon_from_city(**func_args_1)
        else:
            coords = {"error": f"⚠️ 좌표 조회에서 예상치 못한 함수 호출이 발생함: {func_name_1}"}
    
        coords_json = json.dumps(coords, ensure_ascii=False)
        print(f"- 실행 결과 (좌표): {coords_json}")

        tool_response_1 = types.Part.from_function_response(
            name=func_name_1,
            response={'coords': coords_json}
        )

        response_2 = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                types.Content(role='user', parts=[types.Part(text=prompt)]),
                response_1.candidates[0].content,
                types.Content(role='tool', parts=[tool_response_1])
            ],
            config=types.GenerateContentConfig(tools=[tools]),
        )
    
        if not response_2.function_calls or 'error' in coords:
            print("\n⚠️ 2단계 실패 또는 오류:")
            print(response_2.text)
            return
    
        call_2 = response_2.function_calls[0]
        func_name_2 = call_2.name
        func_args_2 = dict(call_2.args)

        print("\n②단계: 날씨 조회 MCP 호출 요청 감지!")
        print(f"- 함수명: {func_name_2}")
        print(f"- 인자: {func_args_2}")

        if func_name_2 == "get_weather_by_coords":
            weather_data = get_weather_by_coords(**func_args_2)
        else:
            weather_data = {"error": f"⚠️ 날씨 조회에서 예상치 못한 함수 호출이 발생함: {func_name_2}"}
    
        weather_json = json.dumps(weather_data, ensure_ascii=False)
        print(f"- 실행 결과 (날씨): {weather_json}")

        tool_response_2 = types.Part.from_function_response(
            name=func_name_2,
            response={'weather_data': weather_json}
        )

        final_response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                types.Content(role='user', parts=[types.Part(text=prompt)]),
                response_1.candidates[0].content,
                types.Content(role='tool', parts=[tool_response_1]),
                response_2.candidates[0].content,
                types.Content(role='tool', parts=[tool_response_2])
            ]
        )

        print("\n✅ Gemini 최종 답변:")
        print(final_response.text)

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_mcp("현재 서울의 날씨를 알려줄래?"))

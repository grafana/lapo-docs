from __future__ import annotations as _annotations

import asyncio
import os
from dataclasses import dataclass
from typing import Any, Dict, Tuple

from httpx import AsyncClient

from pydantic_ai import Agent, ModelRetry, RunContext


@dataclass
class Deps:
    client: AsyncClient
    weather_api_key: str | None
    geo_api_key: str | None


weather_agent = Agent(
    'google-gla:gemini-1.5-flash',

    # 'Be concise, reply with one sentence.' is enough for some models (like openai) to use
    # the below tools appropriately, but others like anthropic and gemini require a bit more direction.
    system_prompt=(
        'Be concise, reply with one sentence.'
        'Use the `get_lat_lng` tool to get the latitude and longitude of the location, '
        'then use the `get_weather` tool to get the weather.'
    ),
    deps_type=Deps,
    retries=2,
)


@dataclass
class DummyWeather:
    temperature: str
    description: str


DUMMY_LOCATIONS: Dict[str, Tuple[float, float]] = {
    'London': (51.5074, -0.1278),
    'Wiltshire': (51.3492, -1.9927),
    'Rome': (41.9028, 12.4964),
    'Paris': (48.8566, 2.3522),
    'Berlin': (52.5200, 13.4050),
    'Milan': (45.4642, 9.1900),
    'Amsterdam': (52.3676, 4.9041),
}

DUMMY_WEATHERS: Dict[str, DummyWeather] = {
    'London': DummyWeather('11 °C', 'Sunny'),
    'Wiltshire': DummyWeather('9 °C', 'Sunny'),
    'Rome': DummyWeather('16 °C', 'Sunny'),
    'Paris': DummyWeather('13 °C', 'Partly Cloudy'),
    'Berlin': DummyWeather('8 °C', 'Mostly Cloudy'),
    'Milan': DummyWeather('14 °C', 'Mostly Clear'),
    'Amsterdam': DummyWeather('10 °C', 'Light Fog'),
}


@weather_agent.tool
async def get_lat_lng(
    ctx: RunContext[Deps], location_name: str
) -> dict[str, float]:
    """Get the latitude and longitude of a location.

    Args:
        ctx: The context.
        location_name: The name of a location.
    """
    print("calling get_lat_lng", location_name)
    if ctx.deps.geo_api_key is None:
        # if no API key is provided, return a dummy response (London)
        # return {'lat': 51.1, 'lng': -0.1}
        if location_name not in DUMMY_LOCATIONS:
            raise ModelRetry('Could not find the location')
        rr = {'lat': DUMMY_LOCATIONS[location_name][0], 'lng': DUMMY_LOCATIONS[location_name][1]}
        print(rr)
        return rr

    params = {
        'q': location_name,
        'api_key': ctx.deps.geo_api_key,
    }
    r = await ctx.deps.client.get('https://geocode.maps.co/search', params=params)
    r.raise_for_status()
    data = r.json()

    if data:
        return {'lat': data[0]['lat'], 'lng': data[0]['lon']}
    else:
        raise ModelRetry('Could not find the location')


@weather_agent.tool
async def get_weather(ctx: RunContext[Deps], lat: float, lng: float) -> dict[str, Any]:
    """Get the weather at a location.

    Args:
        ctx: The context.
        lat: Latitude of the location.
        lng: Longitude of the location.
    """
    print("calling get_weather", lat, lng)
    if ctx.deps.weather_api_key is None:
        # if no API key is provided, return a dummy response
        # return {'temperature': '21 °C', 'description': 'Sunny'}
        location_name: str | None = None
        for location, (dummy_lat, dummy_lng) in DUMMY_LOCATIONS.items():
            if lat == dummy_lat and lng == dummy_lng:
                location_name = location
        if location_name is None:
            raise ModelRetry('Could not find the location by lat/long')
        if location_name not in DUMMY_WEATHERS:
            raise ModelRetry('Could not find the weather for the location')
        rr = DUMMY_WEATHERS[location_name].__dict__
        print(rr)
        return rr

    params = {
        'apikey': ctx.deps.weather_api_key,
        'location': f'{lat},{lng}',
        'units': 'metric',
    }
    r = await ctx.deps.client.get(
        'https://api.tomorrow.io/v4/weather/realtime', params=params
    )
    r.raise_for_status()
    data = r.json()

    values = data['data']['values']
    # https://docs.tomorrow.io/reference/data-layers-weather-codes
    code_lookup = {
        1000: 'Clear, Sunny',
        1100: 'Mostly Clear',
        1101: 'Partly Cloudy',
        1102: 'Mostly Cloudy',
        1001: 'Cloudy',
        2000: 'Fog',
        2100: 'Light Fog',
        4000: 'Drizzle',
        4001: 'Rain',
        4200: 'Light Rain',
        4201: 'Heavy Rain',
        5000: 'Snow',
        5001: 'Flurries',
        5100: 'Light Snow',
        5101: 'Heavy Snow',
        6000: 'Freezing Drizzle',
        6001: 'Freezing Rain',
        6200: 'Light Freezing Rain',
        6201: 'Heavy Freezing Rain',
        7000: 'Ice Pellets',
        7101: 'Heavy Ice Pellets',
        7102: 'Light Ice Pellets',
        8000: 'Thunderstorm',
    }
    return {
        'temperature': f'{values["temperatureApparent"]:0.0f}°C',
        'description': code_lookup.get(values['weatherCode'], 'Unknown'),
    }


async def main():
    async with AsyncClient() as client:
        # create a free API key at https://www.tomorrow.io/weather-api/
        weather_api_key = os.getenv('WEATHER_API_KEY')
        # create a free API key at https://geocode.maps.co/
        geo_api_key = os.getenv('GEO_API_KEY')
        deps = Deps(
            client=client, weather_api_key=weather_api_key, geo_api_key=geo_api_key
        )
        result = await weather_agent.run(
            # 'What is the weather like in London and in Wiltshire?',
            'What is the weather like in London?',
            deps=deps,
        )
        print('Response:', result.data)


if __name__ == '__main__':
    asyncio.run(main())

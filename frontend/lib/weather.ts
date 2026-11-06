/**
 * Open-Meteo client for the weather context page.
 *
 * Rules:
 * - weather is context only; it never becomes a pest or disease risk score here;
 * - every reading carries its source and fetch time;
 * - missing values stay missing (null) instead of being imputed.
 *
 * Open-Meteo is free and needs no API key. Requests are made from the browser,
 * which is allowed because the service returns `Access-Control-Allow-Origin: *`.
 */

export const WEATHER_SOURCE = {
  name: "Open-Meteo",
  url: "https://open-meteo.com/",
  licence: "CC BY 4.0",
} as const;

const GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search";
const FORECAST_URL = "https://api.open-meteo.com/v1/forecast";

export type WeatherGlyphName =
  | "clear"
  | "partly"
  | "cloud"
  | "fog"
  | "drizzle"
  | "rain"
  | "snow"
  | "thunder";

export interface WeatherCondition {
  label: string;
  glyph: WeatherGlyphName;
}

export interface Place {
  id: number;
  name: string;
  latitude: number;
  longitude: number;
  country: string | null;
  admin1: string | null;
  timezone: string | null;
}

export interface CurrentWeather {
  time: string;
  temperature: number | null;
  apparentTemperature: number | null;
  humidity: number | null;
  precipitation: number | null;
  weatherCode: number | null;
  windSpeed: number | null;
  isDay: boolean | null;
}

export interface DailyWeather {
  date: string;
  weatherCode: number | null;
  temperatureMax: number | null;
  temperatureMin: number | null;
  precipitationSum: number | null;
  precipitationProbability: number | null;
}

export interface WeatherReport {
  place: Place;
  timezone: string;
  current: CurrentWeather;
  daily: DailyWeather[];
  fetchedAt: string;
}

export class WeatherError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "WeatherError";
  }
}

/**
 * Pilot cluster from `final/docs-context/phase-0/pilot-area-map.md`:
 * Kolar, Chikkaballapura and Bengaluru Rural districts, Karnataka.
 */
export const DEFAULT_PLACE: Place = {
  id: 1266305,
  name: "Kolar",
  latitude: 13.13768,
  longitude: 78.12999,
  country: "India",
  admin1: "Karnataka",
  timezone: "Asia/Kolkata",
};

export function placeLabel(place: Place): string {
  return [place.name, place.admin1, place.country].filter(Boolean).join(", ");
}

export function describeWeatherCode(code: number | null): WeatherCondition {
  if (code === null) {
    return { label: "Unknown", glyph: "cloud" };
  }
  if (code === 0) {
    return { label: "Clear sky", glyph: "clear" };
  }
  if (code === 1) {
    return { label: "Mainly clear", glyph: "partly" };
  }
  if (code === 2) {
    return { label: "Partly cloudy", glyph: "partly" };
  }
  if (code === 3) {
    return { label: "Overcast", glyph: "cloud" };
  }
  if (code === 45 || code === 48) {
    return { label: "Fog", glyph: "fog" };
  }
  if (code === 51 || code === 53 || code === 55) {
    return { label: "Drizzle", glyph: "drizzle" };
  }
  if (code === 56 || code === 57) {
    return { label: "Freezing drizzle", glyph: "drizzle" };
  }
  if (code === 61 || code === 63 || code === 65) {
    return { label: "Rain", glyph: "rain" };
  }
  if (code === 66 || code === 67) {
    return { label: "Freezing rain", glyph: "rain" };
  }
  if (code === 71 || code === 73 || code === 75 || code === 77) {
    return { label: "Snow", glyph: "snow" };
  }
  if (code === 80 || code === 81 || code === 82) {
    return { label: "Rain showers", glyph: "rain" };
  }
  if (code === 85 || code === 86) {
    return { label: "Snow showers", glyph: "snow" };
  }
  if (code === 95 || code === 96 || code === 99) {
    return { label: "Thunderstorm", glyph: "thunder" };
  }
  return { label: `Weather code ${code}`, glyph: "cloud" };
}

function asRecord(value: unknown): Record<string, unknown> {
  return typeof value === "object" && value !== null
    ? (value as Record<string, unknown>)
    : {};
}

function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function asNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function asText(value: unknown): string | null {
  return typeof value === "string" && value.length > 0 ? value : null;
}

function at(list: unknown[], index: number): unknown {
  return index >= 0 && index < list.length ? list[index] : null;
}

async function getJson(url: string, signal?: AbortSignal): Promise<unknown> {
  let response: Response;
  try {
    response = await fetch(url, {
      signal,
      cache: "no-store",
      headers: { Accept: "application/json" },
    });
  } catch (caught) {
    if (caught instanceof Error && caught.name === "AbortError") {
      throw caught;
    }
    throw new WeatherError(
      "The weather service is unreachable. Check your connection and retry.",
    );
  }

  if (!response.ok) {
    throw new WeatherError(
      `The weather service returned ${response.status}. Try again shortly.`,
    );
  }

  try {
    return (await response.json()) as unknown;
  } catch {
    throw new WeatherError("The weather service returned an unreadable response.");
  }
}

function toPlace(value: unknown): Place | null {
  const record = asRecord(value);
  const latitude = asNumber(record.latitude);
  const longitude = asNumber(record.longitude);
  const name = asText(record.name);

  if (latitude === null || longitude === null || name === null) {
    return null;
  }

  return {
    id: asNumber(record.id) ?? 0,
    name,
    latitude,
    longitude,
    country: asText(record.country),
    admin1: asText(record.admin1),
    timezone: asText(record.timezone),
  };
}

export async function searchPlaces(
  query: string,
  signal?: AbortSignal,
): Promise<Place[]> {
  const params = new URLSearchParams({
    name: query,
    count: "8",
    language: "en",
    format: "json",
  });

  const payload = asRecord(
    await getJson(`${GEOCODE_URL}?${params.toString()}`, signal),
  );

  return asArray(payload.results)
    .map(toPlace)
    .filter((place): place is Place => place !== null);
}

export async function fetchWeather(
  place: Place,
  signal?: AbortSignal,
): Promise<WeatherReport> {
  const params = new URLSearchParams({
    latitude: String(place.latitude),
    longitude: String(place.longitude),
    current: [
      "temperature_2m",
      "relative_humidity_2m",
      "apparent_temperature",
      "precipitation",
      "weather_code",
      "is_day",
      "wind_speed_10m",
    ].join(","),
    daily: [
      "weather_code",
      "temperature_2m_max",
      "temperature_2m_min",
      "precipitation_sum",
      "precipitation_probability_max",
    ].join(","),
    timezone: "auto",
    forecast_days: "7",
    wind_speed_unit: "kmh",
  });

  const payload = asRecord(
    await getJson(`${FORECAST_URL}?${params.toString()}`, signal),
  );
  const currentRecord = asRecord(payload.current);
  const dailyRecord = asRecord(payload.daily);
  const dates = asArray(dailyRecord.time);

  const daily: DailyWeather[] = [];
  dates.forEach((rawDate, index) => {
    const date = asText(rawDate);
    if (date === null) {
      return;
    }
    const weatherCode = asNumber(at(asArray(dailyRecord.weather_code), index));
    daily.push({
      date,
      weatherCode,
      temperatureMax: asNumber(
        at(asArray(dailyRecord.temperature_2m_max), index),
      ),
      temperatureMin: asNumber(
        at(asArray(dailyRecord.temperature_2m_min), index),
      ),
      precipitationSum: asNumber(
        at(asArray(dailyRecord.precipitation_sum), index),
      ),
      precipitationProbability: asNumber(
        at(asArray(dailyRecord.precipitation_probability_max), index),
      ),
    });
  });

  const isDay = asNumber(currentRecord.is_day);

  return {
    place,
    timezone: asText(payload.timezone) ?? place.timezone ?? "UTC",
    current: {
      time: asText(currentRecord.time) ?? "",
      temperature: asNumber(currentRecord.temperature_2m),
      apparentTemperature: asNumber(currentRecord.apparent_temperature),
      humidity: asNumber(currentRecord.relative_humidity_2m),
      precipitation: asNumber(currentRecord.precipitation),
      weatherCode: asNumber(currentRecord.weather_code),
      windSpeed: asNumber(currentRecord.wind_speed_10m),
      isDay: isDay === null ? null : isDay === 1,
    },
    daily,
    fetchedAt: new Date().toISOString(),
  };
}

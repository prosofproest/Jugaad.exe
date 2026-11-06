"use client";

import { useCallback, useRef, useState } from "react";
import type { FormEvent } from "react";

import {
  WEATHER_SOURCE,
  WeatherError,
  describeWeatherCode,
  fetchWeather,
  placeLabel,
  searchPlaces,
  type Place,
  type WeatherGlyphName,
  type WeatherReport,
} from "@/lib/weather";

function WeatherGlyph({ name }: { name: WeatherGlyphName }) {
  const common = {
    width: 48,
    height: 48,
    viewBox: "0 0 48 48",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 2,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    "aria-hidden": true,
    focusable: false,
  };

  switch (name) {
    case "clear":
      return (
        <svg {...common}>
          <circle cx="24" cy="24" r="8" />
          <path d="M24 6v5M24 37v5M6 24h5M37 24h5M11.3 11.3l3.5 3.5M33.2 33.2l3.5 3.5M36.7 11.3l-3.5 3.5M14.8 33.2l-3.5 3.5" />
        </svg>
      );
    case "partly":
      return (
        <svg {...common}>
          <circle cx="18" cy="18" r="6" />
          <path d="M18 6v3M6 18h3M9.5 9.5l2.1 2.1M26.5 9.5l-2.1 2.1" />
          <path d="M34 39a6 6 0 0 0-1-11.9A8.5 8.5 0 0 0 16.4 29 6 6 0 0 0 17 39Z" />
        </svg>
      );
    case "cloud":
      return (
        <svg {...common}>
          <path d="M34 37a7 7 0 0 0-1.2-13.9A9.5 9.5 0 0 0 14.3 26 7 7 0 0 0 15 37Z" />
        </svg>
      );
    case "fog":
      return (
        <svg {...common}>
          <path d="M33 28a6.5 6.5 0 0 0-1.1-12.9A9 9 0 0 0 15 19a6.5 6.5 0 0 0 .6 12.9" />
          <path d="M10 34h28M14 40h22" />
        </svg>
      );
    case "drizzle":
      return (
        <svg {...common}>
          <path d="M33 26a6.5 6.5 0 0 0-1.1-12.9A9 9 0 0 0 15 17a6.5 6.5 0 0 0 .6 12.9" />
          <path d="M17 33v3M24 33v3M31 33v3" />
        </svg>
      );
    case "rain":
      return (
        <svg {...common}>
          <path d="M33 24a6.5 6.5 0 0 0-1.1-12.9A9 9 0 0 0 15 15a6.5 6.5 0 0 0 .6 12.9" />
          <path d="M16 30l-2 6M24 30l-2 6M32 30l-2 6" />
        </svg>
      );
    case "snow":
      return (
        <svg {...common}>
          <path d="M33 24a6.5 6.5 0 0 0-1.1-12.9A9 9 0 0 0 15 15a6.5 6.5 0 0 0 .6 12.9" />
          <path d="M16 32v6M13 35h6M24 32v6M21 35h6M32 32v6M29 35h6" />
        </svg>
      );
    case "thunder":
      return (
        <svg {...common}>
          <path d="M33 22a6.5 6.5 0 0 0-1.1-12.9A9 9 0 0 0 15 13a6.5 6.5 0 0 0 .6 12.9" />
          <path d="M26 28l-7 10h6l-2 6 8-11h-6l3-5Z" />
        </svg>
      );
  }
}

function formatTemperature(value: number | null): string {
  return value === null ? "—" : `${Math.round(value)}°C`;
}

function formatNumber(value: number | null, unit: string): string {
  if (value === null) {
    return "—";
  }
  const rounded = Math.round(value * 10) / 10;
  return `${rounded}${unit}`;
}

function weekday(isoDate: string): string {
  const date = new Date(`${isoDate}T00:00:00Z`);
  if (Number.isNaN(date.getTime())) {
    return isoDate;
  }
  return new Intl.DateTimeFormat("en-GB", {
    weekday: "short",
    timeZone: "UTC",
  }).format(date);
}

function shortDate(isoDate: string): string {
  const date = new Date(`${isoDate}T00:00:00Z`);
  if (Number.isNaN(date.getTime())) {
    return isoDate;
  }
  return new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "short",
    timeZone: "UTC",
  }).format(date);
}

function localTime(isoDateTime: string): string {
  // Open-Meteo returns the location's local wall-clock time without an offset
  // ("2026-11-06T14:15"). Show it as-is rather than shifting to the browser zone.
  const match = /T(\d{2}:\d{2})/.exec(isoDateTime);
  return match?.[1] ?? "unknown time";
}

export function WeatherPanel({
  initialPlace,
  initialReport,
  initialError,
}: {
  initialPlace: Place;
  initialReport: WeatherReport | null;
  initialError: string | null;
}) {
  const [place, setPlace] = useState<Place | null>(initialPlace);
  const [report, setReport] = useState<WeatherReport | null>(initialReport);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(initialError);

  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Place[]>([]);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  const [locating, setLocating] = useState(false);

  const requestRef = useRef<AbortController | null>(null);

  // Fetch-only: all state updates happen after the await, so the effect below
  // never calls setState synchronously.
  const loadReport = useCallback(async (target: Place) => {
    requestRef.current?.abort();
    const controller = new AbortController();
    requestRef.current = controller;

    try {
      const nextReport = await fetchWeather(target, controller.signal);
      if (!controller.signal.aborted) {
        setReport(nextReport);
        setError(null);
        setLoading(false);
      }
    } catch (caught) {
      if (controller.signal.aborted) {
        return;
      }
      setReport(null);
      setError(
        caught instanceof WeatherError
          ? caught.message
          : "Weather could not be loaded for this location.",
      );
      setLoading(false);
    }
  }, []);

  const loadPlace = useCallback(
    (next: Place) => {
      setPlace(next);
      setLoading(true);
      setError(null);
      void loadReport(next);
    },
    [loadReport],
  );

  async function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const term = query.trim();
    if (term.length === 0) {
      return;
    }

    setSearching(true);
    setSearchError(null);
    setResults([]);

    const controller = new AbortController();
    try {
      const places = await searchPlaces(term, controller.signal);
      setResults(places);
      if (places.length === 0) {
        setSearchError(`No place matched “${term}”. Try a town, district or city.`);
      }
    } catch (caught) {
      setSearchError(
        caught instanceof WeatherError
          ? caught.message
          : "Place search failed. Try again.",
      );
    } finally {
      setSearching(false);
    }
  }

  function choosePlace(next: Place) {
    setResults([]);
    setSearchError(null);
    setQuery(next.name);
    void loadPlace(next);
  }

  function useMyLocation() {
    if (!("geolocation" in navigator)) {
      setError("This browser does not expose a location. Search for a place instead.");
      return;
    }

    setLocating(true);
    setError(null);

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocating(false);
        void loadPlace({
          id: -1,
          name: "Current location",
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          country: null,
          admin1: null,
          timezone: null,
        });
      },
      (geoError) => {
        setLocating(false);
        setError(
          geoError.code === geoError.PERMISSION_DENIED
            ? "Location permission was denied. Search for a place instead."
            : "Your location could not be determined. Search for a place instead.",
        );
      },
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 600000 },
    );
  }

  const condition = report ? describeWeatherCode(report.current.weatherCode) : null;

  return (
    <div className="page">
      <header className="page-header">
        <p className="eyebrow">Weather</p>
        <h1>Weather</h1>
        <p className="page-lede">
          Current conditions and a seven-day forecast for one location. Weather is
          context only — it is never turned into a pest or disease risk score on
          this page.
        </p>
      </header>

      <p className="notice notice-warning small">
        <span className="badge badge-muted">context only</span> A forecast is not a
        diagnosis and weather alone cannot confirm disease. Risk needs crop,
        location, verified reports and an approved model.
      </p>

      <section className="card" aria-labelledby="location-heading">
        <div className="panel-header">
          <h2 id="location-heading">Location</h2>
          {place ? (
            <span className="badge badge-muted">
              {place.latitude.toFixed(4)}, {place.longitude.toFixed(4)}
            </span>
          ) : null}
        </div>

        <form className="weather-search" role="search" onSubmit={handleSearch}>
          <label className="sr-only" htmlFor="weather-place">
            Place name
          </label>
          <input
            id="weather-place"
            type="text"
            value={query}
            placeholder="Search a town or district, e.g. Kolar"
            autoComplete="off"
            onChange={(event) => setQuery(event.target.value)}
          />
          <button type="submit" disabled={searching || query.trim().length === 0}>
            {searching ? "Searching…" : "Search"}
          </button>
          <button
            type="button"
            className="button-secondary"
            disabled={locating}
            onClick={useMyLocation}
          >
            {locating ? "Locating…" : "Use my location"}
          </button>
        </form>

        {searchError ? (
          <p className="error small" role="alert">
            {searchError}
          </p>
        ) : null}

        {results.length > 0 ? (
          <ul className="weather-results">
            {results.map((result) => (
              <li key={`${result.id}-${result.latitude}-${result.longitude}`}>
                <button
                  type="button"
                  className="button-secondary"
                  onClick={() => choosePlace(result)}
                >
                  {placeLabel(result)}
                </button>
              </li>
            ))}
          </ul>
        ) : null}

        {place ? (
          <p className="small muted weather-selected">
            Showing: <strong>{placeLabel(place)}</strong>
            {place.timezone ? ` · ${place.timezone}` : ""}
          </p>
        ) : null}
      </section>

      {error ? (
        <div className="error" role="alert">
          <p>{error}</p>
          {place ? (
            <button
              type="button"
              className="button-secondary"
              onClick={() => void loadPlace(place)}
            >
              Retry
            </button>
          ) : null}
        </div>
      ) : null}

      {loading ? (
        <div className="empty-state" role="status">
          <p>Loading weather for {place ? placeLabel(place) : "the selected place"}…</p>
        </div>
      ) : null}

      {report && condition && !loading ? (
        <>
          <section className="card" aria-labelledby="now-heading">
            <div className="panel-header">
              <h2 id="now-heading">Right now</h2>
              <span className="badge badge-muted">{report.timezone}</span>
            </div>

            <div className="weather-current-main">
              <span className="weather-glyph">
                <WeatherGlyph name={condition.glyph} />
              </span>
              <div>
                <p className="weather-temp">
                  {formatTemperature(report.current.temperature)}
                </p>
                <p className="weather-condition">{condition.label}</p>
                <p className="small muted">
                  As of {localTime(report.current.time)}
                  {report.current.isDay === false ? " · night" : ""}
                  {report.current.apparentTemperature !== null
                    ? ` · feels like ${formatTemperature(report.current.apparentTemperature)}`
                    : ""}
                </p>
              </div>
            </div>

            <dl className="weather-metrics">
              <div className="weather-metric">
                <dt>Humidity</dt>
                <dd>{formatNumber(report.current.humidity, "%")}</dd>
              </div>
              <div className="weather-metric">
                <dt>Wind</dt>
                <dd>{formatNumber(report.current.windSpeed, " km/h")}</dd>
              </div>
              <div className="weather-metric">
                <dt>Precipitation</dt>
                <dd>{formatNumber(report.current.precipitation, " mm")}</dd>
              </div>
              <div className="weather-metric">
                <dt>Source</dt>
                <dd>
                  <a href="https://open-meteo.com/" rel="noreferrer">
                    Open-Meteo
                  </a>
                </dd>
              </div>
            </dl>
          </section>

          <section aria-labelledby="daily-heading">
            <div className="section-heading">
              <h2 id="daily-heading">Next 7 days</h2>
              <p className="small muted">
                Daily summary · fetched{" "}
                <time dateTime={report.fetchedAt} suppressHydrationWarning>
                  {new Date(report.fetchedAt).toLocaleTimeString()}
                </time>
              </p>
            </div>

            <ul className="weather-days">
              {report.daily.map((day) => {
                const dayCondition = describeWeatherCode(day.weatherCode);
                return (
                  <li key={day.date} className="weather-day">
                    <p className="weather-day-name">{weekday(day.date)}</p>
                    <p className="small muted">{shortDate(day.date)}</p>
                    <span className="weather-glyph weather-glyph-small">
                      <WeatherGlyph name={dayCondition.glyph} />
                    </span>
                    <p className="small">{dayCondition.label}</p>
                    <p className="weather-day-temp">
                      <strong>{formatTemperature(day.temperatureMax)}</strong>
                      {" / "}
                      {formatTemperature(day.temperatureMin)}
                    </p>
                    <p className="small muted">
                      {formatNumber(day.precipitationProbability, "%")} rain ·{" "}
                      {formatNumber(day.precipitationSum, " mm")}
                    </p>
                  </li>
                );
              })}
            </ul>
          </section>

          <section className="card" aria-labelledby="source-heading">
            <h2 id="source-heading">About this data</h2>
            <p className="small">
              Conditions and forecast come from{" "}
              <a href={WEATHER_SOURCE.url} rel="noreferrer">
                {WEATHER_SOURCE.name}
              </a>{" "}
              ({WEATHER_SOURCE.licence}), a free weather service. Values are shown
              as received; missing readings are shown as “—” and never filled in.
            </p>
            <p className="small muted">
              Weather is one input to a regional outlook. It is not a diagnosis,
              and it does not by itself mean a pest or disease is present.
            </p>
          </section>
        </>
      ) : null}
    </div>
  );
}

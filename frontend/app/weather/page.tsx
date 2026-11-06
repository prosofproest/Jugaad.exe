import type { Metadata } from "next";

import { WeatherPanel } from "@/components/weather-panel";
import {
  DEFAULT_PLACE,
  WeatherError,
  fetchWeather,
  type WeatherReport,
} from "@/lib/weather";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Weather",
};

export default async function WeatherPage() {
  let report: WeatherReport | null = null;
  let error: string | null = null;

  try {
    report = await fetchWeather(DEFAULT_PLACE);
  } catch (caught) {
    error =
      caught instanceof WeatherError
        ? caught.message
        : "Weather could not be loaded for the default location.";
  }

  return (
    <WeatherPanel
      initialPlace={DEFAULT_PLACE}
      initialReport={report}
      initialError={error}
    />
  );
}

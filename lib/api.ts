/**
 * lib/api.ts
 *
 * Every call to the FastAPI backend lives here, so the UI never has to
 * know about URLs or field names.
 *
 * The backend runs separately:  uvicorn app.main:app --reload  (port 8000)
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/** Exactly what the backend sends back (snake_case, like Python). */
export type ApiPlant = {
  id: number;
  nickname: string;
  species: string;
  location: string | null;
  watering_interval_days: number;
  light_requirement: string | null;
  last_watered_at: string | null;
  created_at: string;
};

/** The shape the UI works with (camelCase, plus computed fields). */
export type Plant = {
  id: number;
  name: string;
  species: string;
  location: string;
  intervalDays: number;
  light: string;
  daysUntilWater: number;
};

/**
 * Works out how many days until this plant needs water.
 * Negative = overdue. Never watered = due today.
 */
function daysUntilWater(
  lastWateredAt: string | null,
  intervalDays: number
): number {
  if (!lastWateredAt) return 0;

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const next = new Date(lastWateredAt);
  next.setHours(0, 0, 0, 0);
  next.setDate(next.getDate() + intervalDays);

  const msPerDay = 1000 * 60 * 60 * 24;
  return Math.round((next.getTime() - today.getTime()) / msPerDay);
}

/** Converts a backend plant into the shape the UI expects. */
function toPlant(api: ApiPlant): Plant {
  return {
    id: api.id,
    name: api.nickname,
    species: api.species,
    location: api.location || "",
    intervalDays: api.watering_interval_days,
    light: api.light_requirement || "Unspecified",
    daysUntilWater: daysUntilWater(
      api.last_watered_at,
      api.watering_interval_days
    ),
  };
}

/** GET /plants - load the whole collection. */
export async function fetchPlants(): Promise<Plant[]> {
  const res = await fetch(`${API_URL}/plants/`);
  if (!res.ok) throw new Error(`Could not load plants (${res.status})`);

  const data: ApiPlant[] = await res.json();
  return data.map(toPlant);
}

/** POST /plants - add a new plant. */
export async function createPlant(input: {
  nickname: string;
  species: string;
  location?: string;
  watering_interval_days?: number;
  light_requirement?: string;
}): Promise<Plant> {
  const res = await fetch(`${API_URL}/plants/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      watering_interval_days: 7,
      ...input,
    }),
  });

  if (!res.ok) throw new Error(`Could not save plant (${res.status})`);
  return toPlant(await res.json());
}

/**
 * PUT /plants/{id} - mark a plant as watered right now.
 *
 * Note: the backend's PlantUpdate schema requires species and nickname,
 * so we send those along with the new timestamp.
 */
export async function waterPlant(plant: Plant): Promise<Plant> {
  const res = await fetch(`${API_URL}/plants/${plant.id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      nickname: plant.name,
      species: plant.species,
      location: plant.location || null,
      watering_interval_days: plant.intervalDays,
      light_requirement: plant.light,
      last_watered_at: new Date().toISOString(),
    }),
  });

  if (!res.ok) throw new Error(`Could not update plant (${res.status})`);
  return toPlant(await res.json());
}

/** DELETE /plants/{id} */
export async function deletePlant(id: number): Promise<void> {
  const res = await fetch(`${API_URL}/plants/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`Could not delete plant (${res.status})`);
}

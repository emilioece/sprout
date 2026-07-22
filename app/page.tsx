"use client";

import { useEffect, useState } from "react";
import { fetchPlants, createPlant, waterPlant, type Plant } from "@/lib/api";

export default function Home() {
    const [plants, setPlants] = useState<Plant[]>([]);
    const [nickname, setNickname] = useState("");
    const [species, setSpecies] = useState("");

    // Load plants from the backend when the page opens
    useEffect(() => {
        fetchPlants()
            .then(setPlants)
            .catch(() => console.log("Backend not running?"));
    }, []);

    // Save a new plant to the backend
    async function handleAdd() {
        if (!nickname || !species) return;

        const saved = await createPlant({ nickname, species });
        setPlants([...plants, saved]);
        setNickname("");
        setSpecies("");
    }

    // updated by jullianna 7/22
    // added a new function to handle watering a plant
    // Mark a plant as watered right now
    async function handleWater(plant: Plant) {
        const updated = await waterPlant(plant);
        setPlants(plants.map((p) => (p.id === updated.id ? updated : p)));
    }

    // Turn "days until water" into readable text
    function waterLabel(days: number) {
        if (days < 0) return "Overdue";
        if (days === 0) return "Water today";
        return `Water in ${days} days`;
    }

    return (
        <div className="min-h-screen p-10">
            <h1 className="text-3xl font-semibold mb-6">🌱 Sprout</h1>

            {/* Add a plant */}
            <div className="flex gap-2 mb-8">
                <input
                    type="text"
                    placeholder="Nickname"
                    value={nickname}
                    onChange={(e) => setNickname(e.target.value)}
                    className="border rounded px-3 py-2"
                />
                <input
                    type="text"
                    placeholder="Species"
                    value={species}
                    onChange={(e) => setSpecies(e.target.value)}
                    className="border rounded px-3 py-2"
                />
                <button
                    onClick={handleAdd}
                    className="px-4 py-2 rounded text-white"
                    style={{ background: "#3A4A32" }}
                >
                    Add plant
                </button>
            </div>

            {/* Plant list */}
            <h2 className="text-xl mb-3">My plants ({plants.length})</h2>

            {plants.length === 0 ? (
                <p>No plants yet. Add one above.</p>
            ) : (
                <ul className="flex flex-col gap-2">
                    {plants.map((plant) => (
                        <li
                            key={plant.id}
                            className="border rounded p-3 flex items-center justify-between"
                        >
                            <span>
                                <strong>{plant.name}</strong> — {plant.species}
                            </span>

                            <span className="flex items-center gap-3">
                                <span className="text-sm opacity-70">
                                    {waterLabel(plant.daysUntilWater)}
                                </span>
                                <button
                                    onClick={() => handleWater(plant)}
                                    className="px-3 py-1 rounded text-white text-sm"
                                    style={{ background: "#3A4A32" }}
                                >
                                    💧 Done
                                </button>
                            </span>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}
"use client";

import { useEffect, useState } from "react";
import { fetchPlants, createPlant, type Plant } from "@/lib/api";

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
                        <li key={plant.id} className="border rounded p-3">
                            <strong>{plant.name}</strong> — {plant.species}
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}
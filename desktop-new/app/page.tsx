"use client";

import { useEffect, useState } from "react";
// importing API helpers - backend runs separately on port 8000!
import { fetchPlants, createPlant, waterPlant, deletePlant, type Plant } from "@/lib/api";

export default function Home() {
    // state for holding our list of plants from backend
    const [plants, setPlants] = useState<Plant[]>([]);

    // modal steps & state logic for adding new plant
    const [step, setStep] = useState<1 | 2>(1);
    const [isAdding, setIsAdding] = useState(false);
    const [isSaving, setIsSaving] = useState(false);

    // custom pop-up state so we don't have to use native alert/confirm windows
    const [plantToDelete, setPlantToDelete] = useState<Plant | null>(null);
    const [isDeleting, setIsDeleting] = useState(false);

    // controlled form inputs
    const [species, setSpecies] = useState("");
    const [nickname, setNickname] = useState("");
    const [location, setLocation] = useState("");
    const [notes, setNotes] = useState("");

    // initial fetch when page loads
    useEffect(() => {
        fetchPlants()
            .then(setPlants)
            .catch(() => console.log("Backend not running?")); // reminder: start uvicorn first lol
    }, []);

    function handleNextStep() {
        if (!species.trim()) return; // don't let user continue if field is empty
        if (!nickname.trim()) {
            setNickname(species.trim()); // fallback default nickname to species name
        }
        setStep(2);
    }

    async function handleAdd() {
        if (!nickname.trim() || !species.trim()) return;

        setIsSaving(true);
        try {
            const saved = await createPlant({ nickname, species, location });
            // append new item to end of local state list
            setPlants((prev) => [...prev, saved]);
            resetForm();
        } catch (error) {
            console.error("Failed to save plant:", error);
            alert("Could not save plant. Make sure your backend server is running!");
        } finally {
            setIsSaving(false);
        }
    }

    // clears everything out so form is blank next time modal opens
    function resetForm() {
        setSpecies("");
        setNickname("");
        setLocation("");
        setNotes("");
        setStep(1);
        setIsAdding(false);
    }

    // handles updating timestamp on backend when water button is clicked
    async function handleWater(plant: Plant) {
        try {
            const updated = await waterPlant(plant);
            // replace old plant object with updated one in state array
            setPlants(plants.map((p) => (p.id === updated.id ? updated : p)));
        } catch (error) {
            console.error("Failed to water plant:", error);
        }
    }

    // opens modern confirmation dialog instead of browser alert
    function openDeleteModal(plant: Plant) {
        setPlantToDelete(plant);
    }

    // triggers DELETE endpoint and removes plant from UI
    async function confirmDelete() {
        if (!plantToDelete) return;

        setIsDeleting(true);
        try {
            await deletePlant(plantToDelete.id);
            // filter out deleted ID from state array
            setPlants((prev) => prev.filter((p) => p.id !== plantToDelete.id));
            setPlantToDelete(null);
        } catch (error) {
            console.error("Failed to delete plant:", error);
            alert("Could not delete plant. Make sure your backend server is running!");
        } finally {
            setIsDeleting(false);
        }
    }

    // format helper for watering schedule badges
    function waterLabel(days: number) {
        if (days < 0) return "Overdue";
        if (days === 0) return "Due today";
        return `In ${days}d`;
    }

    // derived dashboard metrics (re-calculates when `plants` state updates)
    const overdueCount = plants.filter((p) => p.daysUntilWater < 0).length;
    const dueTodayCount = plants.filter((p) => p.daysUntilWater === 0).length;

    return (
        <div className="min-h-screen flex relative">
            {/* ============ SIDEBAR ============ */}
            <aside
                className="w-64 bg-white border-r px-4 py-6 flex flex-col justify-between shrink-0"
                style={{ borderColor: "#E5E3DC" }}
            >
                <div>
                    {/* logo header */}
                    <div className="mb-8 px-2">
                        <div className="flex items-center gap-2 mb-1">
                            <span className="text-2xl">🌱</span>
                            <span
                                className="text-2xl font-bold tracking-tight"
                                style={{ fontFamily: "var(--font-fraunces)", color: "#1E2A20" }}
                            >
                                Sprout
                            </span>
                        </div>
                        <p className="text-xs font-normal" style={{ color: "#788177" }}>
                            {plants.length} {plants.length === 1 ? "plant" : "plants"} in collection
                        </p>
                    </div>

                    {/* sidebar navigation links */}
                    <nav className="flex flex-col gap-1">
                        <a
                            href="#"
                            className="flex items-center gap-3 px-3.5 py-3 rounded-xl text-sm font-medium text-white shadow-xs"
                            style={{ backgroundColor: "#284E36" }}
                        >
                            <span className="text-base flex items-center justify-center w-6 h-6 rounded-md bg-[#3A6349]">
                                🧑‍🌾
                            </span>
                            Dashboard
                        </a>

                        <a
                            href="#"
                            className="flex items-center gap-3 px-3.5 py-3 rounded-xl text-sm font-medium transition-colors hover:bg-black/5"
                            style={{ color: "#2B352C" }}
                        >
                            <span className="text-base w-6 text-center">🪴</span>
                            My Plants
                        </a>

                        <a
                            href="#"
                            className="flex items-center gap-3 px-3.5 py-3 rounded-xl text-sm font-medium transition-colors hover:bg-black/5"
                            style={{ color: "#2B352C" }}
                        >
                            <span className="text-base w-6 text-center">📅</span>
                            Schedule
                        </a>

                        <a
                            href="#"
                            className="flex items-center gap-3 px-3.5 py-3 rounded-xl text-sm font-medium transition-colors hover:bg-black/5"
                            style={{ color: "#2B352C" }}
                        >
                            <span className="text-base w-6 text-center">🔍</span>
                            Symptom Guide
                        </a>
                    </nav>
                </div>

                {/* footer area with quick tip box & action button */}
                <div className="flex flex-col gap-3">
                    <div
                        className="rounded-2xl p-4 text-xs leading-relaxed"
                        style={{ backgroundColor: "#E9EEE6" }}
                    >
                        <p className="font-semibold mb-1 flex items-center gap-1.5" style={{ color: "#284E36" }}>
                            <span>💡</span> Tip for beginners
                        </p>
                        <p style={{ color: "#616C60" }}>
                            Check the Dashboard daily — it shows exactly what needs attention today.
                        </p>
                    </div>

                    <button
                        onClick={() => {
                            resetForm();
                            setIsAdding(true);
                        }}
                        className="w-full py-3.5 rounded-xl text-sm font-medium text-white transition-all hover:opacity-95 text-center shadow-xs cursor-pointer"
                        style={{ backgroundColor: "#284E36" }}
                    >
                        + Add Plant
                    </button>
                </div>
            </aside>

            {/* ============ MAIN CONTENT AREA ============ */}
            <main
                className="flex-1 flex flex-col p-12 min-h-screen relative"
                style={{ backgroundColor: "#F3F1EA" }}
            >
                {/* conditional render: show empty state if array is empty, otherwise show dashboard cards */}
                {plants.length === 0 ? (
                    /* --- empty / welcome screen --- */
                    <div className="flex-1 flex flex-col items-center justify-center text-center max-w-md mx-auto gap-4">
                        <span className="text-6xl mb-2">🌱</span>

                        <h1
                            className="text-3xl font-bold tracking-tight"
                            style={{ fontFamily: "var(--font-fraunces)", color: "#1E2A20" }}
                        >
                            Welcome to Sprout
                        </h1>

                        <p className="text-sm leading-relaxed" style={{ color: "#616C60" }}>
                            Add your first plant to get started. Sprout will build your care schedule and remind you what to do and when.
                        </p>

                        <button
                            onClick={() => {
                                resetForm();
                                setIsAdding(true);
                            }}
                            className="mt-2 px-6 py-3.5 rounded-xl text-sm font-medium text-white transition-all hover:opacity-95 shadow-xs cursor-pointer"
                            style={{ backgroundColor: "#284E36" }}
                        >
                            Add your first plant
                        </button>
                    </div>
                ) : (
                    /* --- dashboard layout view --- */
                    <div className="max-w-4xl w-full flex flex-col gap-8">
                        {/* main header block */}
                        <div>
                            <h1
                                className="text-4xl font-bold tracking-tight mb-1"
                                style={{ fontFamily: "var(--font-fraunces)", color: "#1E2A20" }}
                            >
                                Dashboard
                            </h1>
                            <p className="text-sm text-[#788177]">Wednesday, July 22</p>
                        </div>

                        {/* grid for summary count cards */}
                        <div className="grid grid-cols-3 gap-5">
                            <div className="bg-white p-6 rounded-2xl border border-[#E5E3DC] shadow-2xs flex flex-col justify-between h-36">
                                <span className="text-2xl">🪴</span>
                                <div>
                                    <span
                                        className="text-3xl font-bold block"
                                        style={{ fontFamily: "var(--font-fraunces)", color: "#284E36" }}
                                    >
                                        {plants.length}
                                    </span>
                                    <span className="text-xs text-[#788177] font-medium">Plants</span>
                                </div>
                            </div>

                            <div className="bg-white p-6 rounded-2xl border border-[#E5E3DC] shadow-2xs flex flex-col justify-between h-36">
                                <span className="text-2xl">⚠️</span>
                                <div>
                                    <span
                                        className="text-3xl font-bold block"
                                        style={{ fontFamily: "var(--font-fraunces)", color: "#284E36" }}
                                    >
                                        {overdueCount}
                                    </span>
                                    <span className="text-xs text-[#788177] font-medium">Overdue tasks</span>
                                </div>
                            </div>

                            <div className="bg-white p-6 rounded-2xl border border-[#E5E3DC] shadow-2xs flex flex-col justify-between h-36">
                                <span className="text-2xl">📋</span>
                                <div>
                                    <span
                                        className="text-3xl font-bold block"
                                        style={{ fontFamily: "var(--font-fraunces)", color: "#284E36" }}
                                    >
                                        {dueTodayCount}
                                    </span>
                                    <span className="text-xs text-[#788177] font-medium">Due today</span>
                                </div>
                            </div>
                        </div>

                        {/* status banner */}
                        <div className="bg-[#E8EFE6] p-6 rounded-2xl flex items-center gap-4">
                            <span className="text-2xl">✨</span>
                            <div className="flex flex-col gap-0.5">
                                <h3 className="text-sm font-semibold text-[#1E2A20]">All caught up!</h3>
                                <p className="text-xs text-[#616C60]">
                                    No tasks due today. Check the Schedule to see what's coming next.
                                </p>
                            </div>
                        </div>

                        {/* upcoming task items section */}
                        <div className="flex flex-col gap-4 mt-2">
                            <h2
                                className="text-xl font-bold"
                                style={{ fontFamily: "var(--font-fraunces)", color: "#1E2A20" }}
                            >
                                Upcoming watering
                            </h2>

                            <div className="flex flex-col gap-3">
                                {/* map through plants in state array */}
                                {plants.map((plant) => (
                                    <div
                                        key={plant.id}
                                        className="bg-white rounded-2xl p-4 border border-[#E5E3DC] shadow-2xs flex items-center justify-between hover:border-[#284E36]/40 transition-all"
                                    >
                                        <div className="flex items-center gap-3.5">
                                            {/* initials avatar preview */}
                                            <div className="w-12 h-12 rounded-full bg-[#E8EFE6] flex items-center justify-center text-sm font-bold text-[#284E36] overflow-hidden border border-[#D5E0D2]">
                                                {plant.name.slice(0, 4)}
                                            </div>

                                            <div className="flex flex-col">
                                                <strong className="text-base font-semibold text-[#1E2A20]">
                                                    {plant.name}
                                                </strong>
                                                <span className="text-xs text-[#788177]">
                                                    {plant.location || plant.species || "Unspecified"}
                                                </span>
                                            </div>
                                        </div>

                                        {/* right side controls */}
                                        <div className="flex items-center gap-3">
                                            {/* water action button */}
                                            <button
                                                onClick={() => handleWater(plant)}
                                                className="w-10 h-10 rounded-xl bg-[#E8F0FE] hover:bg-[#D2E3FC] text-[#1A73E8] flex items-center justify-center text-lg transition-all cursor-pointer shadow-2xs hover:scale-105 active:scale-95"
                                                title="Mark as watered"
                                                aria-label="Water plant"
                                            >
                                                💧
                                            </button>

                                            <span className="text-xs font-normal text-[#788177] min-w-[60px] text-right">
                                                {waterLabel(plant.daysUntilWater)}
                                            </span>

                                            {/* delete trash button */}
                                            <button
                                                onClick={() => openDeleteModal(plant)}
                                                className="w-8 h-8 rounded-xl flex items-center justify-center text-[#9A9E97] hover:text-[#DC2626] hover:bg-[#FEE2E2] transition-all cursor-pointer ml-1"
                                                title="Delete plant"
                                                aria-label="Delete plant"
                                            >
                                                <svg
                                                    className="w-4 h-4"
                                                    fill="none"
                                                    stroke="currentColor"
                                                    viewBox="0 0 24 24"
                                                >
                                                    <path
                                                        strokeLinecap="round"
                                                        strokeLinejoin="round"
                                                        strokeWidth="2"
                                                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                                                    />
                                                </svg>
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}
            </main>

            {/* ============ DELETE CONFIRMATION MODAL ============ */}
            {plantToDelete && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-xs p-4 animate-in fade-in duration-200">
                    <div className="w-full max-w-sm bg-white rounded-3xl p-6 shadow-xl border border-[#E5E3DC] flex flex-col items-center text-center gap-4">
                        <div className="w-12 h-12 rounded-2xl bg-[#FEE2E2] flex items-center justify-center text-[#DC2626] text-xl">
                            🗑️
                        </div>

                        <div>
                            <h3
                                className="text-xl font-bold text-[#1E2A20] mb-1"
                                style={{ fontFamily: "var(--font-fraunces)" }}
                            >
                                Remove {plantToDelete.name}?
                            </h3>
                            <p className="text-xs text-[#616C60] leading-relaxed">
                                Are you sure you want to delete this plant from your collection? This action cannot be undone.
                            </p>
                        </div>

                        <div className="flex gap-3 w-full mt-2">
                            <button
                                onClick={() => setPlantToDelete(null)}
                                className="flex-1 py-3 rounded-2xl text-xs font-semibold bg-[#F6F5F0] text-[#616C60] hover:bg-[#EFECE6] transition-colors cursor-pointer"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={confirmDelete}
                                disabled={isDeleting}
                                className="flex-1 py-3 rounded-2xl text-xs font-semibold bg-[#DC2626] text-white hover:bg-[#B91C1C] transition-colors shadow-xs cursor-pointer disabled:opacity-50"
                            >
                                {isDeleting ? "Deleting..." : "Delete Plant"}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* ============ ADD PLANT MODAL OVERLAY ============ */}
            {isAdding && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-xs p-4">
                    <div className="w-full max-w-lg bg-white rounded-3xl shadow-xl border border-[#E5E3DC] overflow-hidden flex flex-col max-h-[90vh]">
                        {/* modal header */}
                        <div className="px-6 pt-6 pb-4 flex items-center justify-between border-b border-[#F0EEE8]">
                            <div className="flex items-center gap-3">
                                {step === 2 && (
                                    <button
                                        onClick={() => setStep(1)}
                                        className="w-8 h-8 rounded-full bg-[#EFECE6] hover:bg-[#E2DFD7] flex items-center justify-center text-[#616C60] transition-colors cursor-pointer text-xs"
                                        aria-label="Back"
                                    >
                                        ‹
                                    </button>
                                )}
                                <div>
                                    <h2
                                        className="text-xl font-bold"
                                        style={{ fontFamily: "var(--font-fraunces)", color: "#1E2A20" }}
                                    >
                                        {step === 1 ? "Identify your plant" : "Plant details"}
                                    </h2>
                                    <p className="text-xs text-[#788177]">Step {step} of 2</p>
                                </div>
                            </div>

                            <button
                                onClick={resetForm}
                                className="w-8 h-8 rounded-full bg-[#EFECE6] hover:bg-[#E2DFD7] flex items-center justify-center text-[#616C60] transition-colors cursor-pointer"
                                aria-label="Close"
                            >
                                ✕
                            </button>
                        </div>

                        {/* STEP 1: search/select species */}
                        {step === 1 && (
                            <>
                                <div className="p-6 flex flex-col gap-4 overflow-y-auto">
                                    <div className="flex bg-[#EFECE6] p-1 rounded-2xl text-xs font-medium text-[#616C60]">
                                        <button className="flex-1 py-2 flex items-center justify-center gap-1.5 rounded-xl bg-[#284E36] text-white shadow-xs">
                                            <span>🔍</span> Search
                                        </button>
                                        <button className="flex-1 py-2 flex items-center justify-center gap-1.5 rounded-xl hover:text-black transition-colors">
                                            <span>📷</span> Photo
                                        </button>
                                        <button className="flex-1 py-2 flex items-center justify-center gap-1.5 rounded-xl hover:text-black transition-colors">
                                            <span>💬</span> Describe
                                        </button>
                                    </div>

                                    <div>
                                        <input
                                            type="text"
                                            placeholder="e.g. monstera, snake plant, cactus..."
                                            value={species}
                                            onChange={(e) => setSpecies(e.target.value)}
                                            className="w-full px-4 py-3 text-sm rounded-xl bg-[#F6F5F0] border border-[#284E36] text-[#1E2A20] outline-none transition-all placeholder:text-[#9A9E97]"
                                        />
                                    </div>

                                    {/* quick select plant species preset list */}
                                    <div className="flex flex-col gap-2">
                                        {[
                                            { name: "Monstera deliciosa", tags: "easy · indirect", icon: "🌿" },
                                            { name: "Epipremnum aureum", tags: "easy · low light", icon: "🍃" },
                                            { name: "Ficus lyrata", tags: "expert · indirect", icon: "🌱" },
                                            { name: "Sansevieria trifasciata", tags: "easy · low light", icon: "🌾" },
                                        ].map((item) => (
                                            <button
                                                key={item.name}
                                                type="button"
                                                onClick={() => {
                                                    setSpecies(item.name);
                                                    setNickname(item.name.split(" ")[0]);
                                                }}
                                                className={`p-3.5 rounded-2xl border text-left flex items-center gap-3 transition-all cursor-pointer ${
                                                    species === item.name
                                                        ? "bg-[#E9EEE6] border-[#284E36]"
                                                        : "bg-[#F6F5F0] border-transparent hover:border-[#E5E3DC]"
                                                }`}
                                            >
                                                <span className="text-xl">{item.icon}</span>
                                                <div>
                                                    <p className="text-sm font-semibold text-[#1E2A20]">{item.name}</p>
                                                    <p className="text-xs text-[#788177]">{item.tags}</p>
                                                </div>
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                <div className="p-6 pt-2 border-t border-[#F0EEE8]">
                                    <button
                                        onClick={handleNextStep}
                                        disabled={!species.trim()}
                                        className={`w-full py-3.5 rounded-2xl text-sm font-medium transition-all text-center ${
                                            species.trim()
                                                ? "bg-[#284E36] text-white hover:opacity-95 shadow-xs cursor-pointer"
                                                : "bg-[#BAC3B9] text-white cursor-not-allowed"
                                        }`}
                                    >
                                        Continue →
                                    </button>
                                </div>
                            </>
                        )}

                        {/* STEP 2: nickname & details */}
                        {step === 2 && (
                            <>
                                <div className="p-6 flex flex-col gap-4 overflow-y-auto">
                                    <div className="p-3.5 rounded-2xl bg-[#E9EEE6] flex items-center gap-3">
                                        <span className="text-xl">🍃</span>
                                        <div>
                                            <p className="text-sm font-semibold text-[#284E36]">{species}</p>
                                            <p className="text-xs text-[#616C60]">Care data auto-filled · easy</p>
                                        </div>
                                    </div>

                                    <div>
                                        <label className="block text-xs font-semibold text-[#616C60] mb-1.5">
                                            Plant photo
                                        </label>
                                        <div className="h-28 rounded-2xl bg-[#E9EEE6] border-2 border-dashed border-[#C3D2C1] flex items-center justify-center text-xs text-[#616C60] font-medium cursor-pointer hover:bg-[#E1E8DE] transition-colors">
                                            + Add photo
                                        </div>
                                    </div>

                                    <div>
                                        <label className="block text-xs font-semibold text-[#616C60] mb-1.5">
                                            Nickname *
                                        </label>
                                        <input
                                            type="text"
                                            value={nickname}
                                            onChange={(e) => setNickname(e.target.value)}
                                            className="w-full px-4 py-3 text-sm rounded-xl bg-[#F6F5F0] border border-[#E5E3DC] text-[#1E2A20] outline-none focus:border-[#284E36] transition-all"
                                        />
                                    </div>

                                    <div>
                                        <label className="block text-xs font-semibold text-[#616C60] mb-1.5">
                                            Location in home
                                        </label>
                                        <input
                                            type="text"
                                            placeholder="e.g. Living room window, Bedroom shelf"
                                            value={location}
                                            onChange={(e) => setLocation(e.target.value)}
                                            className="w-full px-4 py-3 text-sm rounded-xl bg-[#F6F5F0] border border-[#E5E3DC] text-[#1E2A20] outline-none focus:border-[#284E36] transition-all placeholder:text-[#9A9E97]"
                                        />
                                    </div>

                                    {/* static schedule info box */}
                                    <div className="bg-[#F6F5F0] rounded-2xl p-4 flex flex-col gap-2">
                                        <h4 className="text-xs font-semibold text-[#1E2A20] mb-1">
                                            Auto-filled care schedule
                                        </h4>
                                        <div className="flex items-center justify-between text-xs text-[#616C60]">
                                            <span className="flex items-center gap-1.5">💧 Watering</span>
                                            <span className="font-medium text-[#1E2A20]">Every 7 days</span>
                                        </div>
                                        <div className="flex items-center justify-between text-xs text-[#616C60]">
                                            <span className="flex items-center gap-1.5">🌿 Fertilizing</span>
                                            <span className="font-medium text-[#1E2A20]">Every 60 days</span>
                                        </div>
                                        <div className="flex items-center justify-between text-xs text-[#616C60]">
                                            <span className="flex items-center gap-1.5">🪴 Repotting</span>
                                            <span className="font-medium text-[#1E2A20]">Every 18 months</span>
                                        </div>
                                    </div>

                                    <div>
                                        <label className="block text-xs font-semibold text-[#616C60] mb-1.5">
                                            Notes (optional)
                                        </label>
                                        <textarea
                                            rows={2}
                                            placeholder="Any quirks about this specific plant?"
                                            value={notes}
                                            onChange={(e) => setNotes(e.target.value)}
                                            className="w-full px-4 py-3 text-sm rounded-xl bg-[#F6F5F0] border border-[#E5E3DC] text-[#1E2A20] outline-none focus:border-[#284E36] transition-all placeholder:text-[#9A9E97] resize-none"
                                        />
                                    </div>
                                </div>

                                <div className="p-6 pt-2 border-t border-[#F0EEE8]">
                                    <button
                                        onClick={handleAdd}
                                        disabled={!nickname.trim() || isSaving}
                                        className={`w-full py-3.5 rounded-2xl text-sm font-medium transition-all text-center ${
                                            nickname.trim() && !isSaving
                                                ? "bg-[#284E36] text-white hover:opacity-95 shadow-xs cursor-pointer"
                                                : "bg-[#BAC3B9] text-white cursor-not-allowed"
                                        }`}
                                    >
                                        {isSaving ? "Adding..." : "Add to my collection"}
                                    </button>
                                </div>
                            </>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
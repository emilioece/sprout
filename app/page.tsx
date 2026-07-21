export default function Home() {
    return (
        <div
            className="min-h-screen flex flex-col items-center justify-center gap-5 px-8"
            style={{ backgroundColor: 'var(--background)' }}
        >
            <span className="text-6xl">🌱</span>
            <div className="text-center">
                <h1 className="text-2xl font-semibold mb-2"
                    style={{fontFamily: "'Fraunces', serif", color: 'var(--foreground)'}}>
                    Welcome to Sprout
                </h1>
                <p className="text-sm max-w-sm" style={{color: 'var(--muted-foreground)'}}>
                    Add your first plant to get started. Sprout will build your care schedule and remind you what to do
                    and when.
                </p>
            </div>
            <button
                className="px-6 py-3 rounded-xl text-sm font-medium transition-all hover:opacity-90"
                style={{
                    background: '#3A4A32',
                    color: '#FFFFFF',}}
            >
                Add your first plant
            </button>
        </div>
    );
}
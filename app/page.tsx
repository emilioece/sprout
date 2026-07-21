export default function Home() {
  return (
      <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            width: "100vw",
            height: "100vh",
            backgroundColor: "#F3F1EA",
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            alignItems: "center",
            gap: "8px",
          }}
      >
        <h1 style={{ margin: 0, fontSize: "2rem", fontWeight: 700, color: "#111111" }}>
          Welcome to Sprout
        </h1>
        <p style={{ margin: 0, fontSize: "1rem", fontWeight: 400, color: "#666666" }}>
          Add your first plant to get started. Sprout will build your care schedule and remind you what to do and when.
        </p>
      </div>
  );
}
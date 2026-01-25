import Topbar from "./Topbar";

export default function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen">
      <Topbar />
      <main className="p-8">
        <div className="mt-6">{children}</div>
      </main>
    </div>
  );
}

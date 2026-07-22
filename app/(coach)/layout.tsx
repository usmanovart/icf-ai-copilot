export default function CoachLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="p-6 md:p-8">
      <div className="mb-6 rounded-md border border-violet-200 bg-violet-50 p-3 text-sm text-violet-800">
        Coach Portal — Sub-Task 5
      </div>
      {children}
    </div>
  );
}

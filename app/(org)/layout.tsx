export default function OrgLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="p-6 md:p-8">
      <div className="mb-6 rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
        Organization Workspace — Sub-Task 5
      </div>
      {children}
    </div>
  );
}

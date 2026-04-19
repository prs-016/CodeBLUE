export default function RiskCardSkeleton() {
  return (
    <div className="space-y-2 animate-pulse">
      {[1, 2, 3].map((i) => (
        <div key={i} className="h-4 bg-grey-dark/50 rounded w-full" />
      ))}
    </div>
  );
}

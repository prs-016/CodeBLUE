import TriageQueue from '../components/Triage/TriageQueue';

export default function TriagePage() {
  return (
    <div className="w-full h-full bg-navy overflow-auto p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-white mb-2">Triage Queue</h1>
        <p className="text-grey-mid mb-8">Ranked global priorities based on threshold proximity, time remaining, and funding coverage.</p>
        <TriageQueue />
      </div>
    </div>
  );
}

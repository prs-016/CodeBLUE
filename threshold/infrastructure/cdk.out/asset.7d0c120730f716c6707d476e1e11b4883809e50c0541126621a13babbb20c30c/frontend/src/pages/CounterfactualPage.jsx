import CounterfactualEngine from "../components/Counterfactual/CounterfactualEngine";

export default function CounterfactualPage() {
  return (
    <div className="min-h-[calc(100vh-4rem)] bg-navy px-6 py-8 md:px-10">
      <div className="mx-auto max-w-7xl">
        <CounterfactualEngine />
      </div>
    </div>
  );
}

import { useParams } from "react-router-dom";

import RegionBrief from "../components/RegionBrief/RegionBrief";

export default function RegionPage() {
  const { regionId } = useParams();

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-navy px-6 py-8 md:px-10">
      <div className="mx-auto max-w-7xl">
        <RegionBrief regionId={regionId} />
      </div>
    </div>
  );
}

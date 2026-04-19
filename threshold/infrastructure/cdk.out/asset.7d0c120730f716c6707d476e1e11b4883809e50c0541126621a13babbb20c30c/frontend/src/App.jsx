import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import Navbar from "./components/shared/Navbar";
import TourNarrator from "./components/Tour/TourNarrator";
import CounterfactualPage from "./pages/CounterfactualPage";
import FundPage from "./pages/FundPage";
import FundingGapPage from "./pages/FundingGapPage";
import Home from "./pages/Home";
import RegionPage from "./pages/RegionPage";
import TriagePage from "./pages/TriagePage";

function App() {
  return (
    <BrowserRouter>
      <div className="flex min-h-screen flex-col bg-navy text-white">
        <Navbar />
        <main className="flex flex-1 flex-col pt-16">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/triage" element={<TriagePage />} />
            <Route path="/region/:regionId" element={<RegionPage />} />
            <Route path="/counterfactual" element={<CounterfactualPage />} />
            <Route path="/funding-gap" element={<FundingGapPage />} />
            <Route path="/fund" element={<FundPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
        <TourNarrator />
      </div>
    </BrowserRouter>
  );
}

export default App;

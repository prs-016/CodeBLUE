import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Navbar from './components/shared/Navbar';
import Home from './pages/Home';
import TriagePage from './pages/TriagePage';
import FundingGapPage from './pages/FundingGapPage';
import FundPage from './pages/FundPage';
// import RegionPage from './pages/RegionPage';
// import CounterfactualPage from './pages/CounterfactualPage';

function App() {
  return (
    <BrowserRouter>
      <div className="flex flex-col min-h-screen bg-navy text-white">
        <Navbar />
        <main className="flex-grow flex flex-col relative w-full h-full pt-16">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/triage" element={<TriagePage />} />
            <Route path="/region/:regionId" element={<div className="p-8">Region Brief arriving soon...</div>} />
            <Route path="/counterfactual" element={<div className="p-8">Counterfactual arriving soon...</div>} />
            <Route path="/funding-gap" element={<FundingGapPage />} />
            <Route path="/fund" element={<FundPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App

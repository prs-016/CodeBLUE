import { Link, useLocation } from 'react-router-dom';
import { Activity, ShieldAlert, Target, Compass, Database } from 'lucide-react';

export default function Navbar() {
  const loc = useLocation();
  const path = loc.pathname;

  const getLinkClass = (p) => 
    `flex items-center space-x-2 text-sm font-medium transition-colors ${
      path === p ? 'text-teal border-b-2 border-teal pb-1' : 'text-grey-mid hover:text-white'
    }`;

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-navy/80 backdrop-blur-md border-b border-grey-dark/50">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        
        {/* LOGO */}
        <div className="flex items-center space-x-3">
          <Activity className="h-6 w-6 text-teal-light" />
          <Link to="/" className="text-xl font-bold tracking-widest bg-clip-text text-transparent bg-gradient-to-r from-teal-light to-white">
            THRESHOLD
          </Link>
        </div>

        {/* NAVIGATION LINKS */}
        <div className="hidden md:flex items-center space-x-8 pt-1">
          <Link to="/" className={getLinkClass('/')}>
            <Compass className="h-4 w-4"/> <span>War Room</span>
          </Link>
          <Link to="/triage" className={getLinkClass('/triage')}>
            <ShieldAlert className="h-4 w-4"/> <span>Triage</span>
          </Link>
          <Link to="/funding-gap" className={getLinkClass('/funding-gap')}>
            <Target className="h-4 w-4"/> <span>Funding Gap</span>
          </Link>
          <Link to="/counterfactual" className={getLinkClass('/counterfactual')}>
            <Database className="h-4 w-4"/> <span>Counterfactual</span>
          </Link>
          <Link to="/fund" className={getLinkClass('/fund')}>
            <span className="bg-teal/20 text-teal-light px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider">
              Threshold Fund
            </span>
          </Link>
        </div>

        {/* TEAM BADGE */}
        <div>
          <div className="text-[10px] font-mono text-grey-mid border border-grey-mid/30 px-2 py-1 rounded">
            CODE BLUE
          </div>
        </div>
      </div>
    </nav>
  );
}

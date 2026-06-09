import { useHashRoute } from "./hooks/useHashRoute";
import { WatchView } from "./views/WatchView";
import { MethodologyView } from "./views/MethodologyView";
import { BadgesView } from "./views/BadgesView";
import { DonateFooter } from "./components/DonateFooter";

const NAV = [
  ["", "Watch"], ["methodology", "Methodology"], ["badges", "Badges"],
] as const;

export default function App() {
  const route = useHashRoute();

  return (
    <>
      <header>
        <a className="logo" href="#/">MG<span className="pipe" />Terminal<span className="sub">/ manipulation watch</span></a>
        <nav className="nav">
          {NAV.map(([r, label]) => (
            <a key={r} href={`#/${r}`} className={`navlink ${route === r ? "on" : ""}`}>{label}</a>
          ))}
        </nav>
        <span className="live"><span className="dot" /> auto · every 4h</span>
      </header>

      <div className="wrap">
        {route === "methodology" ? <MethodologyView />
          : route === "badges" ? <BadgesView />
            : <WatchView />}
        <DonateFooter />
      </div>
    </>
  );
}

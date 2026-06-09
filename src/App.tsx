import { useHashRoute } from "./hooks/useHashRoute";
import { WatchView } from "./views/WatchView";
import { MethodologyView } from "./views/MethodologyView";
import { BadgesView } from "./views/BadgesView";
import { TokenDetailView } from "./views/TokenDetailView";
import { DonateFooter } from "./components/DonateFooter";

const NAV = [
  ["", "Watch"], ["methodology", "Methodology"], ["badges", "Badges"],
] as const;

function activeNav(route: string): string {
  if (route.startsWith("token/")) return "";
  return route;
}

export default function App() {
  const route = useHashRoute();
  const nav = activeNav(route);

  return (
    <>
      <header>
        <a className="logo" href="#/">MG<span className="pipe" />Terminal<span className="sub">/ manipulation watch</span></a>
        <nav className="nav">
          {NAV.map(([r, label]) => (
            <a key={r} href={`#/${r}`} className={`navlink ${nav === r ? "on" : ""}`}>{label}</a>
          ))}
        </nav>
        <span className="live"><span className="dot" /> auto · every 4h</span>
      </header>

      <div className="wrap">
        {route.startsWith("token/") ? <TokenDetailView symbol={decodeURIComponent(route.slice(6))} />
          : route === "methodology" ? <MethodologyView />
            : route === "badges" ? <BadgesView />
              : <WatchView />}
        <DonateFooter />
      </div>
    </>
  );
}

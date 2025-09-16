import Reports from "./components/Reports";
import ScanHistory from "./components/ScanHistory";
import Scanner from "./components/Scanner";
import Settings from "./components/Settings";
import Help from "./components/Help";
import { Route, Routes } from "react-router-dom";
import Nav2 from "./components/Nav2";

function Routing() {
  return (
    <>
      <Nav2 />
      <div className="container">
        <Routes>
          <Route path="/scanner" element={<Scanner />} />
          <Route path="/scanhistory" element={<ScanHistory />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/help" element={<Help />} />
        </Routes>
      </div>
    </>
  );
}

export default Routing;

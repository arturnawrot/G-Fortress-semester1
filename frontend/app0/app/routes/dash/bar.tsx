import { Link, NavLink } from "react-router";
export const Bar = () => {
  return (
    <div role="tablist" className="shadow tabs tabs-lift tabs-lg text-base-content">
      <NavLink to="scanner" role="tab" className="tab ">
        Scanner
      </NavLink>

      <NavLink to="scanhistory" role="tab" className="tab ">
        Scan History
      </NavLink>

      <NavLink to="reports" role="tab" className="tab ">
        Reports
      </NavLink>

      <NavLink to="help" role="tab" className="tab">
        Help
      </NavLink>

      
    </div>
  );
};

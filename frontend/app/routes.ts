import type { RouteConfig } from "@react-router/dev/routes";
// Correctly import only 'index' and 'route'
import { index, route } from "@react-router/dev/routes";

export default [
  // These routes are public and are not wrapped by the layout
  index("routes/home.tsx"),
  route("login", "routes/login.tsx"),

  // This is the layout route. It renders the ProtectedRoute component.
  // The child routes below will be rendered inside ProtectedRoute's <Outlet />.
  route("/", "components/ProtectedRoute.tsx", [
    route("dashboard", "routes/dashboard.tsx"),
    route("reports", "routes/reports/index.tsx"),
    route("reports/:reportId", "routes/reports/$reportId.tsx"),
    route("scheduled-scans", "routes/scheduled-scans/index.tsx")
  ]),
] satisfies RouteConfig;
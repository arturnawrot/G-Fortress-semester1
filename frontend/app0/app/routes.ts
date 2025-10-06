import type { RouteConfig } from "@react-router/dev/routes";
import { index, route } from "@react-router/dev/routes";

export default [
  index("routes/home.tsx"),
  route("login", "routes/login.tsx"),
  route("dashboard", "routes/dashboard.tsx"),
  route("userdashboard", "routes/userdashboard.tsx" ,
    [
  route("help", "routes/dash/help.tsx"),
  route("scanner", "routes/dash/scanner.tsx"),
  route("scanhistory", "routes/dash/scanhistory.tsx"),
  route("reports", "routes/dash/reports.tsx"),
]),
  
] satisfies RouteConfig;
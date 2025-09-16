import { Link, useMatch, useResolvedPath } from "react-router-dom";

export default function Nav() {
  return (
    <nav className="nav nav-pills nav-fill" style={{ marginBottom: "20px" }}>
      <Link to="/" className="title">
        G-Fortress
      </Link>
      <ul className="nav nav-pills nav-justified">
        <CustomLink to="/scanner">Scanner</CustomLink>
        <CustomLink to="/scanhistory">Scan History</CustomLink>
        <CustomLink to="/reports">Reports</CustomLink>
        <CustomLink to="/settings">Settings</CustomLink>
        <CustomLink to="/help">Help</CustomLink>
      </ul>
    </nav>
  );
}

function CustomLink({
  to,
  children,
  ...props
}: {
  to: string;
  children: string;
}) {
  const resolvedPath = useResolvedPath(to);
  const isActive = useMatch({ path: resolvedPath.pathname, end: true });

  return (
    <li className={isActive ? "active" : ""}>
      <Link to={to} {...props}>
        {children}
      </Link>
    </li>
  );
}

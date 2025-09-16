import { Nav } from "react-bootstrap";
import { Link } from "react-router-dom";
function Nav2() {
  return (
    <Nav justify variant="tabs">
      <Nav.Item>
        <Nav.Link as={Link} to="/Scanner" eventKey="link-1">
          Scanner
        </Nav.Link>
      </Nav.Item>
      <Nav.Item>
        <Nav.Link as={Link} to="/ScanHistory" eventKey="link-2">
          Scan History
        </Nav.Link>
      </Nav.Item>
      <Nav.Item>
        <Nav.Link as={Link} to="/Reports" eventKey="link-3">
          Reports
        </Nav.Link>
      </Nav.Item>
      {/*<Nav.Item>
        <Nav.Link as={Link} to="/Settings" eventKey="link-4">
          Settings
        </Nav.Link>
      </Nav.Item>*/}
      <Nav.Item>
        <Nav.Link as={Link} to="/Help" eventKey="link-5">
          Help
        </Nav.Link>
      </Nav.Item>
    </Nav>
  );
}

export default Nav2;

function ScanType() {
  return (
    <div className="dropdown">
      <h4>Scan Depth:</h4>
      <button
        className="btn btn-primary dropdown-toggle"
        type="button"
        data-bs-toggle="dropdown"
        aria-expanded="false"
        style={{ marginBottom: "40px" }}
      >
        Select Scan Depth
      </button>
      <br></br>
      <ul className="dropdown-menu">
        <li>
          <button className="dropdown-item" type="button">
            Full Scan
          </button>
        </li>
        <li>
          <button className="dropdown-item" type="button">
            Custom Scan
          </button>
        </li>
        <li>
          <button className="dropdown-item" type="button">
            Quick Scan
          </button>
        </li>
      </ul>
    </div>
  );
}

export default ScanType;

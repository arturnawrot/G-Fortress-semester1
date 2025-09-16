import ScanType from "./ScanType";
import DateTimePicker from "react-datetime-picker";
import Exclusions from "./Exclusions";
import Threats from "./Threats";
import { Stack } from "react-bootstrap";
function Scanner() {
  return (
    <>
      <Stack direction="vertical" gap={2}>
        <h2 style={{ marginTop: "20px" }}>Scan Customization</h2>
        <div className="p-2">{<ScanType />}</div>
        <div className="p-2">
          <h4>Schedule Scan:</h4>
          {<DateTimePicker />}
        </div>
        <div className="p-2">{<Threats />}</div>
        <div className="p-2">{<Exclusions />}</div>
      </Stack>

      <Stack direction="horizontal" gap={3} style={{ marginTop: "20px" }}>
        <div className="p-2">
          <button className="btn btn-secondary">Save settings</button>
        </div>
        <div className="p-2">
          <button className="btn btn-secondary">Load settings</button>
        </div>
        <div className="p-2">
          <button className="btn btn-primary" type="button">
            Begin scan
          </button>
        </div>
      </Stack>
    </>
  );
}

export default Scanner;

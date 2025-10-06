import DateTimePicker from "react-datetime-picker";
import { useState } from "react";
import "react-datetime-picker/dist/DateTimePicker.css";
import "react-calendar/dist/Calendar.css";
import "react-clock/dist/Clock.css";
import FileUpload from "./file"
type ValuePiece = Date | null;

type Value = ValuePiece | [ValuePiece, ValuePiece];

export default function Scanner() {
  const [value, onChange] = useState<Value>(new Date());
const [files, setFiles] = useState<File[]>([]);

  return (
    
    <div className="inter-in">
      <h1 className="mb-5 text-xl">Scan Customization</h1>
      <div className="p-2">
        <h4>Schedule Scan:</h4>
        {<DateTimePicker onChange={onChange} value={value} />}
      </div>
      <div className="p-2">
        <div className="divider"></div>
        <div className="dropdown">
          <h4>Scan Depth:</h4>
          <select defaultValue="Choose scan depth" className="select-appearance-none">
            <option disabled={true}>Choose scan depth</option>
            <option value="Full">Full Scan</option>
            <option value="Custom">Custom Scan</option>
            <option value="Quick">Quick Scan</option>
          </select>
        </div>
      </div>
      <div className="divider"></div>
      <div className="p-2">
        <h4>Threats:</h4>
        <select defaultValue="Select a threat to prioritise">
          <option disabled={true}>Select a threat to prioritise</option>
        </select>
      </div>
      <div className="divider"></div>
      <h4>Exclusions:</h4>
    <FileUpload />
      <div className="p-2">
        <button className="btn btn-primary" >Begin scan</button>
      </div>
    </div>
  );
}

import { Form } from "react-bootstrap";
function Threats() {
  return (
    <>
      <h4 style={{ marginTop: "40px" }}>Threats:</h4>
      <>
        <Form.Select>
          <option>Select a threat to prioritise</option>
        </Form.Select>
        <br />
      </>
    </>
  );
}
export default Threats;

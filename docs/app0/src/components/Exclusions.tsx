import { Form } from "react-bootstrap";
function Exclusions() {
  return (
    <div className="dropdown">
      <h4 style={{ marginTop: "40px" }}>Exclusions:</h4>
      <Form.Group controlId="formFileMultiple" className="mb-3">
        <Form.Control type="file" multiple />
      </Form.Group>
    </div>
  );
}

export default Exclusions;

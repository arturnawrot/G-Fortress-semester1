import { usePDF } from "react-to-pdf";
import { Card, Button } from "react-bootstrap";
import pie from "./pie.jpg";
const Report = () => {
  const { toPDF, targetRef } = usePDF({
    filename: "report.pdf",
  });

  return (
    <>
      <div ref={targetRef}>
        <h2 style={{ marginTop: "20px" }}>Scan Reports:</h2>
        <Card style={{ width: "18rem" }}>
          <Card.Img variant="top" src={pie} />
          <Card.Body>
            <Card.Text>
              Text describing results of scan and how issues may be fixed.
            </Card.Text>
            <Button variant="primary" onClick={() => toPDF()}>
              Download report
            </Button>
          </Card.Body>
        </Card>
      </div>
    </>
  );
};

export default Report;

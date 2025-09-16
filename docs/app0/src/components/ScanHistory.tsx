import Card from "react-bootstrap/Card";
function ScanHistory() {
  return (
    <>
      <h2 style={{ marginTop: "20px" }}>Scan History</h2>
      <Card>
        <Card.Body>
          {
            "Sample scan log text:[2024-11-20T12:00:00,123][INFO ][o.e.n.Node] [node-1] initializing ...[2024-11-20T12:00:05,789][INFO ][o.e.c.c.ClusterService] [node-1] new_master {node-1}{ID123}{127.0.0.1}{127.0.0.1:9300}{http_enabled=true}, reason: master node changed"
          }
        </Card.Body>
      </Card>
    </>
  );
}

export default ScanHistory;

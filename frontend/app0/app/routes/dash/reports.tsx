import { Chart as chartjs, Legend, Tooltip, ArcElement } from "chart.js";
import { Data } from "./sampledata";
import { Pie } from "react-chartjs-2";

chartjs.register(Tooltip, Legend, ArcElement);

export default function Report() {
  const options = {
    aspectRatio: 3.5,
    maintainAspectRatio: true,
    layout: {
      padding: {},
    },
    plugins: {
      legend: {
        display: true,
      },
      tooltip: {
        enabled: true,
      },
    },
    
  };
  return (
    <>
      <div style={{ width: '100%', aspectRatio: 3.5 }}>
        <h2>Scan Reports:</h2>
        <Pie
          options={options}
          data={Data}
        />
        Text describing results of scan and how issues may be fixed.
      </div>
    </>
  );
}

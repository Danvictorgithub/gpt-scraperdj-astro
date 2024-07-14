import React from "react";
import { Bar } from "react-chartjs-2";
import { Chart as ChartJS } from "chart.js/auto";
interface Props {
  dataInfo;
}
export default function DataChart(props: Props) {
  return (
    <div className="flex-1 basis-0 border border-gray-500 p-4 rounded-xl flex items-center justify-center">
      <Bar
        className="flex"
        data={{
          labels: [
            "6 Days ago",
            "5 Days ago",
            "4 Days ago",
            "3 Days ago",
            "2 Days ago",
            "Yesterday",
            "Today",
          ],
          datasets: [
            {
              label: "Conversation Generated Per Hour Average",
              data: props.dataInfo,
              backgroundColor: [
                "white",
                "white",
                "white",
                "white",
                "white",
                "white",
                "white",
              ],
              borderRadius: 10,
            },
          ],
        }}
        options={{
          scales: {
            x: {
              grid: {
                color: "black",
              },
              ticks: {
                color: "gray",
              },
              title: {
                display: true,
                text: "Days",
                color: "white",
              },
            },
            y: {
              grid: {
                color: "black",
              },
              ticks: {
                color: "gray", // Change Y-axis tick labels to white
              },
              title: {
                display: true,
                text: "Conversation Generated Per Hour",
                color: "white", // Change Y-axis title to white
              },
            },
          },
          plugins: {
            legend: {
              labels: {
                color: "white", // Change legend text to white
              },
            },
          },
        }}
      />
    </div>
  );
}

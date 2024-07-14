import React, { useState } from "react";
import { Bar } from "react-chartjs-2";
import { Chart as ChartJS } from "chart.js/auto";
interface Props {
  dataInfo_rate;
  dataInfo_total;
}
export default function DataChart(props: Props) {
  const [chart, setChart] = useState("rate");
  return (
    <div className="h-full flex-1 basis-0 border border-gray-500 p-4 rounded-xl flex flex-col items-center justify-start">
      <div className="flex gap-2 bg-gray-800 p-1 px-4 rounded-xl">
        <button
          onClick={() => setChart("rate")}
          className={
            `rounded-xl px-12 py-1  text-white hover:bg-black active:border-black ` +
            (chart === "rate" ? "bg-gray-900" : "")
          }
        >
          <p className="">Rate</p>
        </button>
        <button
          onClick={() => setChart("total")}
          className={
            `rounded-xl px-12 py-1  text-white hover:bg-black active:border-black ` +
            (chart === "total" ? "bg-gray-900" : "")
          }
        >
          <p className="">Total</p>
        </button>
      </div>
      <div className="h-full w-full flex-1 flex items-center">
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
                label:
                  chart == "rate"
                    ? "Conversation Generated Per Hour Average"
                    : "Conversation Generated In a Day",
                data:
                  chart == "rate" ? props.dataInfo_rate : props.dataInfo_total,
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
                  text:
                    chart == "rate"
                      ? "Conversation Generated Per Hour Average"
                      : "Total Generated Conversations",
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
    </div>
  );
}

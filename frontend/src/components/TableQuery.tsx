import React, { useState, useEffect } from "react";
import axios from "axios";
import { Pagination } from "@nextui-org/react";

interface Data {
  count: number;
  next: string | null;
  previous: string | null;
  results: Array<{
    start_conversation: string;
    end_conversation: string;
  }>;
}

interface Props {
  token: string;
  backendUrl: string;
}

export default function TableQuery(props: Props) {
  const [data, setData] = useState<Data>({
    count: 0,
    next: null,
    previous: null,
    results: [],
  });
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10; // Define the number of items you want per page

  useEffect(() => {
    const fetchData = async () => {
      const offset = (currentPage - 1) * itemsPerPage;
      try {
        const response = await axios.get<Data>(
          `${props.backendUrl}/api/conversations/?limit=${itemsPerPage}&offset=${offset}`,
          {
            headers: {
              Authorization: `Bearer ${props.token}`,
            },
          }
        );
        setData(response.data);
      } catch (err) {
        console.error(err);
      }
    };

    fetchData();
  }, [currentPage, props.token, props.backendUrl, itemsPerPage]);

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  return (
    <div>
      <div className="flex-1 basis-0 border border-gray-500 p-4 rounded-xl overflow-scroll mt-4 ">
        <table className="w-full">
          <thead>
            <tr>
              <th
                scope="col"
                className="py-3.5 text-sm font-bold text-center rtl:text-right text-white"
              >
                Start Conversation
              </th>
              <th
                scope="col"
                className="py-3.5 text-sm font-bold text-center rtl:text-right text-white"
              >
                End Conversation
              </th>
            </tr>
          </thead>
          <tbody>
            {data.results.map((conversation) => (
              <tr className="border-b" key={conversation.start_conversation}>
                <td className="text-wrap px-4 py-4 text-sm font-medium whitespace-nowrap text-gray-300">
                  {conversation.start_conversation}
                </td>
                <td className="text-wrap p-4 py-4 text-sm font-medium whitespace-nowrap text-gray-300">
                  {conversation.end_conversation}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <Pagination
        total={Math.ceil(data.count / itemsPerPage)}
        initialPage={1}
        onChange={(page) => handlePageChange(page)}
      />
    </div>
  );
}

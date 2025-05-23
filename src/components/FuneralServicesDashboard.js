import React, { useState, useEffect } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

function FuneralServicesDashboard() {
  const [data, setData] = useState([]);
  const [stats, setStats] = useState({});
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [dataResponse, statsResponse] = await Promise.all([
        fetch('http://localhost:5000/api/data'),
        fetch('http://localhost:5000/api/stats')
      ]);

      if (!dataResponse.ok || !statsResponse.ok) {
        throw new Error('Failed to fetch data from server');
      }

      const dataJson = await dataResponse.json();
      const statsJson = await statsResponse.json();

      setData(dataJson.data);
      setStats(statsJson);
    } catch (error) {
      console.error('Error fetching data:', error);
      setError('Failed to load data. Please make sure the backend server is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    try {
      setError(null);
      const response = await fetch(`http://localhost:5000/api/search?q=${encodeURIComponent(searchQuery)}`);
      
      if (!response.ok) {
        throw new Error('Search failed');
      }

      const json = await response.json();
      setData(json.data);
    } catch (error) {
      console.error('Error searching:', error);
      setError('Search failed. Please try again.');
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-lg text-gray-600">Loading data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="text-center">
          <div className="text-red-500 text-xl mb-4">⚠️ {error}</div>
          <button 
            onClick={fetchData}
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const typeData = Object.entries(stats.typeDistribution || {}).map(([name, value]) => ({
    name,
    value
  }));

  const stateData = Object.entries(stats.stateDistribution || {}).map(([name, value]) => ({
    name,
    value
  }));

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Funeral Services Dashboard</h1>
      
      {/* Search Form */}
      <form onSubmit={handleSearch} className="mb-8">
        <div className="flex gap-4">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search businesses..."
            className="flex-1 p-2 border rounded"
          />
          <button
            type="submit"
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
          >
            Search
          </button>
        </div>
      </form>

      {/* Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
        <div className="bg-white p-4 rounded shadow">
          <h2 className="text-xl font-semibold mb-4">Service Types Distribution</h2>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={typeData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  label
                >
                  {typeData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white p-4 rounded shadow">
          <h2 className="text-xl font-semibold mb-4">State Distribution</h2>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stateData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="value" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Data Table */}
      <div className="bg-white rounded shadow overflow-x-auto">
        <table className="min-w-full">
          <thead>
            <tr className="bg-gray-100">
              <th className="px-6 py-3 text-left">Business Name</th>
              <th className="px-6 py-3 text-left">Type</th>
              <th className="px-6 py-3 text-left">Address</th>
              <th className="px-6 py-3 text-left">Phone</th>
              <th className="px-6 py-3 text-left">Email</th>
              <th className="px-6 py-3 text-left">Website</th>
              <th className="px-6 py-3 text-left">Contact Person</th>
              <th className="px-6 py-3 text-left">Social Media</th>
              <th className="px-6 py-3 text-left">Size</th>
              <th className="px-6 py-3 text-left">Rating</th>
              <th className="px-6 py-3 text-left">State</th>
              <th className="px-6 py-3 text-left">City</th>
              <th className="px-6 py-3 text-left">Source</th>
            </tr>
          </thead>
          <tbody>
            {data.map((item, index) => (
              <tr key={index} className="border-t">
                <td className="px-6 py-4">{item['Business Name']}</td>
                <td className="px-6 py-4">{item.Type}</td>
                <td className="px-6 py-4">{item.Address}</td>
                <td className="px-6 py-4">{item.Phone}</td>
                <td className="px-6 py-4">{item.Email}</td>
                <td className="px-6 py-4">
                  {item.Website !== "N/A" ? (
                    <a href={item.Website} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline">
                      {item.Website}
                    </a>
                  ) : (
                    "N/A"
                  )}
                </td>
                <td className="px-6 py-4">{item['Contact Person']}</td>
                <td className="px-6 py-4">
                  {item['Social Media'] && item['Social Media'] !== "N/A" ? (
                    <div className="space-y-1">
                      {item['Social Media'].split(', ').map((link, i) => (
                        <a key={i} href={link} target="_blank" rel="noopener noreferrer" className="block text-blue-500 hover:underline">
                          {link.split('.com/')[1] || link}
                        </a>
                      ))}
                    </div>
                  ) : (
                    "N/A"
                  )}
                </td>
                <td className="px-6 py-4">{item.Size}</td>
                <td className="px-6 py-4">{item.Rating}</td>
                <td className="px-6 py-4">{item.State}</td>
                <td className="px-6 py-4">{item.City}</td>
                <td className="px-6 py-4">{item.Source}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default FuneralServicesDashboard; 
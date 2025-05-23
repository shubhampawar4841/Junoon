import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

const FuneralServicesDashboard = () => {
  const [data, setData] = useState([]);
  const [filteredData, setFilteredData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    state: 'all',
    type: 'all',
    search: ''
  });
  const [stats, setStats] = useState({});

  // Load and parse the CSV data
  useEffect(() => {
    const loadData = async () => {
      try {
        // Read the CSV file
        const csvContent = await window.fs.readFile('paste-2.txt', { encoding: 'utf8' });
        
        // Parse CSV manually
        const lines = csvContent.trim().split('\n');
        const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''));
        
        const parsedData = lines.slice(1).map(line => {
          // Simple CSV parsing - handles quotes and commas
          const values = [];
          let current = '';
          let inQuotes = false;
          
          for (let i = 0; i < line.length; i++) {
            const char = line[i];
            if (char === '"') {
              inQuotes = !inQuotes;
            } else if (char === ',' && !inQuotes) {
              values.push(current.trim().replace(/"/g, ''));
              current = '';
            } else {
              current += char;
            }
          }
          values.push(current.trim().replace(/"/g, ''));
          
          const row = {};
          headers.forEach((header, index) => {
            row[header] = values[index] || '';
          });
          return row;
        });

        // Clean the data
        const cleanedData = parsedData.map(row => ({
          ...row,
          'Business Name': row['Business Name'] || 'N/A',
          'Type': row['Type'] || 'N/A',
          'Address': row['Address'] || 'N/A',
          'Phone': row['Phone'] === 'N/A' ? '' : row['Phone'],
          'Website': row['Website'] === 'N/A' ? '' : row['Website'],
          'City': row['City'] || 'N/A',
          'State': row['State'] || 'N/A'
        }));

        setData(cleanedData);
        setFilteredData(cleanedData);
        
        // Calculate statistics
        const stateCount = {};
        const typeCount = {};
        cleanedData.forEach(row => {
          stateCount[row.State] = (stateCount[row.State] || 0) + 1;
          typeCount[row.Type] = (typeCount[row.Type] || 0) + 1;
        });

        setStats({
          totalBusinesses: cleanedData.length,
          states: stateCount,
          types: typeCount,
          completeness: {
            'Business Name': Math.round((cleanedData.filter(r => r['Business Name'] !== 'N/A').length / cleanedData.length) * 100),
            'Address': Math.round((cleanedData.filter(r => r.Address !== 'N/A').length / cleanedData.length) * 100),
            'Phone': Math.round((cleanedData.filter(r => r.Phone && r.Phone !== '').length / cleanedData.length) * 100),
            'Website': Math.round((cleanedData.filter(r => r.Website && r.Website !== '').length / cleanedData.length) * 100)
          }
        });

        setLoading(false);
      } catch (error) {
        console.error('Error loading data:', error);
        setLoading(false);
      }
    };

    loadData();
  }, []);

  // Filter data based on current filters
  useEffect(() => {
    let filtered = data;

    if (filters.state !== 'all') {
      filtered = filtered.filter(row => row.State === filters.state);
    }

    if (filters.type !== 'all') {
      filtered = filtered.filter(row => row.Type === filters.type);
    }

    if (filters.search) {
      const searchTerm = filters.search.toLowerCase();
      filtered = filtered.filter(row => 
        (row['Business Name'] || '').toLowerCase().includes(searchTerm) ||
        (row.Address || '').toLowerCase().includes(searchTerm) ||
        (row.City || '').toLowerCase().includes(searchTerm)
      );
    }

    setFilteredData(filtered);
  }, [data, filters]);

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const getUniqueValues = (key) => {
    return [...new Set(data.map(row => row[key]).filter(val => val && val !== 'N/A'))].sort();
  };

  const stateChartData = Object.entries(stats.states || {})
    .map(([state, count]) => ({ state, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10);

  const typeChartData = Object.entries(stats.types || {})
    .map(([type, count]) => ({ type, count }))
    .sort((a, b) => b.count - a.count);

  const COLORS = ['#3498db', '#2ecc71', '#9b59b6', '#f1c40f', '#e74c3c', '#1abc9c', '#34495e', '#e67e22'];

  const avgCompleteness = Object.values(stats.completeness || {}).reduce((a, b) => a + b, 0) / 
                         Object.keys(stats.completeness || {}).length || 0;

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-lg text-gray-600">Loading funeral services data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white py-8">
        <div className="container mx-auto px-4">
          <h1 className="text-4xl font-bold mb-2">🏛️ Funeral Services Dashboard</h1>
          <p className="text-xl opacity-90">Comprehensive database of funeral service providers</p>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        {/* Statistics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-lg p-6 transform hover:scale-105 transition-transform">
            <div className="flex items-center">
              <div className="text-3xl text-blue-500 mr-4">🏢</div>
              <div>
                <h3 className="text-2xl font-bold">{stats.totalBusinesses || 0}</h3>
                <p className="text-gray-600">Total Businesses</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-lg p-6 transform hover:scale-105 transition-transform">
            <div className="flex items-center">
              <div className="text-3xl text-green-500 mr-4">📍</div>
              <div>
                <h3 className="text-2xl font-bold">{Object.keys(stats.states || {}).length}</h3>
                <p className="text-gray-600">States Covered</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-lg p-6 transform hover:scale-105 transition-transform">
            <div className="flex items-center">
              <div className="text-3xl text-purple-500 mr-4">📊</div>
              <div>
                <h3 className="text-2xl font-bold">{avgCompleteness.toFixed(1)}%</h3>
                <p className="text-gray-600">Data Completeness</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-lg p-6 transform hover:scale-105 transition-transform">
            <div className="flex items-center">
              <div className="text-3xl text-orange-500 mr-4">🔄</div>
              <div>
                <h3 className="text-2xl font-bold">{filteredData.length}</h3>
                <p className="text-gray-600">Filtered Results</p>
              </div>
            </div>
          </div>
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-xl font-bold mb-4">Top States by Business Count</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={stateChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="state" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#3498db" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-xl font-bold mb-4">Business Types Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={typeChartData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ type, percent }) => `${type} (${(percent * 100).toFixed(0)}%)`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="count"
                >
                  {typeChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <h3 className="text-xl font-bold mb-4">Filters</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">State</label>
              <select 
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                value={filters.state}
                onChange={(e) => handleFilterChange('state', e.target.value)}
              >
                <option value="all">All States</option>
                {getUniqueValues('State').map(state => (
                  <option key={state} value={state}>{state}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Business Type</label>
              <select 
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                value={filters.type}
                onChange={(e) => handleFilterChange('type', e.target.value)}
              >
                <option value="all">All Types</option>
                {getUniqueValues('Type').map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Search</label>
              <input 
                type="text"
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Search businesses..."
                value={filters.search}
                onChange={(e) => handleFilterChange('search', e.target.value)}
              />
            </div>
          </div>
        </div>

        {/* Data Table */}
        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-xl font-bold">Business Directory ({filteredData.length} results)</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Business Name</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Address</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">City</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">State</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Phone</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Website</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredData.slice(0, 50).map((row, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {row['Business Name']}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {row.Type}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">
                      {row.Address}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {row.City}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {row.State}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {row.Phone || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {row.Website && row.Website !== 'N/A' ? (
                        <a 
                          href={row.Website} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-800 underline"
                        >
                          Visit Site
                        </a>
                      ) : 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {filteredData.length > 50 && (
            <div className="px-6 py-3 bg-gray-50 text-sm text-gray-500">
              Showing first 50 of {filteredData.length} results
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default FuneralServicesDashboard;
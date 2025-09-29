import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#AF19FF', '#FF4242'];

const DynamicChart = ({ chartSpec }) => {
  if (!chartSpec || !chartSpec.data) {
    return null;
  }

  const { type, data, x_axis, y_axis, title } = chartSpec;

  const renderChart = () => {
    switch (type) {
      case 'bar':
        return (
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={x_axis} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey={y_axis} fill="#8884d8" />
          </BarChart>
        );
      case 'line':
        return (
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={x_axis} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey={y_axis} stroke="#82ca9d" />
          </LineChart>
        );
      case 'pie':
        return (
          <PieChart>
            <Pie data={data} dataKey={y_axis} nameKey={x_axis} cx="50%" cy="50%" outerRadius={100} fill="#8884d8" label>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        );
      default:
        return <p>Unsupported chart type: {type}</p>;
    }
  };

  return (
    <div className="chart-container">
      <h4>{title || 'Chart'}</h4>
      <ResponsiveContainer width="100%" height={300}>
        {renderChart()}
      </ResponsiveContainer>
    </div>
  );
};

export default DynamicChart;
"use client";

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

interface SentimentChartProps {
  data: {
    positive: number;
    negative: number;
    neutral: number;
  };
}

export default function SentimentChart({ data }: SentimentChartProps) {
  const chartData = [
    { name: '긍정', value: data.positive, color: '#10B981' },
    { name: '부정', value: data.negative, color: '#EF4444' },
    { name: '중립', value: data.neutral, color: '#6B7280' },
  ];

  const total = data.positive + data.negative + data.neutral;

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0];
      const percentage = total > 0 ? ((data.value / total) * 100).toFixed(1) : 0;
      return (
        <div className="bg-white p-3 rounded-lg shadow-lg border">
          <p className="font-semibold">{data.name}</p>
          <p className="text-sm text-gray-600">
            {data.value}개 ({percentage}%)
          </p>
        </div>
      );
    }
    return null;
  };

  if (total === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        <p>분석된 데이터가 없습니다</p>
      </div>
    );
  }

  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={100}
            paddingAngle={2}
            dataKey="value"
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend 
            verticalAlign="bottom" 
            height={36}
            iconType="circle"
            formatter={(value, entry) => (
              <span style={{ color: entry?.color }}>
                {value} ({entry?.payload?.value ?? 0}개)
              </span>
            )}
          />
        </PieChart>
      </ResponsiveContainer>

      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4 mt-4">
        <div className="text-center">
          <div className="text-2xl font-bold text-green-600">{data.positive}</div>
          <div className="text-sm text-gray-600">긍정</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-red-600">{data.negative}</div>
          <div className="text-sm text-gray-600">부정</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-gray-600">{data.neutral}</div>
          <div className="text-sm text-gray-600">중립</div>
        </div>
      </div>
    </div>
  );
}

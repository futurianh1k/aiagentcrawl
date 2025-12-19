"use client";

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface KeywordCloudProps {
  data: Array<{
    keyword: string;
    frequency: number;
    sentiment_score: number;
  }>;
}

export default function KeywordCloud({ data }: KeywordCloudProps) {
  // 데이터를 빈도순으로 정렬하고 상위 10개만 표시
  const sortedData = data
    .sort((a, b) => b.frequency - a.frequency)
    .slice(0, 10)
    .map(item => ({
      ...item,
      // 감정 점수에 따라 색상 결정을 위한 필드 추가
      sentiment: item.sentiment_score > 0.1 ? 'positive' : 
                item.sentiment_score < -0.1 ? 'negative' : 'neutral'
    }));

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 rounded-lg shadow-lg border">
          <p className="font-semibold">{label}</p>
          <p className="text-sm text-gray-600">빈도: {data.frequency}회</p>
          <p className="text-sm text-gray-600">
            감정 점수: {data.sentiment_score.toFixed(2)}
          </p>
          <p className={`text-sm font-medium ${
            data.sentiment === 'positive' ? 'text-green-600' :
            data.sentiment === 'negative' ? 'text-red-600' : 'text-gray-600'
          }`}>
            {data.sentiment === 'positive' ? '긍정적' :
             data.sentiment === 'negative' ? '부정적' : '중립적'}
          </p>
        </div>
      );
    }
    return null;
  };

  // 감정에 따른 색상 반환
  const getBarColor = (sentiment: string) => {
    switch (sentiment) {
      case 'positive': return '#10B981';
      case 'negative': return '#EF4444';
      default: return '#6B7280';
    }
  };

  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        <p>키워드 데이터가 없습니다</p>
      </div>
    );
  }

  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={sortedData}
          margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="keyword" 
            angle={-45}
            textAnchor="end"
            height={80}
            interval={0}
            fontSize={12}
          />
          <YAxis />
          <Tooltip content={<CustomTooltip />} />
          <Bar 
            dataKey="frequency" 
            fill={(entry) => getBarColor(entry?.sentiment)}
            radius={[2, 2, 0, 0]}
          >
            {sortedData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getBarColor(entry.sentiment)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Legend */}
      <div className="flex justify-center mt-4 space-x-6 text-sm">
        <div className="flex items-center">
          <div className="w-3 h-3 bg-green-500 rounded mr-2"></div>
          <span>긍정적</span>
        </div>
        <div className="flex items-center">
          <div className="w-3 h-3 bg-red-500 rounded mr-2"></div>
          <span>부정적</span>
        </div>
        <div className="flex items-center">
          <div className="w-3 h-3 bg-gray-500 rounded mr-2"></div>
          <span>중립적</span>
        </div>
      </div>
    </div>
  );
}
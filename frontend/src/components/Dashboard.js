import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Scatter } from 'recharts';

const TechnicalIndicatorChart = ({ data, indicator, color }) => {
  const values = data.map(item => item[indicator]).filter(value => value !== null && !isNaN(value));
  const min = Math.min(...values);
  const max = Math.max(...values);
  const padding = (max - min) * 0.1;
  const domain = [Math.floor(min - padding), Math.ceil(max + padding)];

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis domain={domain} />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey={indicator} stroke={color} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
};

const PriceMovementChart = ({ data, signals, trades }) => {
  console.log('Trades data:', trades);
  const prices = data.map(item => item.close).filter(value => value !== null && !isNaN(value));
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const padding = (maxPrice - minPrice) * 0.1;
  const domain = [Math.floor(minPrice - padding), Math.ceil(maxPrice + padding)];

  // Generate a unique color for each combination of indicators
  const getTradeColor = (indicators) => {
    const hash = indicators.sort().join(',');
    let color = '#';
    for (let i = 0; i < 3; i++) {
      const value = (hash.charCodeAt(i * 2) * 255) % 255;
      color += ('0' + value.toString(16)).substr(-2);
    }
    return color;
  };

  // Prepare trade data for the chart
  const tradeMarkers = trades.flatMap(trade => [
    {
      date: new Date(trade.buy_date).toISOString().split('T')[0],
      close: trade.buy_price,
      tradeColor: getTradeColor(trade.indicators),
      action: 'buy'
    },
    {
      date: new Date(trade.sell_date).toISOString().split('T')[0],
      close: trade.sell_price,
      tradeColor: getTradeColor(trade.indicators),
      action: 'sell'
    }
  ]);

  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis domain={domain} />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="close" stroke="#8884d8" dot={false} />
        <Line 
        type="monotone" 
        data={tradeMarkers} 
        dataKey="close" 
        stroke="red" 
        dot={{ fill: 'red', r: 6 }}
/>
        {Object.entries(signals).map(([indicator, signalData]) => (
          <Scatter
            key={indicator}
            name={`${indicator} 信号`}
            data={signalData}
            fill={getIndicatorColor(indicator)}
            shape="star"
          />
        ))}
        <Scatter
          name="交易"
          data={tradeMarkers}
          shape={(props) => {
            const { cx, cy, fill } = props;
            return props.payload.action === 'buy' 
              ? <polygon points={`${cx},${cy-8} ${cx-6},${cy+4} ${cx+6},${cy+4}`} fill={fill} stroke="black" strokeWidth={1}/> 
              : <circle cx={cx} cy={cy}  r={4} fill={fill} stroke="black" strokeWidth={1} />;
          }}
          fill={(entry) => entry.tradeColor}
        />
      </LineChart>
    </ResponsiveContainer>
  );
};

const IndicatorTable = ({ data }) => (
  <table className="min-w-full bg-white">
    <thead>
      <tr>
        <th className="px-4 py-2 border-b-2 border-gray-200 bg-gray-100 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
          日期
        </th>
        <th className="px-4 py-2 border-b-2 border-gray-200 bg-gray-100 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
          指标
        </th>
        <th className="px-4 py-2 border-b-2 border-gray-200 bg-gray-100 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
          数值
        </th>
        <th className="px-4 py-2 border-b-2 border-gray-200 bg-gray-100 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
          操作
        </th>
      </tr>
    </thead>
    <tbody>
      {data.map((row, index) => (
        <tr key={index}>
          <td className="px-4 py-2 border-b border-gray-200">{row.date}</td>
          <td className="px-4 py-2 border-b border-gray-200">{row.indicator}</td>
          <td className="px-4 py-2 border-b border-gray-200">{row.value.toFixed(2)}</td>
          <td className="px-4 py-2 border-b border-gray-200">{row.action === 'buy' ? '买入' : '卖出'}</td>
        </tr>
      ))}
    </tbody>
  </table>
);

const TradesTable = ({ data }) => (
  <table className="min-w-full bg-white mt-4">
    <thead>
      <tr>
        <th className="px-4 py-2 border-b-2 border-gray-200 bg-gray-100 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
          买入日期
        </th>
        <th className="px-4 py-2 border-b-2 border-gray-200 bg-gray-100 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
          卖出日期
        </th>
        <th className="px-4 py-2 border-b-2 border-gray-200 bg-gray-100 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
          买入价格
        </th>
        <th className="px-4 py-2 border-b-2 border-gray-200 bg-gray-100 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
          卖出价格
        </th>
        <th className="px-4 py-2 border-b-2 border-gray-200 bg-gray-100 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
          利润
        </th>
        <th className="px-4 py-2 border-b-2 border-gray-200 bg-gray-100 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
          指标
        </th>
      </tr>
    </thead>
    <tbody>
      {data.map((trade, index) => (
        <tr key={index}>
          <td className="px-4 py-2 border-b border-gray-200">{trade.buy_date}</td>
          <td className="px-4 py-2 border-b border-gray-200">{trade.sell_date}</td>
          <td className="px-4 py-2 border-b border-gray-200">{trade.buy_price.toFixed(2)}</td>
          <td className="px-4 py-2 border-b border-gray-200">{trade.sell_price.toFixed(2)}</td>
          <td className="px-4 py-2 border-b border-gray-200">{trade.profit.toFixed(2)}</td>
          <td className="px-4 py-2 border-b border-gray-200">{trade.indicators.join(', ')}</td>
        </tr>
      ))}
    </tbody>
  </table>
);

const getIndicatorColor = (indicator) => {
  const colors = {
    SMA: '#FF6384',
    EMA: '#36A2EB',
    RSI: '#FFCE56',
    MACD: '#4BC0C0',
    BB: '#9966FF',
    Stoch: '#FF9F40',
    Ichimoku: '#FF6384',
    CCI: '#36A2EB',
    ADX: '#FFCE56',
    WILLR: '#4BC0C0'
  };
  return colors[indicator] || '#000000';
};

const Dashboard = () => {
  const [data, setData] = useState([]);
  const [indicatorData, setIndicatorData] = useState([]);
  const [signals, setSignals] = useState({});
  const [trades, setTrades] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        console.log('正在获取数据...');
        const apiUrl = 'https://3fxmtqm1-35ga8pke-f1mdr4eer6f4.ac1-preview.marscode.dev/api/sugar-options-data';
        const response = await fetch(apiUrl);
        console.log('收到响应:', response);
        if (!response.ok) {
          throw new Error(`HTTP 错误! 状态: ${response.status}`);
        }
        const jsonData = await response.json();
        console.log('收到数据:', jsonData);
        setData(jsonData.data);
        setIndicatorData(jsonData.indicatorData);
        setSignals(jsonData.signals);
        setTrades(jsonData.trades);
      } catch (error) {
        console.error('获取数据时出错:', error);
        setError(error.message);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  if (isLoading) {
    return <div>加载中...</div>;
  }

  if (error) {
    return <div>错误: {error}</div>;
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-4">糖期权技术分析仪表板</h1>
      
      {data.length > 0 ? (
        <>
          <h2 className="text-2xl font-semibold mt-8 mb-4">价格走势与指标信号</h2>
          <PriceMovementChart data={data} signals={signals} trades={trades} />

          <h2 className="text-2xl font-semibold mt-8 mb-4">技术指标</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <TechnicalIndicatorChart data={data} indicator="SMA_20" color="#FF6384" />
            <TechnicalIndicatorChart data={data} indicator="SMA_50" color="#36A2EB" />
            <TechnicalIndicatorChart data={data} indicator="EMA_20" color="#FFCE56" />
            <TechnicalIndicatorChart data={data} indicator="RSI" color="#4BC0C0" />
            <TechnicalIndicatorChart data={data} indicator="MACD_12_26_9" color="#9966FF" />
            <TechnicalIndicatorChart data={data} indicator="BBM_20_2.0" color="#FF9F40" />
            <TechnicalIndicatorChart data={data} indicator="STOCHk_14_3_3" color="#FF6384" />
            <TechnicalIndicatorChart data={data} indicator="ICH_0_ISA_9" color="#36A2EB" />
            <TechnicalIndicatorChart data={data} indicator="CCI" color="#FFCE56" />
            <TechnicalIndicatorChart data={data} indicator="ADX_14" color="#4BC0C0" />
            <TechnicalIndicatorChart data={data} indicator="WILLR" color="#9966FF" />
          </div>

          <h2 className="text-2xl font-semibold mt-8 mb-4">交易</h2>
          <TradesTable data={trades} />

          <h2 className="text-2xl font-semibold mt-8 mb-4">指标信号表</h2>
          <IndicatorTable data={indicatorData} />
        </>
      ) : (
        <p>没有可用的数据。请检查后端连接和数据源。</p>
      )}
    </div>
  );
};

export default Dashboard;
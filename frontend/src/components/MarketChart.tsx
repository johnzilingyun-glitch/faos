import React, { useEffect, useRef } from 'react';
import { createChart, ColorType } from 'lightweight-charts';

interface MarketChartProps {
  symbol?: string;
  data: { time: string; value: number }[];
  colors?: {
    backgroundColor?: string;
    lineColor?: string;
    textColor?: string;
    areaTopColor?: string;
    areaBottomColor?: string;
  };
}

export const MarketChart: React.FC<MarketChartProps> = (props) => {
  const {
    data,
    colors: {
      backgroundColor = 'transparent',
      lineColor = '#6366f1',
      textColor = '#475569',
      areaTopColor = 'rgba(99, 102, 241, 0.2)',
      areaBottomColor = 'rgba(99, 102, 241, 0.0)',
    } = {},
  } = props;

  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<any>(null);
  const seriesRef = useRef<any>(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: backgroundColor },
        textColor,
      },
      grid: {
        vertLines: { color: 'rgba(255, 255, 255, 0.05)' },
        horzLines: { color: 'rgba(255, 255, 255, 0.05)' },
      },
      width: chartContainerRef.current.clientWidth,
      height: 300,
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
      },
      rightPriceScale: {
        borderVisible: false,
      },
    });

    const newSeries = chart.addAreaSeries({
      lineColor,
      topColor: areaTopColor,
      bottomColor: areaBottomColor,
    });

    if (data && data.length > 0) {
      newSeries.setData(data);
    } else {
      // Mock data if no data provided yet (for preview)
      const mockData = [
        { time: '2023-01-01', value: 100 },
        { time: '2023-02-01', value: 120 },
        { time: '2023-03-01', value: 110 },
        { time: '2023-04-01', value: 140 },
        { time: '2023-05-01', value: 135 },
        { time: '2023-06-01', value: 160 },
      ];
      newSeries.setData(mockData);
    }

    chartRef.current = chart;
    seriesRef.current = newSeries;

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (chartRef.current) {
        chartRef.current.remove();
      }
    };
  }, [data, backgroundColor, lineColor, textColor, areaTopColor, areaBottomColor]);

  return (
    <div className="impeccable-card" style={{ marginBottom: '2rem', padding: '1rem' }}>
      <div className="card-header" style={{ paddingLeft: '1rem', paddingTop: '1rem' }}>
        <div className="card-title">{props.symbol ? `${props.symbol} Market Data` : 'Market Chart'}</div>
      </div>
      <div
        ref={chartContainerRef}
        style={{ width: '100%', height: '300px' }}
      />
    </div>
  );
};

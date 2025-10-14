/**
 * HistoricalChart component - ECharts with zoom/pan for historical data analysis (User Story 4)
 */
import React, { useRef, useEffect } from 'react';
import * as echarts from 'echarts';
import { useTranslation } from 'react-i18next';

export interface HistoricalDataPoint {
  timestamp: string;
  value: number;
}

export interface HistoricalChartProps {
  data: HistoricalDataPoint[];
  unit: string;
  deviceName?: string;
  height?: number;
  enableZoom?: boolean;
  enableDataZoom?: boolean;
  loading?: boolean;
}

const HistoricalChart: React.FC<HistoricalChartProps> = ({
  data,
  unit,
  deviceName,
  height = 400,
  enableZoom = true,
  enableDataZoom = true,
  loading = false,
}) => {
  const { t } = useTranslation();
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    console.log('[HistoricalChart] useEffect triggered', { hasRef: !!chartRef.current, hasInstance: !!chartInstance.current, dataLength: data.length });

    if (!chartRef.current) {
      console.log('[HistoricalChart] No chartRef, returning');
      return;
    }

    // Initialize chart if not already initialized
    if (!chartInstance.current) {
      console.log('[HistoricalChart] Initializing ECharts instance');
      chartInstance.current = echarts.init(chartRef.current);
    }

    // Show loading
    if (loading) {
      chartInstance.current.showLoading();
      return;
    } else {
      chartInstance.current.hideLoading();
    }

    // Prepare data
    const timestamps = data.map(d => new Date(d.timestamp));
    const values = data.map(d => d.value);

    // Debug logging
    console.log('[HistoricalChart] Rendering with data:', {
      dataLength: data.length,
      firstTimestamp: timestamps[0]?.toISOString(),
      lastTimestamp: timestamps[timestamps.length - 1]?.toISOString(),
      valueRange: [Math.min(...values), Math.max(...values)],
      sampleData: data.slice(0, 3)
    });

    // Chart configuration
    const option: echarts.EChartsOption = {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
          label: {
            backgroundColor: '#6a7985',
          },
        },
        formatter: (params: any) => {
          const param = params[0];
          const timestamp = timestamps[param.dataIndex];
          const value = param.value;

          return `
            <div style="padding: 8px;">
              <strong>${timestamp.toLocaleString()}</strong><br/>
              ${t('common.value', { defaultValue: 'Value' })}: <strong>${value} ${unit}</strong>
            </div>
          `;
        },
      },
      legend: {
        data: [deviceName || t('common.value', { defaultValue: 'Value' })],
        bottom: 10,
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: enableDataZoom ? '15%' : '10%',
        top: '10%',
        containLabel: true,
      },
      toolbox: {
        feature: {
          saveAsImage: {
            title: t('common.export', { defaultValue: 'Export' }),
            name: `${deviceName || 'chart'}_${new Date().toISOString().split('T')[0]}`,
          },
          dataZoom: enableZoom ? {
            yAxisIndex: 'none',
            title: {
              zoom: t('historical.zoom', { defaultValue: 'Zoom' }),
              back: t('historical.resetZoom', { defaultValue: 'Reset Zoom' }),
            },
          } : undefined,
          restore: {
            title: t('historical.restore', { defaultValue: 'Restore' }),
          },
        },
        right: 20,
        top: 10,
      },
      xAxis: {
        type: 'time',
        boundaryGap: false,
        axisLabel: {
          formatter: (value: number) => {
            const date = new Date(value);
            // Format based on zoom level
            if (data.length > 0) {
              const timeRange = timestamps[timestamps.length - 1].getTime() - timestamps[0].getTime();
              const oneDay = 24 * 60 * 60 * 1000;
              const oneHour = 60 * 60 * 1000;

              if (timeRange > 7 * oneDay) {
                // Show date for ranges > 7 days
                return date.toLocaleDateString();
              } else if (timeRange > oneDay) {
                // Show date and time for 1-7 days
                return `${date.toLocaleDateString()} ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
              } else {
                // Show time for ranges < 1 day
                return date.toLocaleTimeString();
              }
            }
            return date.toLocaleString();
          },
        },
      },
      yAxis: {
        type: 'value',
        name: unit,
        axisLabel: {
          formatter: `{value} ${unit}`,
        },
        scale: true, // Auto-scale based on data
      },
      dataZoom: enableDataZoom ? [
        {
          type: 'inside',
          start: 0,
          end: 100,
          zoomOnMouseWheel: true,
          moveOnMouseMove: true,
          moveOnMouseWheel: false,
        },
        {
          type: 'slider',
          start: 0,
          end: 100,
          height: 30,
          bottom: 20,
        },
      ] : undefined,
      series: [
        {
          name: deviceName || t('common.value', { defaultValue: 'Value' }),
          type: 'line',
          smooth: true,
          symbol: 'none', // Hide symbols for better performance with large datasets
          sampling: 'lttb', // Largest-Triangle-Three-Buckets downsampling
          lineStyle: {
            width: 2,
            color: '#1890ff',
          },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(24, 144, 255, 0.3)' },
              { offset: 1, color: 'rgba(24, 144, 255, 0.05)' },
            ]),
          },
          data: timestamps.map((ts, idx) => [ts.getTime(), values[idx]]),
        },
      ],
    };

    chartInstance.current.setOption(option, true);
    console.log('[HistoricalChart] Chart option set successfully');

    // Cleanup on unmount
    return () => {
      // No cleanup needed for this effect
    };
  }, [data, unit, deviceName, height, enableZoom, enableDataZoom, loading, t]);

  // Handle window resize and cleanup on unmount
  useEffect(() => {
    const handleResize = () => {
      chartInstance.current?.resize();
    };

    window.addEventListener('resize', handleResize);

    // Cleanup function runs ONLY when component unmounts
    return () => {
      window.removeEventListener('resize', handleResize);
      if (chartInstance.current) {
        console.log('[HistoricalChart] Disposing chart instance on unmount');
        chartInstance.current.dispose();
        chartInstance.current = null;
      }
    };
  }, []);

  return (
    <div className="historical-chart">
      <div ref={chartRef} style={{ width: '100%', height: `${height}px` }} />
      {data.length > 0 && (
        <div className="chart-info" style={{ textAlign: 'center', marginTop: '8px', color: '#888' }}>
          {t('historical.dataPoints', { count: data.length, defaultValue: `${data.length} data points` })}
        </div>
      )}
    </div>
  );
};

export default HistoricalChart;

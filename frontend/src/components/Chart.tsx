/**
 * Chart component - wrapper for ECharts with threshold visualization
 */
import React, { useRef, useEffect } from 'react';
import * as echarts from 'echarts';
import { useTranslation } from 'react-i18next';

export interface ChartDataPoint {
  timestamp: string;
  value: number;
}

export interface ChartThresholds {
  warningLower?: number;
  warningUpper?: number;
  criticalLower?: number;
  criticalUpper?: number;
}

export interface ChartProps {
  data: ChartDataPoint[];
  unit: string;
  thresholds?: ChartThresholds;
  height?: number;
  onPointHover?: (dataPoint: ChartDataPoint) => void;
}

const Chart: React.FC<ChartProps> = ({
  data,
  unit,
  thresholds,
  height = 300,
  onPointHover,
}) => {
  const { t } = useTranslation();
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!chartRef.current) return;

    // Initialize chart
    chartInstance.current = echarts.init(chartRef.current);

    // Prepare data
    const timestamps = data.map(d => new Date(d.timestamp).toLocaleTimeString());
    const values = data.map(d => d.value);

    // Build markLine data for thresholds
    const markLineData: any[] = [];

    if (thresholds?.criticalUpper !== undefined) {
      markLineData.push({
        yAxis: thresholds.criticalUpper,
        name: t('chart.threshold.criticalUpper', { defaultValue: 'Critical Upper' }),
        lineStyle: { color: '#f5222d', type: 'dashed' },
        label: { formatter: `Critical: {c} ${unit}` },
      });
    }

    if (thresholds?.warningUpper !== undefined) {
      markLineData.push({
        yAxis: thresholds.warningUpper,
        name: t('chart.threshold.warningUpper', { defaultValue: 'Warning Upper' }),
        lineStyle: { color: '#faad14', type: 'dashed' },
        label: { formatter: `Warning: {c} ${unit}` },
      });
    }

    if (thresholds?.warningLower !== undefined) {
      markLineData.push({
        yAxis: thresholds.warningLower,
        name: t('chart.threshold.warningLower', { defaultValue: 'Warning Lower' }),
        lineStyle: { color: '#faad14', type: 'dashed' },
        label: { formatter: `Warning: {c} ${unit}` },
      });
    }

    if (thresholds?.criticalLower !== undefined) {
      markLineData.push({
        yAxis: thresholds.criticalLower,
        name: t('chart.threshold.criticalLower', { defaultValue: 'Critical Lower' }),
        lineStyle: { color: '#f5222d', type: 'dashed' },
        label: { formatter: `Critical: {c} ${unit}` },
      });
    }

    // Chart configuration
    const option: echarts.EChartsOption = {
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => {
          const param = params[0];
          const dataPoint = data[param.dataIndex];

          // Trigger hover callback
          if (onPointHover && dataPoint) {
            onPointHover(dataPoint);
          }

          return `
            <div>
              <strong>${new Date(dataPoint.timestamp).toLocaleString()}</strong><br/>
              Value: ${param.value} ${unit}
            </div>
          `;
        },
      },
      xAxis: {
        type: 'category',
        data: timestamps,
        boundaryGap: false,
      },
      yAxis: {
        type: 'value',
        name: unit,
        axisLabel: {
          formatter: `{value} ${unit}`,
        },
      },
      series: [
        {
          name: 'Value',
          type: 'line',
          data: values,
          smooth: true,
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
          markLine: markLineData.length > 0 ? { data: markLineData, symbol: 'none' } : undefined,
        },
      ],
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true,
      },
    };

    chartInstance.current.setOption(option);

    // Cleanup
    return () => {
      chartInstance.current?.dispose();
    };
  }, [data, unit, thresholds, onPointHover, t]);

  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      chartInstance.current?.resize();
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return <div ref={chartRef} style={{ width: '100%', height: `${height}px` }} />;
};

export default Chart;

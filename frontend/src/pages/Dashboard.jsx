import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { Chart as ChartJS, ArcElement, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';
import { Pie, Bar } from 'react-chartjs-2';
import { History, Activity, AlertCircle, RefreshCw } from 'lucide-react';

ChartJS.register(ArcElement, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [statsRes, historyRes] = await Promise.all([
        api.get('/ml/stats'),
        api.get('/ml/history')
      ]);
      setStats(statsRes.data);
      setHistory(historyRes.data);
    } catch (err) {
      setError('Failed to fetch dashboard data. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex bg-slate-900 min-h-[calc(100vh-4rem)] items-center justify-center">
        <RefreshCw className="w-8 h-8 text-indigo-500 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex bg-slate-900 min-h-[calc(100vh-4rem)] items-center justify-center p-4">
        <div className="bg-rose-500/10 border border-rose-500/50 text-rose-400 p-6 rounded-2xl flex items-center gap-4">
          <AlertCircle className="w-8 h-8 shrink-0" />
          <p className="font-medium">{error}</p>
        </div>
      </div>
    );
  }

  const pieData = {
    labels: ['Real News', 'Fake News'],
    datasets: [
      {
        data: [stats?.real_count || 0, stats?.fake_count || 0],
        backgroundColor: ['rgba(16, 185, 129, 0.2)', 'rgba(244, 63, 94, 0.2)'],
        borderColor: ['rgba(16, 185, 129, 1)', 'rgba(244, 63, 94, 1)'],
        borderWidth: 2,
      },
    ],
  };

  const chartOptions = {
    plugins: {
      legend: { labels: { color: '#e2e8f0' } }
    }
  };

  return (
    <div className="bg-slate-900 min-h-[calc(100vh-4rem)] p-4 md:p-8 text-slate-200">
      <div className="max-w-6xl mx-auto space-y-8">
        
        <div className="flex items-center gap-3 border-b border-slate-700/50 pb-6 rounded-t-xl bg-slate-800/20 px-8 pt-8">
          <div className="p-3 bg-indigo-500/20 rounded-xl">
            <Activity className="w-8 h-8 text-indigo-400" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-white tracking-tight">Analytics Dashboard</h1>
            <p className="text-slate-400 mt-1">Your fake news detection history and statistics</p>
          </div>
        </div>

        {/* Stats Summary */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 px-4 md:px-0">
          <div className="bg-slate-800/40 p-6 rounded-2xl border border-slate-700/50 flex flex-col items-center justify-center">
            <span className="text-slate-400 uppercase text-xs font-bold tracking-widest mb-2">Total Scanned</span>
            <span className="text-4xl font-black text-indigo-400">{stats?.total_predictions}</span>
          </div>
          <div className="bg-emerald-900/20 p-6 rounded-2xl border border-emerald-500/30 flex flex-col items-center justify-center">
            <span className="text-slate-400 uppercase text-xs font-bold tracking-widest mb-2">Real Detected</span>
            <span className="text-4xl font-black text-emerald-400">{stats?.real_count}</span>
          </div>
          <div className="bg-rose-900/20 p-6 rounded-2xl border border-rose-500/30 flex flex-col items-center justify-center">
            <span className="text-slate-400 uppercase text-xs font-bold tracking-widest mb-2">Fake Detected</span>
            <span className="text-4xl font-black text-rose-400">{stats?.fake_count}</span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 px-4 md:px-0">
          {/* Chart Section */}
          <div className="lg:col-span-1 bg-slate-800/40 border border-slate-700/50 rounded-2xl p-6 flex flex-col items-center shadow-xl">
            <h3 className="text-lg font-semibold text-slate-300 mb-6 self-start">Distribution</h3>
            <div className="w-64 h-64">
              {stats?.total_predictions > 0 ? (
                <Pie data={pieData} options={chartOptions} />
              ) : (
                <div className="h-full flex items-center justify-center text-slate-500 text-sm">No data to chart yet.</div>
              )}
            </div>
          </div>

          {/* History Section */}
          <div className="lg:col-span-2 bg-slate-800/40 border border-slate-700/50 rounded-2xl p-6 shadow-xl overflow-hidden flex flex-col">
            <div className="flex items-center gap-2 mb-6 text-slate-300">
              <History className="w-5 h-5" />
              <h3 className="text-lg font-semibold">Recent Predictions</h3>
            </div>
            
            <div className="flex-1 overflow-y-auto max-h-[400px] pr-2 space-y-3 custom-scrollbar">
              {history.length === 0 ? (
                <div className="text-center text-slate-500 py-10">No history found. Try analyzing a text first.</div>
              ) : (
                history.map((record) => (
                  <div key={record.id} className="bg-slate-900/50 border border-slate-700/50 rounded-xl p-4 hover:border-indigo-500/30 transition-colors">
                    <div className="flex justify-between items-start mb-2 gap-4">
                      <span className={`text-xs font-bold uppercase tracking-wider px-2 py-1 rounded w-fit ${record.prediction === 'REAL' ? 'text-emerald-400 bg-emerald-400/10' : 'text-rose-400 bg-rose-400/10'}`}>
                        {record.prediction} ({record.confidence.toFixed(1)}%)
                      </span>
                      <span className="text-xs text-slate-500 whitespace-nowrap">{new Date(record.timestamp).toLocaleString()}</span>
                    </div>
                    <p className="text-sm text-slate-300 line-clamp-3 leading-relaxed border-l-2 border-slate-600 pl-3 italic">"{record.text}"</p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

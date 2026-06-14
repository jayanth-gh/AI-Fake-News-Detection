import React, { useState } from 'react';
import api from '../services/api';
import { Send, Loader2, AlertTriangle, ShieldAlert, ShieldCheck, HelpCircle, ExternalLink, MessageSquare } from 'lucide-react';

const Home = () => {
  const [text, setText] = useState('');
  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handlePredict = async (e) => {
    e.preventDefault();
    if (!text.trim() && !image) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      let res;
      if (image) {
        const formData = new FormData();
        formData.append('file', image);
        res = await api.post('/ml/predict/image', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        
        // Show indicator that image was analyzed
        if (res.data && text === '') {
           setText("Image analyzed successfully. (Extracted text processed by AI)");
        }
      } else {
        res = await api.post('/ml/predict', { text });
      }
      setResult(res.data);
    } catch (err) {
      const detail = err.response?.data?.detail || err.message || 'An error occurred while analyzing.';
      if (err.response?.status === 503) {
         setError("Service temporarily unavailable. Our verification APIs might be down.");
      } else if (err.response?.status === 401) {
         setError('Please log in again to verify content.');
      } else {
         setError(detail);
      }
    } finally {
      setLoading(false);
    }
  };

  const getVerdictStyle = (prediction) => {
    if (prediction === 'REAL') return {
      container: 'bg-emerald-900/20 border-emerald-500/30 shadow-[0_0_40px_-10px_rgba(16,185,129,0.2)]',
      iconBg: 'bg-emerald-500/20 text-emerald-400',
      text: 'text-emerald-400',
      bar: 'bg-emerald-500',
      icon: <ShieldCheck className="w-12 h-12" />
    };
    if (prediction === 'FAKE') return {
      container: 'bg-rose-900/20 border-rose-500/30 shadow-[0_0_40px_-10px_rgba(244,63,94,0.2)]',
      iconBg: 'bg-rose-500/20 text-rose-400',
      text: 'text-rose-400',
      bar: 'bg-rose-500',
      icon: <ShieldAlert className="w-12 h-12" />
    };
    return {
      container: 'bg-yellow-900/20 border-yellow-500/30 shadow-[0_0_40px_-10px_rgba(234,179,8,0.2)]',
      iconBg: 'bg-yellow-500/20 text-yellow-400',
      text: 'text-yellow-400',
      bar: 'bg-yellow-500',
      icon: <HelpCircle className="w-12 h-12" /> // UNCERTAIN
    };
  };

  return (
    <div className="bg-slate-900 min-h-[calc(100vh-4rem)] p-4 md:p-8 text-slate-200">
      <div className="max-w-4xl mx-auto space-y-8">
        
        {/* Header Section */}
        <div className="text-center space-y-4 pt-10 pb-4">
          <h1 className="text-4xl md:text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-cyan-400 tracking-tight">
            Real-Time Fact Checker
          </h1>
          <p className="text-slate-400 text-lg md:text-xl max-w-2xl mx-auto">
            Paste a claim or news excerpt below. Our AI scours live search engines and cross-compares sources to determine its factual accuracy.
          </p>
        </div>

        {/* Input Section */}
        <div className="bg-slate-800/50 backdrop-blur-xl border border-slate-700/50 rounded-2xl shadow-2xl overflow-hidden p-6 md:p-8">
          <form onSubmit={handlePredict} className="space-y-4">
            <div className="relative group">
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Paste the breaking news claim here..."
                className="w-full h-48 sm:h-64 bg-slate-900/50 border border-slate-700 rounded-xl p-4 text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all resize-y"
              ></textarea>
              <div className="absolute bottom-4 right-4 text-xs font-medium text-slate-500 bg-slate-800/80 px-2 py-1 rounded backdrop-blur-sm pointer-events-none">
                {text.length} chars
              </div>
            </div>
            
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mt-2">
              <div className="flex items-center gap-4">
                <input 
                    type="file" 
                    accept="image/*" 
                    className="text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:bg-indigo-500/20 file:text-indigo-400 hover:file:bg-indigo-500/30 file:cursor-pointer max-w-[200px] sm:max-w-xs"
                    onChange={(e) => {
                      const file = e.target.files[0];
                      if (file) {
                        setImage(file);
                        setPreview(URL.createObjectURL(file));
                        setText(''); // Prioritize image
                      }
                    }} 
                />
                {preview && <img src={preview} alt="Upload Preview" className="h-10 w-auto object-cover rounded border border-slate-600 shadow" />}
              </div>
              
              <button
                type="submit"
                disabled={loading || (text.length === 0 && !image)}
                className="bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-700 disabled:text-slate-400 disabled:cursor-not-allowed text-white font-semibold py-3 px-8 rounded-xl shadow-lg shadow-indigo-600/20 transition-all active:scale-95 flex items-center gap-2 group w-full justify-center sm:w-auto"
              >
                {loading ? (
                  <><Loader2 className="w-5 h-5 animate-spin" /> Analyzing...</>
                ) : (
                  <>Verify <Send className="w-5 h-5 group-hover:-translate-y-0.5 group-hover:translate-x-0.5 transition-transform" /></>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Error Section */}
        {error && (
          <div className="bg-rose-500/10 border border-rose-500/50 text-rose-400 p-6 rounded-2xl flex items-center gap-4 animate-in fade-in slide-in-from-bottom-4">
            <AlertTriangle className="w-8 h-8 shrink-0" />
            <p className="font-medium">{error}</p>
          </div>
        )}

        {/* Result Section */}
        {result && (() => {
          const style = getVerdictStyle(result.prediction);
          return (
            <div className="animate-in fade-in slide-in-from-bottom-8 duration-500 space-y-6">
              
              {/* Verdict Indicator */}
              <div className={`p-8 rounded-2xl border flex flex-col items-center justify-center text-center space-y-4 relative overflow-hidden ${style.container}`}>
                <div className={`p-4 rounded-full ${style.iconBg}`}>
                  {style.icon}
                </div>
                
                <div>
                  <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-widest mb-1">Live Fact Check Verdict</h2>
                  <div className="flex items-center justify-center gap-3">
                    <span className={`text-5xl font-extrabold ${style.text}`}>
                      {result.prediction}
                    </span>
                  </div>
                </div>

                <div className="w-full max-w-sm mt-4">
                  <div className="flex justify-between text-sm font-medium mb-2">
                    <span className="text-slate-400">Confidence</span>
                    <span className="text-white">{result.confidence.toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-2.5 overflow-hidden">
                    <div 
                      className={`h-full rounded-full transition-all duration-1000 ease-out ${style.bar}`} 
                      style={{ width: `${result.confidence}%` }}
                    ></div>
                  </div>
                </div>
              </div>

              {/* LLM Reasoning */}
              <div className="bg-white/5 backdrop-blur-xl border border-slate-700/50 rounded-2xl p-6 shadow-2xl">
                <div className="flex items-center gap-2 mb-6 border-b border-slate-700/50 pb-4">
                  <div className="p-2 bg-indigo-500/20 rounded-lg">
                    <MessageSquare className="w-5 h-5 text-indigo-400" />
                  </div>
                  <div>
                    <h3 className="text-xl font-semibold text-white">AI Fact-Check Analysis</h3>
                    <p className="text-slate-400 text-sm">Reasoning based on cross-referencing multiple live news sources</p>
                  </div>
                </div>
                <p className="text-slate-300 leading-relaxed text-lg whitespace-pre-line border-l-4 border-slate-600 pl-4 italic">
                  {result.reasoning}
                </p>
              </div>

              {/* Sources */}
              {result.sources && result.sources.length > 0 && (
                <div className="bg-slate-800/40 border border-slate-700/50 rounded-2xl p-6 shadow-2xl">
                  <h3 className="text-lg font-semibold text-white mb-4">Referenced Sources</h3>
                  <div className="grid gap-3 sm:grid-cols-2">
                    {result.sources.map((source, idx) => (
                      <a key={idx} href={source.url} target="_blank" rel="noopener noreferrer" className="block bg-slate-900/50 hover:bg-slate-800/80 border border-slate-700/50 rounded-xl p-4 transition-colors group relative overflow-hidden">
                        <div className="absolute top-0 right-0 w-12 h-12 bg-white/5 scale-150 rotate-45 transform translate-x-4 -translate-y-4 group-hover:bg-white/10 transition-colors"></div>
                        <div className="flex justify-between items-start mb-2 gap-4">
                          <h4 className="font-medium text-indigo-300 line-clamp-2 pr-4">{source.title}</h4>
                          <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded
                            ${source.stance === 'support' ? 'bg-emerald-500/20 text-emerald-400' : 
                              source.stance === 'contradict' ? 'bg-rose-500/20 text-rose-400' : 
                              'bg-slate-600/50 text-slate-300'}`}
                          >
                            {source.stance}
                          </span>
                        </div>
                        <div className="flex items-center gap-1 text-xs text-slate-500">
                          <ExternalLink className="w-3 h-3" />
                          <span className="truncate">{new URL(source.url || 'http://unknown.com').hostname.replace('www.', '')}</span>
                        </div>
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })()}
      </div>
    </div>
  );
};

export default Home;

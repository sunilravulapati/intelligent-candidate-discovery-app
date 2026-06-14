import Link from "next/link";

export const metadata = {
  title: "Redrob Candidate Discovery - Intelligence Suite",
  description: "Next-generation vector retrieval and machine learning ranking platform for high-performance candidate sourcing.",
};

export default function Home() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center relative overflow-hidden selection:bg-indigo-500/30 selection:text-indigo-200">
      
      {/* Background Gradients */}
      <div className="absolute top-[-10%] left-[-10%] w-[600px] h-[600px] bg-indigo-600/10 rounded-full blur-[120px] -z-10" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[600px] h-[600px] bg-purple-600/10 rounded-full blur-[120px] -z-10" />
      
      {/* Main Container */}
      <div className="max-w-4xl px-6 py-12 text-center flex flex-col items-center gap-8 relative z-10">
        
        {/* Glow Tag */}
        <div className="inline-flex items-center gap-2 bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 px-4 py-1.5 rounded-full text-xs font-semibold uppercase tracking-widest animate-pulse">
          🚀 Machine Learning & Vector-First Ingestion
        </div>

        {/* Hero Title */}
        <h1 className="text-4xl md:text-6xl font-black tracking-tight leading-tight text-transparent bg-clip-text bg-gradient-to-r from-slate-100 via-indigo-200 to-purple-300">
          Intelligent Candidate Discovery & Ranking
        </h1>

        {/* Subtitle */}
        <p className="text-slate-400 text-lg md:text-xl max-w-2xl leading-relaxed">
          Unlock the power of bi-encoder dense vector embeddings combined with high-precision XGBoost/LightGBM re-ranking. Streamline recruiter workflows and match ideal profiles in milliseconds.
        </p>

        {/* Feature Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full mt-6 text-left">
          
          {/* Card 1 */}
          <div className="bg-slate-900/50 backdrop-blur-md border border-slate-800 rounded-xl p-5 hover:border-indigo-500/40 transition duration-300">
            <div className="w-10 h-10 bg-indigo-500/10 border border-indigo-500/20 rounded-lg flex items-center justify-center mb-4 text-indigo-400">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <h3 className="text-base font-bold text-slate-200 mb-2">Vector Retrieval</h3>
            <p className="text-slate-400 text-xs leading-relaxed">
              Retrieve candidate matches using dense embeddings from Sentence-Transformers indexed in high-performance FAISS collections.
            </p>
          </div>

          {/* Card 2 */}
          <div className="bg-slate-900/50 backdrop-blur-md border border-slate-800 rounded-xl p-5 hover:border-purple-500/40 transition duration-300">
            <div className="w-10 h-10 bg-purple-500/10 border border-purple-500/20 rounded-lg flex items-center justify-center mb-4 text-purple-400">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10a2 2 0 01-2 2h-2a2 2 0 01-2-2zm9-1V4a1 1 0 00-1-1h-2a1 1 0 00-1 1v14a1 1 0 001 1h2a1 1 0 001-1z" />
              </svg>
            </div>
            <h3 className="text-base font-bold text-slate-200 mb-2">Tabular ML Ranking</h3>
            <p className="text-slate-400 text-xs leading-relaxed">
              Re-rank candidate pools by scoring tabular features (experience overlap, skills matching, expected salary) using XGBoost.
            </p>
          </div>

          {/* Card 3 */}
          <div className="bg-slate-900/50 backdrop-blur-md border border-slate-800 rounded-xl p-5 hover:border-emerald-500/40 transition duration-300">
            <div className="w-10 h-10 bg-emerald-500/10 border border-emerald-500/20 rounded-lg flex items-center justify-center mb-4 text-emerald-400">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-base font-bold text-slate-200 mb-2">Explainable AI</h3>
            <p className="text-slate-400 text-xs leading-relaxed">
              Format matching details into simple, human-readable insights to help recruiters understand the ranking.
            </p>
          </div>

        </div>

        {/* CTA Button */}
        <div className="mt-8 flex flex-col sm:flex-row gap-4 items-center justify-center">
          <Link
            id="enter-dashboard-cta"
            href="/dashboard"
            className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-semibold py-4 px-8 rounded-xl shadow-lg shadow-indigo-500/25 hover:shadow-indigo-500/35 transition-all text-sm group flex items-center gap-2"
          >
            <span>Enter Recruiter Workspace</span>
            <svg className="w-4 h-4 transform group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 5l7 7-7 7" />
            </svg>
          </Link>
          <a
            href="https://github.com"
            target="_blank"
            rel="noreferrer"
            className="bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 font-semibold py-4 px-8 rounded-xl transition-all text-sm"
          >
            Read System Documentation
          </a>
        </div>

      </div>
      
      {/* Wave bottom decoration */}
      <div className="absolute bottom-0 left-0 w-full overflow-hidden leading-none z-0 opacity-20">
        <svg viewBox="0 0 1200 120" preserveAspectRatio="none" className="relative block w-full h-12 text-slate-900 fill-current">
          <path d="M321.39,56.44c58-10.79,114.16-30.13,172-41.86,82.39-16.72,168.19-17.73,250.45-.39C823.78,31,906.67,72,985.66,92.83c70.05,18.48,146.53,26.09,214.34,3V120H0V0C26.9,8.75,57.05,18.3,90.47,26.85,140.78,39.75,201.14,47.1,321.39,56.44Z" />
        </svg>
      </div>

    </div>
  );
}

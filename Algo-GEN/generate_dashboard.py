"""
Dashboard HTML Generator for GA-CVRP Results
Usage: python generate_dashboard.py
Works with all_results.json that gets updated with each main.py run
"""
import json
import os
from datetime import datetime

KNOWN_OPTIMUM = 961

def generate_dashboard_html(results_data):
    """
    Generate interactive HTML dashboard for GA results.
    
    Args:
        results_data: List of result dictionaries with keys:
                     instance, method, best_cost, execution_time, feasible
    """
    
    if not results_data:
        print("❌ No data provided!")
        return None
    
    # Handle both single result and list of results
    if isinstance(results_data, dict):
        results_data = [results_data]
    
    # Filter feasible results for ranking
    feasible_results = [r for r in results_data if r.get('feasible', False)]
    
    if not feasible_results:
        feasible_results = results_data
    
    # Sort by cost
    sorted_results = sorted(feasible_results, key=lambda x: x.get('best_cost', float('inf')))
    
    # Calculate statistics
    best_result = sorted_results[0] if sorted_results else results_data[0]
    avg_cost = sum(r.get('best_cost', 0) for r in feasible_results) / len(feasible_results) if feasible_results else 0
    avg_time = sum(r.get('execution_time', 0) for r in results_data) / len(results_data)
    feasible_count = sum(1 for r in results_data if r.get('feasible', False))
    
    # Calculate gap_percent if not present
    for r in results_data:
        if 'gap_percent' not in r and 'best_cost' in r:
            r['gap_percent'] = round(((r['best_cost'] - KNOWN_OPTIMUM) / KNOWN_OPTIMUM) * 100, 2)
        elif 'gap_percent' not in r:
            r['gap_percent'] = 0
    
    # Convert to JSON for JavaScript
    results_json = json.dumps(results_data)
    sorted_results_json = json.dumps(sorted_results)
    
    # JavaScript code for interactivity
    js_code = """
        const allResults = """ + results_json + """;
        const sortedResults = """ + sorted_results_json + """;
        const KNOWN_OPTIMUM = """ + str(KNOWN_OPTIMUM) + """;
        
        // Populate results table
        const tableBody = document.getElementById('resultsTable');
        sortedResults.forEach((result, index) => {
            const row = document.createElement('tr');
            const gapPercent = result.gap_percent || (((result.best_cost - KNOWN_OPTIMUM) / KNOWN_OPTIMUM) * 100).toFixed(1);
            const gapClass = gapPercent < 5 ? 'bg-emerald-500/20 text-emerald-400' :
                           gapPercent < 10 ? 'bg-amber-500/20 text-amber-400' :
                           'bg-rose-500/20 text-rose-400';
            
            row.className = `border-b border-gray-700 hover:bg-gray-700/50 transition ${index === 0 ? 'bg-emerald-500/10 font-semibold' : ''}`;
            
            row.innerHTML = `
                <td class="py-4 px-4">
                    <span class="font-bold ${index === 0 ? 'text-emerald-400 text-lg' : 'text-gray-400'}">
                        ${index === 0 ? '🏆' : index + 1}
                    </span>
                </td>
                <td class="py-4 px-4 font-medium text-gray-100 text-sm">${result.method}</td>
                <td class="py-4 px-4 text-right font-mono font-bold text-cyan-400">${result.best_cost.toFixed(2)}</td>
                <td class="py-4 px-4 text-right">
                    <span class="font-semibold px-3 py-1 rounded-full text-xs ${gapClass}">
                        ${gapPercent.toFixed(1)}%
                    </span>
                </td>
                <td class="py-4 px-4 text-right text-sm text-gray-300">${result.execution_time.toFixed(2)}s</td>
                <td class="py-4 px-4 text-center text-lg">
                    ${result.feasible ? '✅' : '❌'}
                </td>
            `;
            tableBody.appendChild(row);
        });
        
        // Cost comparison chart
        const costCtx = document.getElementById('costChart').getContext('2d');
        new Chart(costCtx, {
            type: 'bar',
            data: {
                labels: sortedResults.map((r, i) => `${i+1}. ${r.method}`),
                datasets: [{
                    label: 'Best Cost',
                    data: sortedResults.map(r => r.best_cost),
                    backgroundColor: sortedResults.map((r, i) => 
                        i === 0 ? 'rgba(16, 185, 129, 0.95)' : 'rgba(6, 182, 212, 0.85)'
                    ),
                    borderColor: sortedResults.map((r, i) => 
                        i === 0 ? 'rgb(5, 150, 105)' : 'rgb(8, 145, 178)'
                    ),
                    borderWidth: 2,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                indexAxis: 'y',
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: '#06b6d4',
                        borderWidth: 1,
                        padding: 12,
                        displayColors: false,
                        callbacks: {
                            label: function(context) {
                                return 'Cost: ' + context.parsed.x.toFixed(2);
                            }
                        }
                    }
                },
                scales: {
                    x: { 
                        beginAtZero: false,
                        ticks: { color: '#9ca3af' },
                        grid: { color: '#374151' }
                    },
                    y: {
                        ticks: { color: '#9ca3af' },
                        grid: { display: false }
                    }
                }
            }
        });
        
        // Execution time chart
        const timeCtx = document.getElementById('timeChart').getContext('2d');
        new Chart(timeCtx, {
            type: 'bar',
            data: {
                labels: allResults.map((r, i) => `${i+1}. ${r.method}`),
                datasets: [{
                    label: 'Execution Time (s)',
                    data: allResults.map(r => r.execution_time),
                    backgroundColor: 'rgba(139, 92, 246, 0.85)',
                    borderColor: 'rgb(124, 58, 255)',
                    borderWidth: 2,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                indexAxis: 'y',
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: '#a78bfa',
                        borderWidth: 1,
                        padding: 12,
                        displayColors: false
                    }
                },
                scales: {
                    x: { 
                        beginAtZero: true,
                        ticks: { color: '#9ca3af' },
                        grid: { color: '#374151' }
                    },
                    y: {
                        ticks: { color: '#9ca3af' },
                        grid: { display: false }
                    }
                }
            }
        });
        
        // Gap percentage chart
        const gapCtx = document.getElementById('gapChart').getContext('2d');
        new Chart(gapCtx, {
            type: 'bar',
            data: {
                labels: sortedResults.map((r, i) => `${i+1}. ${r.method}`),
                datasets: [{
                    label: 'Gap to Optimum (%)',
                    data: sortedResults.map(r => r.gap_percent || (((r.best_cost - KNOWN_OPTIMUM) / KNOWN_OPTIMUM) * 100)),
                    backgroundColor: sortedResults.map(r => {
                        const gap = r.gap_percent || (((r.best_cost - KNOWN_OPTIMUM) / KNOWN_OPTIMUM) * 100);
                        return gap < 5 ? 'rgba(16, 185, 129, 0.95)' :
                               gap < 10 ? 'rgba(245, 158, 11, 0.85)' :
                               'rgba(239, 68, 68, 0.85)';
                    }),
                    borderColor: sortedResults.map(r => {
                        const gap = r.gap_percent || (((r.best_cost - KNOWN_OPTIMUM) / KNOWN_OPTIMUM) * 100);
                        return gap < 5 ? 'rgb(5, 150, 105)' :
                               gap < 10 ? 'rgb(217, 119, 6)' :
                               'rgb(220, 38, 38)';
                    }),
                    borderWidth: 2,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                indexAxis: 'y',
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderWidth: 1,
                        padding: 12,
                        displayColors: false,
                        callbacks: {
                            label: function(context) {
                                return 'Gap: ' + context.parsed.x.toFixed(2) + '%';
                            }
                        }
                    }
                },
                scales: {
                    x: { 
                        beginAtZero: true,
                        ticks: { color: '#9ca3af' },
                        grid: { color: '#374151' }
                    },
                    y: {
                        ticks: { color: '#9ca3af' },
                        grid: { display: false }
                    }
                }
            }
        });
    """
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GA-CVRP Results Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{ box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif; }}
        
        .gradient-bg {{ background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #312e81 100%); }}
        
        .stat-card {{ 
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border: 1px solid rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
        }}
        .stat-card:hover {{ 
            transform: translateY(-8px);
            border-color: rgba(255, 255, 255, 0.2);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
        }}
        
        .chart-container {{ position: relative; height: 400px; margin-bottom: 1rem; }}
        
        .glow-effect {{ 
            filter: drop-shadow(0 0 8px rgba(6, 182, 212, 0.3));
        }}
        
        .card-container {{
            border: 1px solid rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(10px);
            background: linear-gradient(135deg, rgba(30, 27, 75, 0.8), rgba(49, 46, 129, 0.5));
            border-radius: 1rem;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .fade-in {{ animation: fadeIn 0.6s ease-out; }}
        
        table tr {{ animation: fadeIn 0.6s ease-out; }}
    </style>
</head>
<body class="gradient-bg min-h-screen text-gray-100 p-4 md:p-8">
    <div class="max-w-7xl mx-auto">
        
        <!-- Header -->
        <div class="relative overflow-hidden mb-8 fade-in">
            <div class="absolute inset-0 bg-gradient-to-r from-cyan-500/20 to-emerald-500/20 blur-3xl"></div>
            <div class="card-container p-8 md:p-10 relative">
                <div class="flex items-start justify-between">
                    <div>
                        <h1 class="text-4xl md:text-5xl font-bold mb-2 flex items-center gap-3 text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-emerald-400">
                            <span>🧬</span> Genetic Algorithm CVRP
                        </h1>
                        <p class="text-gray-400 text-lg">Optimization Results Dashboard</p>
                    </div>
                </div>
                
                <div class="mt-8 grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div class="bg-cyan-500/10 border border-cyan-500/30 rounded-lg px-4 py-3 hover:bg-cyan-500/20 transition">
                        <div class="text-xs text-cyan-400 uppercase font-semibold tracking-wider">Instance</div>
                        <div class="text-xl font-bold text-white mt-1">{results_data[0].get('instance', 'A-n32-k5')}</div>
                    </div>
                    <div class="bg-emerald-500/10 border border-emerald-500/30 rounded-lg px-4 py-3 hover:bg-emerald-500/20 transition">
                        <div class="text-xs text-emerald-400 uppercase font-semibold tracking-wider">Results</div>
                        <div class="text-xl font-bold text-white mt-1">{len(results_data)}</div>
                    </div>
                    <div class="bg-violet-500/10 border border-violet-500/30 rounded-lg px-4 py-3 hover:bg-violet-500/20 transition">
                        <div class="text-xs text-violet-400 uppercase font-semibold tracking-wider">Generations</div>
                        <div class="text-xl font-bold text-white mt-1">200</div>
                    </div>
                    <div class="bg-rose-500/10 border border-rose-500/30 rounded-lg px-4 py-3 hover:bg-rose-500/20 transition">
                        <div class="text-xs text-rose-400 uppercase font-semibold tracking-wider">Optimum</div>
                        <div class="text-xl font-bold text-white mt-1">{KNOWN_OPTIMUM}</div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- KPI Cards -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-5 mb-8 fade-in">
            <div class="stat-card bg-gradient-to-br from-emerald-500/20 to-teal-600/20 rounded-xl p-6 text-white">
                <div class="flex items-center justify-between mb-3">
                    <div class="text-2xl">🏆</div>
                    <div class="text-xs font-semibold bg-emerald-500/30 px-2 py-1 rounded-full text-emerald-300">TOP</div>
                </div>
                <div class="text-xs font-semibold mb-2 text-emerald-400 uppercase tracking-wider">Best Cost</div>
                <div class="text-3xl font-bold mb-2">{best_result.get('best_cost', 0):.2f}</div>
                <div class="text-sm text-gray-300 mb-3">{best_result.get('method', 'N/A')}</div>
                <div class="text-xs bg-emerald-500/30 px-2 py-1 rounded inline-block text-emerald-300 font-semibold">
                    Gap: {best_result.get('gap_percent', 0):.1f}%
                </div>
            </div>
            
            <div class="stat-card bg-gradient-to-br from-cyan-500/20 to-blue-600/20 rounded-xl p-6 text-white">
                <div class="flex items-center justify-between mb-3">
                    <div class="text-2xl">📊</div>
                    <div class="text-xs font-semibold bg-cyan-500/30 px-2 py-1 rounded-full text-cyan-300">AVG</div>
                </div>
                <div class="text-xs font-semibold mb-2 text-cyan-400 uppercase tracking-wider">Avg Cost</div>
                <div class="text-3xl font-bold mb-2">{avg_cost:.2f}</div>
                <div class="text-sm text-gray-300">{len(feasible_results)} feasible</div>
            </div>
            
            <div class="stat-card bg-gradient-to-br from-violet-500/20 to-purple-600/20 rounded-xl p-6 text-white">
                <div class="flex items-center justify-between mb-3">
                    <div class="text-2xl">⚡</div>
                    <div class="text-xs font-semibold bg-violet-500/30 px-2 py-1 rounded-full text-violet-300">TIME</div>
                </div>
                <div class="text-xs font-semibold mb-2 text-violet-400 uppercase tracking-wider">Avg Time</div>
                <div class="text-3xl font-bold mb-2">{avg_time:.2f}s</div>
                <div class="text-sm text-gray-300">per experiment</div>
            </div>
            
            <div class="stat-card bg-gradient-to-br from-rose-500/20 to-pink-600/20 rounded-xl p-6 text-white">
                <div class="flex items-center justify-between mb-3">
                    <div class="text-2xl">✅</div>
                    <div class="text-xs font-semibold bg-rose-500/30 px-2 py-1 rounded-full text-rose-300">VALID</div>
                </div>
                <div class="text-xs font-semibold mb-2 text-rose-400 uppercase tracking-wider">Feasible</div>
                <div class="text-3xl font-bold mb-2">{feasible_count}/{len(results_data)}</div>
                <div class="text-sm text-gray-300">solutions valid</div>
            </div>
        </div>
        
        <!-- Charts -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8 fade-in">
            <div class="card-container p-8 rounded-xl">
                <h2 class="text-2xl font-bold mb-6 text-white flex items-center gap-2">
                    <span>📊</span> Cost Comparison
                </h2>
                <div class="chart-container">
                    <canvas id="costChart"></canvas>
                </div>
            </div>
            
            <div class="card-container p-8 rounded-xl">
                <h2 class="text-2xl font-bold mb-6 text-white flex items-center gap-2">
                    <span>⚡</span> Execution Time
                </h2>
                <div class="chart-container">
                    <canvas id="timeChart"></canvas>
                </div>
            </div>
        </div>
        
        <div class="card-container p-8 rounded-xl mb-8 fade-in">
            <h2 class="text-2xl font-bold mb-6 text-white flex items-center gap-2">
                <span>🎯</span> Gap to Optimum
            </h2>
            <div class="chart-container" style="height: 400px;">
                <canvas id="gapChart"></canvas>
            </div>
        </div>
        
        <!-- Results Table -->
        <div class="card-container p-8 rounded-xl mb-8 fade-in">
            <h2 class="text-2xl font-bold mb-6 text-white flex items-center gap-2">
                <span>📋</span> Detailed Results
            </h2>
            <div class="overflow-x-auto">
                <table class="w-full text-sm">
                    <thead>
                        <tr class="border-b border-gray-700 text-gray-300">
                            <th class="text-left py-4 px-4 font-semibold">Rank</th>
                            <th class="text-left py-4 px-4 font-semibold">Method</th>
                            <th class="text-right py-4 px-4 font-semibold">Cost</th>
                            <th class="text-right py-4 px-4 font-semibold">Gap %</th>
                            <th class="text-right py-4 px-4 font-semibold">Time (s)</th>
                            <th class="text-center py-4 px-4 font-semibold">Valid</th>
                        </tr>
                    </thead>
                    <tbody id="resultsTable" class="text-gray-100">
                        <!-- Populated by JavaScript -->
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Guide -->
        <div class="card-container p-8 rounded-xl mb-8 fade-in">
            <h2 class="text-2xl font-bold mb-6 text-white">📚 Interpretation Guide</h2>
            <div class="grid md:grid-cols-3 gap-6">
                <div class="p-4 bg-cyan-500/10 border border-cyan-500/30 rounded-lg">
                    <h3 class="font-semibold text-lg mb-3 text-cyan-400">🎯 Quality Metrics</h3>
                    <ul class="space-y-2 text-sm text-gray-300">
                        <li><strong class="text-gray-100">Cost:</strong> Lower is better</li>
                        <li><strong class="text-gray-100">Gap %:</strong> &lt;5% = Excellent</li>
                        <li><strong class="text-gray-100">Valid:</strong> Meets all constraints</li>
                    </ul>
                </div>
                <div class="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-lg">
                    <h3 class="font-semibold text-lg mb-3 text-emerald-400">⚡ Performance</h3>
                    <ul class="space-y-2 text-sm text-gray-300">
                        <li><strong class="text-gray-100">Time:</strong> Speed of GA</li>
                        <li><strong class="text-gray-100">Cost:</strong> Solution quality</li>
                        <li><strong class="text-gray-100">Gap %:</strong> Distance from optimum</li>
                    </ul>
                </div>
                <div class="p-4 bg-rose-500/10 border border-rose-500/30 rounded-lg">
                    <h3 class="font-semibold text-lg mb-3 text-rose-400">🏆 Top Performer</h3>
                    <ul class="space-y-2 text-sm text-gray-300">
                        <li><strong class="text-gray-100">Method:</strong> {best_result.get('method', 'N/A')}</li>
                        <li><strong class="text-gray-100">Cost:</strong> {best_result.get('best_cost', 0):.2f}</li>
                        <li><strong class="text-gray-100">Time:</strong> {best_result.get('execution_time', 0):.2f}s</li>
                    </ul>
                </div>
            </div>
        </div>
        
        <!-- Footer -->
        <div class="text-center text-gray-500 text-sm py-6 fade-in">
            <p>Dashboard updated: <span class="text-gray-400 font-semibold">{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</span></p>
            <p class="text-xs mt-2">Genetic Algorithm Dashboard | Data from all_results.json</p>
        </div>
    </div>
    
    <script>
    {js_code}
    </script>
</body>
</html>"""
    
    return html


def load_results_from_json(json_file):
    """Load results from JSON file."""
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
            return data
    except FileNotFoundError:
        print(f"❌ File not found: {{json_file}}")
        return None
    except json.JSONDecodeError:
        print(f"❌ JSON decode error in {{json_file}}!")
        return None


def main():
    print("="*70)
    print("🎨 GA-CVRP DASHBOARD GENERATOR")
    print("="*70)
    
    # Load from all_results.json (main output file with cumulative results)
    results = load_results_from_json('all_results.json')
    
    if not results:
        print("\n❌ Could not load all_results.json")
        print("Make sure you have run main.py first")
        return
    
    # Handle single result vs list
    if isinstance(results, dict):
        results = [results]
    
    print(f"✅ Loaded {{len(results)}} result(s) from all_results.json")
    
    # Generate HTML
    print("🎨 Generating dashboard...")
    html_content = generate_dashboard_html(results)
    
    if not html_content:
        print("❌ Failed to generate dashboard")
        return
    
    # Save dashboard
    output_file = "dashboard_ag.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Dashboard saved: {{output_file}}")
    print(f"\n📖 Open {{output_file}} in your browser to view all results")
    print("="*70)


if __name__ == "__main__":
    main()
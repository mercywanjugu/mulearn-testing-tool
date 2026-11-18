import React, { useState, useRef, useEffect } from 'react';

function App() {
  const [codeFile, setCodeFile] = useState(null);
  const [testFile, setTestFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);

  const codeInputRef = useRef(null);
  const testInputRef = useRef(null);

  const fetchHistory = async () => {
    try {
      const response = await fetch("http://localhost:8000/history/");
      const data = await response.json();
      setHistory(data.runs || []);
    } catch (error) {
      console.error("Could not load SQLite history:", error);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const detectLanguage = (filename) => {
    if (!filename) return null;
    const ext = filename.split('.').pop().toLowerCase();
    if (ext === 'cpp' || ext === 'h') return '⚡ C++ (g++ Execution Mode)';
    if (ext === 'py') return '🐍 Python (unittest Execution Mode)';
    if (ext === 'java') return '☕ Java (JUnit Execution Mode)';
    return '📄 Text Document';
  };

  const resetForm = () => {
    setCodeFile(null);
    setTestFile(null);
    setResult(null);
    if (codeInputRef.current) codeInputRef.current.value = '';
    if (testInputRef.current) testInputRef.current.value = '';
  };

  const handleRunMutation = async (e) => {
    e.preventDefault();
    if (!codeFile || !testFile) {
      alert("Please upload both files first!");
      return;
    }

    setLoading(true);
    setResult(null);

    const formData = new FormData();
    formData.append("code_file", codeFile);
    formData.append("test_file", testFile);

    try {
      const response = await fetch("http://localhost:8000/run-mutation/", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      setResult(data);
      fetchHistory();
    } catch (error) {
      console.error("Error communicating with backend:", error);
      alert("Could not talk to the backend server. Make sure FastAPI is running!");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '40px', fontFamily: 'sans-serif', maxWidth: '680px', margin: '0 auto', color: '#E5E7EB' }}>
      <h1 style={{ color: '#818CF8', marginBottom: '10px' }}>🛡️ MuLearn Dashboard</h1>
      <p style={{ color: '#9CA3AF', marginBottom: '30px' }}>Test the strength of your test suites for Python, Java, and C++.</p>

      <form onSubmit={handleRunMutation} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div style={{ backgroundColor: '#1F2937', padding: '15px', borderRadius: '8px', border: '1px solid #374151' }}>
          <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '8px', color: '#F3F4F6' }}>
            Upload Source Code File (Python / Java / C++):
          </label>
          <input 
            ref={codeInputRef}
            type="file" 
            accept=".py,.java,.cpp,.h" 
            onChange={(e) => setCodeFile(e.target.files[0] || null)} 
            style={{ color: 'transparent' }}
          />
          {codeFile && (
            <div style={{ marginTop: '8px', color: '#34D399', fontSize: '14px', fontWeight: '500' }}>
              ✓ Selected: <span style={{ color: '#F3F4F6' }}>{codeFile.name}</span>
              <div style={{ color: '#818CF8', fontSize: '12px', marginTop: '4px', fontWeight: 'bold' }}>
                Detected: {detectLanguage(codeFile.name)}
              </div>
            </div>
          )}
        </div>

        <div style={{ backgroundColor: '#1F2937', padding: '15px', borderRadius: '8px', border: '1px solid #374151' }}>
          <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '8px', color: '#F3F4F6' }}>
            Upload Test Suite File:
          </label>
          <input 
            ref={testInputRef}
            type="file" 
            accept=".py,.java,.cpp" 
            onChange={(e) => setTestFile(e.target.files[0] || null)} 
            style={{ color: 'transparent' }}
          />
          {testFile && (
            <div style={{ marginTop: '8px', color: '#34D399', fontSize: '14px', fontWeight: '500' }}>
              ✓ Selected: <span style={{ color: '#F3F4F6' }}>{testFile.name}</span>
              <div style={{ color: '#818CF8', fontSize: '12px', marginTop: '4px', fontWeight: 'bold' }}>
                Detected: {detectLanguage(testFile.name)}
              </div>
            </div>
          )}
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button 
            type="submit" 
            disabled={loading}
            style={{
              flex: 3,
              padding: '12px',
              backgroundColor: loading ? '#4B5563' : '#6366F1',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              fontWeight: 'bold',
              cursor: loading ? 'not-allowed' : 'pointer',
              fontSize: '16px'
            }}
          >
            {loading ? "Running Mutation Testing Engine..." : "⚡ Run Mutation Analysis"}
          </button>

          <button 
            type="button"
            onClick={resetForm}
            style={{
              flex: 1,
              padding: '12px',
              backgroundColor: '#374151',
              color: '#D1D5DB',
              border: '1px solid #4B5563',
              borderRadius: '6px',
              fontWeight: 'bold',
              cursor: 'pointer',
              fontSize: '16px'
            }}
          >
            🔄 Reset
          </button>
        </div>
      </form>

      {result && (
        <div style={{ marginTop: '30px', padding: '20px', borderRadius: '8px', border: '1px solid #374151', backgroundColor: '#1F2937' }}>
          <h3 style={{ marginTop: 0, color: '#F3F4F6' }}>Analysis Output Summary:</h3>
          <p style={{ fontSize: '16px', color: '#D1D5DB' }}>
            <strong>Result Indicator:</strong>{' '}
            <span style={{ color: result.status === 'Success' ? '#34D399' : '#F87171', fontWeight: 'bold' }}>
              {result.result}
            </span>
          </p>
          <p style={{ fontSize: '14px', lineHeight: '1.5', color: '#9CA3AF' }}>
            <strong>Explanation Details:</strong> {result.details}
          </p>
        </div>
      )}

      {/* SQLite Database History Table */}
      <div style={{ marginTop: '40px', padding: '20px', borderRadius: '8px', border: '1px solid #374151', backgroundColor: '#111827' }}>
        <h3 style={{ marginTop: 0, color: '#818CF8', fontSize: '16px' }}>🗄️ Recent Mutation Runs (Local SQLite Database)</h3>
        {history.length === 0 ? (
          <p style={{ color: '#6B7280', fontSize: '14px' }}>No test runs recorded in SQLite yet. Run an analysis above to save your first record.</p>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #374151', color: '#9CA3AF' }}>
                <th style={{ padding: '8px 4px' }}>File</th>
                <th style={{ padding: '8px 4px' }}>Lang</th>
                <th style={{ padding: '8px 4px' }}>Outcome</th>
                <th style={{ padding: '8px 4px' }}>Score</th>
                <th style={{ padding: '8px 4px' }}>Time (s)</th>
              </tr>
            </thead>
            <tbody>
              {history.map((run) => (
                <tr key={run.Run_ID} style={{ borderBottom: '1px solid #1F2937' }}>
                  <td style={{ padding: '8px 4px', color: '#F3F4F6' }}>{run.File_Name}</td>
                  <td style={{ padding: '8px 4px', color: '#818CF8' }}>{run.Language}</td>
                  <td style={{ padding: '8px 4px', color: run.Final_Mutation_Score === 100 ? '#34D399' : '#F87171', fontWeight: 'bold' }}>
                    {run.Result_Status}
                  </td>
                  <td style={{ padding: '8px 4px' }}>{run.Final_Mutation_Score}%</td>
                  <td style={{ padding: '8px 4px', color: '#9CA3AF' }}>{run.Execution_Duration}s</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default App;



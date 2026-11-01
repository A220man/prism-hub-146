import { useState } from 'react';

interface VTableEntry {
  index: number;
  address: string;
  function_name?: string;
  signature?: string;
}

interface VTableAnalyzeResponse {
  class_name: string;
  vtable_address: string;
  resolved_entries: VTableEntry[];
  call_sites: any[];
}

function VTableAnalyzer() {
  const [className, setClassName] = useState('BaseClass');
  const [vtableAddress, setVtableAddress] = useState('0x401000');
  const [entries, setEntries] = useState<string>('0,0x401000\n1,0x401050\n2,0x4010a0');
  const [result, setResult] = useState<VTableAnalyzeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);
    try {
      const entryList = entries.trim().split('\n').map((line, i) => {
        const [idx, addr] = line.split(',').map(s => s.trim());
        return { index: parseInt(idx) || i, address: addr };
      });

      const response = await fetch('/api/vtable/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          class_name: className,
          vtable_address: vtableAddress,
          entries: entryList,
        }),
      });

      if (!response.ok) {
        throw new Error(`Analysis failed: ${response.status}`);
      }

      setResult(await response.json());
    } catch (e) {
      setError(`Error: ${e}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section style={{ marginTop: '1rem', padding: '1rem', border: '1px solid #ddd', borderRadius: '8px' }}>
      <h2>VTable Function Call Analyzer</h2>
      <p style={{ fontSize: '0.9rem', color: '#666', marginBottom: '1rem' }}>
        Enter vtable entries (index,address per line) to resolve indirect function calls
      </p>

      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
        <div>
          <label style={{ display: 'block', marginBottom: '0.25rem' }}>Class Name</label>
          <input
            type="text"
            value={className}
            onChange={(e) => setClassName(e.target.value)}
            style={{ padding: '0.5rem', width: '200px' }}
          />
        </div>
        <div>
          <label style={{ display: 'block', marginBottom: '0.25rem' }}>VTable Address</label>
          <input
            type="text"
            value={vtableAddress}
            onChange={(e) => setVtableAddress(e.target.value)}
            style={{ padding: '0.5rem', width: '200px' }}
          />
        </div>
      </div>

      <div style={{ marginBottom: '1rem' }}>
        <label style={{ display: 'block', marginBottom: '0.25rem' }}>Entries (index,address per line)</label>
        <textarea
          value={entries}
          onChange={(e) => setEntries(e.target.value)}
          rows={5}
          style={{ padding: '0.5rem', width: '100%', maxWidth: '500px', fontFamily: 'monospace' }}
        />
      </div>

      <button
        onClick={handleAnalyze}
        disabled={loading}
        style={{ padding: '0.5rem 1rem', background: '#007bff', color: 'white', border: 'none', borderRadius: '4px', cursor: loading ? 'not-allowed' : 'pointer' }}
      >
        {loading ? 'Analyzing...' : 'Analyze VTable'}
      </button>

      {error && <p style={{ color: 'red', marginTop: '1rem' }}>{error}</p>}

      {result && (
        <div style={{ marginTop: '1.5rem' }}>
          <h3>Resolved VTable: {result.class_name} @ {result.vtable_address}</h3>
          <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '0.5rem' }}>
            <thead>
              <tr style={{ background: '#f5f5f5' }}>
                <th style={{ padding: '0.5rem', border: '1px solid #ddd', textAlign: 'left' }}>Index</th>
                <th style={{ padding: '0.5rem', border: '1px solid #ddd', textAlign: 'left' }}>Address</th>
                <th style={{ padding: '0.5rem', border: '1px solid #ddd', textAlign: 'left' }}>Resolved Function</th>
                <th style={{ padding: '0.5rem', border: '1px solid #ddd', textAlign: 'left' }}>Signature</th>
              </tr>
            </thead>
            <tbody>
              {result.resolved_entries.map((entry) => (
                <tr key={entry.index}>
                  <td style={{ padding: '0.5rem', border: '1px solid #ddd' }}>{entry.index}</td>
                  <td style={{ padding: '0.5rem', border: '1px solid #ddd', fontFamily: 'monospace' }}>{entry.address}</td>
                  <td style={{ padding: '0.5rem', border: '1px solid #ddd', fontWeight: entry.function_name?.startsWith('sub_') ? 'normal' : 'bold' }}>
                    {entry.function_name || 'Unknown'}
                  </td>
                  <td style={{ padding: '0.5rem', border: '1px solid #ddd', fontFamily: 'monospace', color: '#666' }}>
                    {entry.signature || '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {result.call_sites.length > 0 && (
            <div style={{ marginTop: '1.5rem' }}>
              <h3>Call Sites (Cross-References)</h3>
              <p style={{ fontSize: '0.9rem', color: '#666' }}>
                Locations where these vtable functions are called indirectly
              </p>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '0.5rem' }}>
                  <thead>
                    <tr style={{ background: '#f5f5f5' }}>
                      <th style={{ padding: '0.5rem', border: '1px solid #ddd', textAlign: 'left' }}>Call Address</th>
                      <th style={{ padding: '0.5rem', border: '1px solid #ddd', textAlign: 'left' }}>Caller Function</th>
                      <th style={{ padding: '0.5rem', border: '1px solid #ddd', textAlign: 'left' }}>Instruction</th>
                      <th style={{ padding: '0.5rem', border: '1px solid #ddd', textAlign: 'left' }}>VTable Index</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.call_sites.map((cs, i) => (
                      <tr key={i}>
                        <td style={{ padding: '0.5rem', border: '1px solid #ddd', fontFamily: 'monospace' }}>{cs.address}</td>
                        <td style={{ padding: '0.5rem', border: '1px solid #ddd' }}>{cs.function}</td>
                        <td style={{ padding: '0.5rem', border: '1px solid #ddd', fontFamily: 'monospace' }}>{cs.instruction}</td>
                        <td style={{ padding: '0.5rem', border: '1px solid #ddd' }}>{cs.vtable_index}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </section>
  );
}

export default VTableAnalyzer;

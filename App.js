import React, { useState, useEffect, useRef, useMemo } from 'react';
import { 
  Shield, Activity, AlertTriangle, Database, Eye, Search, 
  Download, Menu, X, Home, FileText, List, Target, LogOut, 
  User, CheckCircle, XCircle, Plus, Trash2, Loader, UserPlus, Lock
} from 'lucide-react';
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer 
} from 'recharts';
import { 
  signInWithEmailAndPassword, 
  createUserWithEmailAndPassword, 
  onAuthStateChanged, 
  signOut 
} from "firebase/auth";
import { ref, set } from "firebase/database";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

// Ensure you import 'db' here
import { auth, db } from "./firebase"; 
import { fetchAuditLogs, fetchAttackLogs, fetchAttackStats, checkHealth } from './api'; // Updated import
import './App.css'; 

// ==================== DECRYPTED TEXT COMPONENT ====================
const DecryptedText = ({ text, speed = 50 }) => {
  const [displayText, setDisplayText] = useState("");
  useEffect(() => {
    const chars = "AXOYKVZ0123456789!@#$%^&*()_+";
    let iteration = 0;
    const interval = setInterval(() => {
      setDisplayText(text.split("").map((char, i) => {
        if (char === " ") return " ";
        if (i < iteration) return text[i];
        return chars[Math.floor(Math.random() * chars.length)];
      }).join(""));
      if (iteration >= text.length) clearInterval(interval);
      iteration += 1 / 3;
    }, speed);
    return () => clearInterval(interval);
  }, [text, speed]);
  return <span className="font-mono text-emerald">{displayText}</span>;
};

// ==================== ANIMATED BACKGROUND ====================
const AnimatedBackground = () => {
  const canvasRef = useRef(null);
  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    let w = window.innerWidth;
    let h = window.innerHeight;
    const resize = () => { w = window.innerWidth; h = window.innerHeight; canvas.width = w; canvas.height = h; };
    window.addEventListener('resize', resize);
    resize();
    
    const particles = Array.from({ length: 80 }, () => ({
      x: Math.random() * w, y: Math.random() * h, vx: (Math.random() - 0.5) * 0.5, vy: (Math.random() - 0.5) * 0.5
    }));
    
    const animate = () => {
      ctx.fillStyle = 'rgba(2, 6, 23, 0.1)';
      ctx.fillRect(0, 0, w, h);
      ctx.strokeStyle = 'rgba(16, 185, 129, 0.05)';
      ctx.lineWidth = 1;
      for (let x = 0; x < w; x += 60) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke(); }
      for (let y = 0; y < h; y += 60) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke(); }
      
      particles.forEach(p => {
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0 || p.x > w) p.vx *= -1;
        if (p.y < 0 || p.y > h) p.vy *= -1;
        ctx.fillStyle = 'rgba(16, 185, 129, 0.4)';
        ctx.beginPath();
        ctx.arc(p.x, p.y, 2, 0, Math.PI * 2);
        ctx.fill();
      });
      requestAnimationFrame(animate);
    };
    animate();
    return () => window.removeEventListener('resize', resize);
  }, []);
  return <canvas ref={canvasRef} className="canvas-bg" />;
};

// ==================== SPOTLIGHT CARD ====================
const SpotlightCard = ({ children, className = "", onClick, style }) => {
  const [pos, setPos] = useState({ x: 0, y: 0 });
  const handleMouseMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setPos({ x: e.clientX - rect.left, y: e.clientY - rect.top });
  };
  return (
    <div 
      className={`spotlight-card ${className}`} 
      onMouseMove={handleMouseMove}
      onClick={onClick}
      style={{
        ...style,
        '--mouse-x': `${pos.x}px`,
        '--mouse-y': `${pos.y}px`,
      }}
    >
      {children}
    </div>
  );
};

// ==================== AUTH COMPONENTS ====================
const Login = ({ onLogin }) => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [isRegister, setIsRegister] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      let userCredential;
      if (isRegister) {
        userCredential = await createUserWithEmailAndPassword(auth, email, password);
      } else {
        userCredential = await signInWithEmailAndPassword(auth, email, password);
      }
      onLogin(userCredential.user);
      toast.success(`Welcome, ${userCredential.user.email}!`, { theme: 'dark' });
    } catch (error) {
      toast.error(error.message, { theme: 'dark' });
    }
    setLoading(false);
  };

  return (
    <SpotlightCard className="auth-card">
      <h2>{isRegister ? "Register" : "Login"}</h2>
      <form onSubmit={handleSubmit}>
        <input 
          type="email" 
          placeholder="Email" 
          value={email} 
          onChange={(e) => setEmail(e.target.value)} 
          required 
        />
        <input 
          type="password" 
          placeholder="Password" 
          value={password} 
          onChange={(e) => setPassword(e.target.value)} 
          required 
        />
        <button type="submit" disabled={loading}>
          {loading ? <Loader className="animate-spin" size={16} /> : isRegister ? "Register" : "Login"}
        </button>
      </form>
      <p onClick={() => setIsRegister(!isRegister)}>
        {isRegister ? "Already have an account? Login" : "Need an account? Register"}
      </p>
    </SpotlightCard>
  );
};

// ==================== SIDEBAR ====================
const Sidebar = ({ currentPage, setCurrentPage, onLogout }) => {
  const menuItems = [
    { icon: Home, label: 'Dashboard', page: 'dashboard' },
    { icon: FileText, label: 'Audit Logs', page: 'audit' },
    { icon: AlertTriangle, label: 'Attack Monitor', page: 'attack' },
    { icon: Database, label: 'Data Integrity', page: 'integrity' },
    { icon: Target, label: 'Threat Intelligence', page: 'threat' },
  ];

  return (
    <nav className="sidebar">
      <div className="sidebar-header">
        <Shield size={24} color="#10b981" />
        <DecryptedText text="SecureSync" />
      </div>
      <ul>
        {menuItems.map((item) => (
          <li 
            key={item.page} 
            className={currentPage === item.page ? 'active' : ''} 
            onClick={() => setCurrentPage(item.page)}
          >
            <item.icon size={18} />
            {item.label}
          </li>
        ))}
      </ul>
      <div className="sidebar-footer">
        <div onClick={onLogout}>
          <LogOut size={18} />
          Logout
        </div>
      </div>
    </nav>
  );
};

// ==================== DASHBOARD PAGE ====================
const DashboardPage = () => {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await checkHealth();
        setHealth(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <div className="loading"><Loader className="animate-spin" size={40} /></div>;
  if (error) return <div className="error">Error: {error}</div>;

  return (
    <div className="page-content">
      <h1>System Dashboard</h1>
      <div className="grid grid-3">
        <SpotlightCard>
          <h3>System Health</h3>
          <p>Status: {health.status}</p>
          <p>Timestamp: {new Date(health.timestamp * 1000).toLocaleString()}</p>
        </SpotlightCard>
        {/* Add more real data cards as needed */}
      </div>
    </div>
  );
};

// ==================== AUDIT LOGS PAGE ====================
const AuditLogsPage = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await fetchAuditLogs();
        setLogs(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const filteredLogs = logs.filter(log => 
    log.plant_id.toLowerCase().includes(search.toLowerCase()) || 
    log.source_ip.includes(search)
  );

  if (loading) return <div className="loading"><Loader className="animate-spin" size={40} /></div>;
  if (error) return <div className="error">Error: {error}</div>;

  return (
    <div className="page-content">
      <h1>Audit Logs</h1>
      <div className="search-bar">
        <Search size={18} />
        <input 
          placeholder="Search by plant or IP..." 
          value={search} 
          onChange={(e) => setSearch(e.target.value)} 
        />
      </div>
      <table className="logs-table">
        <thead>
          <tr>
            <th>Plant</th>
            <th>IP</th>
            <th>Time</th>
            <th>Payload Hash</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {filteredLogs.map((log) => (
            <tr key={log.payload_hash}>
              <td>{log.plant_id}</td>
              <td className="font-mono">{log.source_ip}</td>
              <td>{new Date(log.created_at).toLocaleString()}</td>
              <td className="font-mono truncate">{log.payload_hash}</td>
              <td><CheckCircle color="#10b981" size={16} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// ==================== ATTACK MONITOR PAGE ====================
const AttackMonitorPage = () => {
  const [events, setEvents] = useState([]);
  const [stats, setStats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [logsData, statsData] = await Promise.all([fetchAttackLogs(), fetchAttackStats()]);
        setEvents(logsData);
        setStats(statsData);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <div className="loading"><Loader className="animate-spin" size={40} /></div>;
  if (error) return <div className="error">Error: {error}</div>;

  return (
    <div className="page-content">
      <h1>Attack Monitor</h1>
      <div className="grid grid-2">
        <SpotlightCard style={{ gridColumn: '1 / -1' }}>
          <h2>Attack Trends</h2>
          <div style={{ height: '300px' }}>
            <ResponsiveContainer>
              <AreaChart data={stats}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Area type="monotone" dataKey="count" stroke="#f43f5e" fill="#f43f5e" fillOpacity={0.3} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </SpotlightCard>
        
        <SpotlightCard>
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '10px' }}><Activity color="#f43f5e" size={20} /> Live Threat Feed</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem', maxHeight: '500px', overflowY: 'auto' }}>
            {events.map((e) => (
              <div key={e.id} style={{ padding: '1rem', background: 'rgba(2,6,23,0.5)', border: '1px solid var(--border-color)', borderRadius: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                  <div className="bg-rose" style={{ padding: '8px', borderRadius: '6px' }}><AlertTriangle size={18} color="#f43f5e"/></div>
                  <div><p style={{ fontWeight: 500 }}>{e.attack_type}</p><p className="font-mono text-rose" style={{ fontSize: '0.8rem' }}>{e.source_ip}</p></div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <span style={{ fontSize: '0.75rem', padding: '4px 8px', borderRadius: '4px', background: '#334155', color: 'white', fontWeight: 'bold' }}>{e.reason}</span>
                  <p className="text-muted" style={{ fontSize: '0.75rem', marginTop: '4px' }}>{new Date(e.created_at).toLocaleTimeString()}</p>
                </div>
              </div>
            ))}
          </div>
       </SpotlightCard>
       
       <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <SpotlightCard style={{ padding: '1.5rem', background: 'linear-gradient(to bottom, rgba(136, 19, 55, 0.2), rgba(15, 23, 42, 0.8))', borderColor: 'rgba(244, 63, 94, 0.3)' }}>
            <h3 style={{ marginBottom: '1rem' }}>System Status</h3>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '1rem' }}>
               <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#f43f5e', boxShadow: '0 0 10px #f43f5e' }}></div>
               <span className="font-mono text-rose" style={{ fontWeight: 'bold' }}>THREAT DETECTED</span>
            </div>
            <p className="text-muted" style={{ fontSize: '0.9rem' }}>Automated defense protocols active. {events.length} attacks logged recently.</p>
          </SpotlightCard>
          
          <SpotlightCard style={{ padding: '1.5rem' }}>
             <h3 style={{ marginBottom: '1rem' }}>Attack Distribution</h3>
             <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
               {/* Calculate distribution from real data */}
               {[
                 { label: 'RATE_LIMIT', val: events.filter(e => e.attack_type === 'RATE_LIMIT').length / events.length * 100 || 0, col: '#f43f5e' },
                 { label: 'REPLAY_ATTACK', val: events.filter(e => e.attack_type === 'REPLAY_ATTACK').length / events.length * 100 || 0, col: '#f97316' },
                 { label: 'Other', val: events.filter(e => !['RATE_LIMIT', 'REPLAY_ATTACK'].includes(e.attack_type)).length / events.length * 100 || 0, col: '#eab308' }
               ].map(x => (
                 <div key={x.label}>
                   <div className="flex-between" style={{ marginBottom: '5px', fontSize: '0.8rem', color: '#94a3b8' }}><span>{x.label}</span><span>{Math.round(x.val)}%</span></div>
                   <div style={{ width: '100%', height: '8px', background: '#1e293b', borderRadius: '4px' }}>
                     <div style={{ width: `${x.val}%`, height: '100%', background: x.col, borderRadius: '4px' }}></div>
                   </div>
                 </div>
               ))}
             </div>
          </SpotlightCard>
       </div>
    </div>
  );
};

// ==================== OTHER PAGES (placeholders, add fetches if needed) ====================
const DataIntegrityPage = () => <div>Data Integrity Page (Implement real data)</div>;
const ThreatIntelligencePage = () => <div>Threat Intelligence Page (Implement real data)</div>;

// ==================== MAIN APP ====================
const App = () => {
  const [user, setUser] = useState(null);
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(true);

  useEffect(() => {
    const unsubscribe = onAuth
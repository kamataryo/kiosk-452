// import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ConsoleMode } from './pages/ConsoleMode';
import { MandanMode } from './pages/MandanMode';
import './App.css';

function App() {
  return (
    <Router>
      <Routes>
        {/* メインページ: Smart Roadster コンソールモード */}
        <Route path="/" element={<ConsoleMode />} />

        {/* 漫談モード */}
        <Route path="/mandan" element={<MandanMode />} />

        {/* 未知のパスは / にリダイレクト */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

export default App;

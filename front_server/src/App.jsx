import { BrowserRouter, Routes, Route } from 'react-router-dom';
import ChatRoom from './pages/ChatRoom';
import RoomSelector from './pages/RoomSelector';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage'; 

function App() {
  return (
    <BrowserRouter>
      <Routes>

        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        <Route path="/rooms" element={<RoomSelector />} />
        <Route path="/chat/:roomId" element={<ChatRoom />} />

        <Route path="/" element={<LoginPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
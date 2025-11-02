import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { io } from 'socket.io-client'; // Voltamos a usar 'io'
import axios from 'axios';
import './RoomSelector.css';

const RENDER_URL = 'https://makeastory-backend.onrender.com';
const LOBBY_URL = RENDER_URL;

function RoomSelector() {
    const [rooms, setRooms] = useState([]);
    const [error, setError] = useState('');
    const navigate = useNavigate();

    // Busca as salas via Socket.IO
    useEffect(() => {
        const socket = io(LOBBY_URL);

        // Ouve o evento 'rooms_info'
        //
        socket.on('rooms_info', (data) => {
            console.log('Salas recebidas do socket:', data.rooms);
            setRooms(data.rooms || []);
        });

        socket.on('connect_error', () => {
            setError('Não foi possível conectar ao servidor do lobby.');
        });

        return () => {
            socket.disconnect();
        };
    }, []);

    // Função para criar sala (continua usando API REST, está correto)
    const handleCreateRoom = async () => {
        setError('');
        const token = localStorage.getItem('token');

        if (!token) {
            setError('Você precisa estar logado para criar uma sala.');
            navigate('/login');
            return;
        }

        try {
            // A API REST para criar salas ainda é válida
            const response = await axios.post(
                `${RENDER_URL}/api/rooms`,
                {},
                { headers: { 'Authorization': `Bearer ${token}` } }
            );

            // Navega para a sala recém-criada
            const newRoomId = response.data.room.id; // O back-end REST/routes.py envia o ID
            navigate(`/chat/${newRoomId}`);

        } catch (err) {
            console.error("Erro ao criar sala:", err);

            if (err.response && err.response.data && err.response.data.msg) {
                // Usa a mensagem de erro específica do backend
                setError(err.response.data.msg);
            } else {
                setError('Erro ao tentar criar a sala.');
            }
        }
    };

    return (
        <div className="room-selector-container">
            <div className="room-selector-box">
                <h2>Lobby Principal</h2>
                {error && <p style={{ color: '#ff3b30', textAlign: 'center' }}>{error}</p>}

                <button className="create-room-btn" onClick={handleCreateRoom}>
                    Criar Sala
                </button>

                <hr style={{ borderColor: '#ff00ff', opacity: 0.3, margin: '1.5rem 0' }} />

                <ul className="room-list">
                    {rooms.length === 0 && <p style={{ textAlign: 'center' }}>Nenhuma sala aberta...</p>}

                    {rooms.map(sala => (
                        <li key={sala.room_id} className="room-list-item">
                            <Link
                                to={`/chat/${sala.room_id}`}
                                className={sala.status === 'IN_PROGRESS' ? 'in-progress' : ''}
                                onClick={(e) => {
                                    if (sala.status === 'IN_PROGRESS') {
                                        e.preventDefault();
                                        setError(`A sala '${sala.room_name}' já está em jogo.`);
                                    } else {
                                        setError('');
                                    }
                                }}
                            >
                                {sala.room_name}
                                <span style={{ float: 'right' }}>
                                    {sala.status === 'IN_PROGRESS' ? 'Em Jogo' : `(${sala.members} / 5)`}
                                </span>
                            </Link>
                        </li>
                    ))}
                </ul>

                <div className="auth-link-box">
                    <Link to="/login">Voltar ao Login</Link>
                </div>
            </div>
        </div>
    );
}

export default RoomSelector;
// src/pages/RoomSelector.jsx
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { io } from 'socket.io-client';

// CONECTA AO NAMESPACE DO LOBBY (/)
const LOBBY_URL = 'http://localhost:5000'; //

function RoomSelector() {
    const [rooms, setRooms] = useState([]);

    useEffect(() => {
        // Conecta ao socket do lobby
        const socket = io(LOBBY_URL);

        // Ouve o evento 'rooms_info' que o back-end envia
        socket.on('rooms_info', (data) => {
            console.log('Salas recebidas:', data.rooms);
            setRooms(data.rooms || []);
        });

        // Desconecta quando o componente for desmontado
        return () => {
            socket.disconnect();
        };
    }, []); // Roda apenas uma vez, quando o componente montar

    return (
        <div style={{ padding: '20px' }}>
            <h2>Escolha uma Sala</h2>

            <ul style={{ listStyle: 'none', padding: 0 }}>
                {rooms.length === 0 && <p>Carregando salas...</p>}

                {rooms.map(sala => (
                    <li key={sala.room_id} style={{ margin: '10px 0' }}>
                        {/* O Link do react-router-dom vai para a rota /chat/:roomId
                          que definimos no App.jsx. 
                        */}
                        <Link
                            to={`/chat/${sala.room_id}`}
                            style={{ fontSize: '1.2em', textDecoration: 'none' }}
                        >
                            {sala.room_name} ({sala.members} membros)
                        </Link>
                    </li>
                ))}
            </ul>
        </div>
    );
}

export default RoomSelector;
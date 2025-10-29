import React, { useState, useEffect, useRef } from 'react';
import { io } from 'socket.io-client';
import { useParams, Link } from 'react-router-dom';

// CONECTA AO NAMESPACE DE SALA (/r)
const ROOM_URL = 'http://localhost:5000/r';

function ChatRoom() {
    const { roomId } = useParams();
    const [socket, setSocket] = useState(null);
    const [status, setStatus] = useState('Connecting...');
    const [messages, setMessages] = useState([]);
    const [myMessage, setMyMessage] = useState('');
    const chatEndRef = useRef(null); // Para rolar o chat para baixo

    // Efeito para rolar o chat
    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    useEffect(() => {
        const newSocket = io(ROOM_URL); //

        // 1. Evento de conexão
        newSocket.on('connect', () => {
            // 2. EMITIR 'join_room' com callback (ACK)
            newSocket.emit('join_room', { room_id: parseInt(roomId) }, (ack) => {
                // O back-end (room.py) precisa ser ATUALIZADO para enviar esse ack
                if (ack && ack.status === 'ok') {
                    setStatus(`✔ Joined room ${ack.room_id}`);
                } else {
                    // Fallback se o ack não vier como esperado
                    setStatus(ack ? `❌ ${ack.msg}` : 'Joined (no ack)');
                }
            });
        });

        // 3. OUVIR 'connect_confirm' (do room.py) ou 'connect_ack' (do room.html)
        // O código do seu colega está inconsistente. 'room.py' envia 'connect_confirm'
        // 'room.html' ouve 'connect_ack'. Vou ouvir os dois.
        newSocket.on('connect_confirm', (data) => {
            setStatus(`✔ Connected as ${data.sid}`);
        });
        newSocket.on('connect_ack', () => {
            setStatus(`✔ Connection established`);
        });

        newSocket.on('snippet_broadcast', (data) => {
            // Esperando data = { snippets: [...] } como no room.html
            if (data && data.snippets) {
                const newMsgs = data.snippets.map(item => ({
                    type: 'snippet',
                    text: item.snippet,
                    sender: item.sender.slice(0, 5) //
                }));
                setMessages((prev) => [...prev, ...newMsgs]);
            } else {
                // Fallback se o back-end ainda estiver enviando o formato antigo
                console.warn('Recebido formato antigo de snippet_broadcast', data);
            }
        });

        newSocket.on('game_started', (data) => {
            const msg = {
                type: 'system',
                text: `Game started by ${data.triggerer}`
            };
            setMessages((prev) => [...prev, msg]);
        });

        newSocket.on('round_started', (data) => {
            const msg = {
                type: 'system',
                text: `Round started by ${data.triggerer}`
            };
            setMessages((prev) => [...prev, msg]);
        });

        newSocket.on('ai_response', (data) => {
            const msg = { type: 'ai_response', ...data };
            setMessages((prev) => [...prev, msg]);
        });

        newSocket.on('connect_error', (err) => {
            setStatus(`Connection Error: ${err.message}`);
        });

        setSocket(newSocket);

        return () => newSocket.disconnect();
    }, [roomId]);

    const handleSendMessage = (e) => {
        e.preventDefault();
        if (socket && myMessage) {
            socket.emit('story_snippet', { snippet: myMessage, room: roomId }, (ack) => {
                const msg = {
                    type: 'snippet',
                    text: myMessage
                };
                setMessages((prev) => [...prev, msg]);
                if (ack && ack.status === 'ok') {
                    setMyMessage('');
                } else {
                    // Mostra erro se o servidor negar
                    const msg = { type: 'system', text: `${ack.msg}` };
                    setMessages((prev) => [...prev, msg]);
                }
            });
        }
    };

    const handleStartGame = () => {
        if (socket) {
            socket.emit('start_game', (ack) => {
                if (ack && ack.status === 'error') {
                    const msg = { type: 'system', text: `${ack.msg}` }; //
                    setMessages((prev) => [...prev, msg]);
                }
            });
        }
    };

    // Função de ajuda para renderizar diferentes tipos de msg
    const renderMessage = (msg, index) => {
        if (msg.type === 'ai_response') {
            return (
                <div key={index} className="ai-message">
                    <p>{msg.story}</p>
                    <img src={msg.image_url} alt="História gerada" />
                    <a href={msg.song_url} target="_blank" rel="noopener noreferrer">Ouvir música</a>
                </div>
            );
        }
        if (msg.type === 'system') {
            return <div key={index} className="system-message"><b>{msg.text}</b></div>;
        }
        // (msg.type === 'snippet')
        return (
            <div key={index} className="user-message">
                <strong>{msg.sender || 'User'}:</strong> {msg.text}
            </div>
        );
    };

    return (
        <div style={{ padding: '20px' }}>
            <Link to="/rooms">{"< Voltar para Salas"}</Link>
            <h2 style={{ marginTop: '20px' }}>Sala: {roomId}</h2>
            <div className="status-bar">{status}</div>
            <div className="message-list" style={{ border: '1px solid #ccc', height: '300px', overflowY: 'auto', padding: '10px' }}>
                {messages.map(renderMessage)}
                <div ref={chatEndRef} />
            </div>
            <button onClick={handleStartGame} style={{ marginTop: '10px', background: 'lightblue' }}>
                Gerar História (IA)
            </button>
            <form onSubmit={handleSendMessage} style={{ marginTop: '10px' }}>
                <input
                    type="text"
                    value={myMessage}
                    onChange={(e) => setMyMessage(e.target.value)}
                    placeholder="Digite sua parte da história..."
                    style={{ width: '80%' }}
                />
                <button type="submit">Enviar</button>
            </form>
        </div>
    );
}

export default ChatRoom;
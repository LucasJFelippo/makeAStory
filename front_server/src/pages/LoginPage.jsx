import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import './AuthForm.css';

const RENDER_URL = 'https://makeastory-backend.onrender.com';
const LOGIN_URL = `${RENDER_URL}/auth/login`;
const GUEST_LOGIN_URL = `${RENDER_URL}/auth/guest_login`;

function LoginPage() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleLogin = async (e) => {
        e.preventDefault();
        setError(''); // Limpa erros antigos

        try {
            const response = await axios.post(LOGIN_URL, {
                username: username,
                password: password
            });

            // Login com sucesso
            const token = response.data.access_token;
            localStorage.setItem('token', token); // Salva o token no storage

            // Redireciona para o seletor de salas
            navigate('/rooms');

        } catch (err) {
            if (err.response) {
                // Erro do servidor (ex: "Usuário ou senha inválidos")
                setError(err.response.data.msg);
            } else {
                // Erro de rede
                setError('Não foi possível conectar ao servidor.');
            }
        }
    };

    const handleGuestLogin = async () => {
        setError('');
        if (!username) {
            setError('O nome de usuário é obrigatório para entrar como convidado.');
            return;
        }

        try {
            //
            const response = await axios.post(GUEST_LOGIN_URL, {
                username: username
            });

            // Login de convidado com sucesso
            const token = response.data.access_token;
            localStorage.setItem('token', token); // Salva o token

            navigate('/rooms'); // Redireciona para as salas

        } catch (err) {
            if (err.response) {
                setError(err.response.data.msg);
            } else {
                setError('Não foi possível conectar ao servidor.');
            }
        }
    };

    return (
        <div className="auth-container">
            <form className="auth-form" onSubmit={handleLogin}>
                <h2>Login</h2>
                {error && <p className="auth-error">{error}</p>}

                <div className="auth-form-group">
                    <label htmlFor="username">Usuário</label>
                    <input
                        type="text"
                        id="username"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        required
                    />
                </div>

                <div className="auth-form-group">
                    <label htmlFor="password">Senha</label>
                    <input
                        type="password"
                        id="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                    // required
                    />
                </div>

                <button type="submit">Entrar</button>

                <div className="auth-separator">OU</div>

                <button
                    type="button" // Importante: 'type="button"' impede o envio do formulário
                    className="guest-btn"
                    onClick={handleGuestLogin}
                >
                    Entrar como Convidado
                </button>

                <div className="auth-form-link">
                    <p>Não tem uma conta? <Link to="/register">Registre-se</Link></p>
                </div>
            </form>
        </div>
    );
}

export default LoginPage;
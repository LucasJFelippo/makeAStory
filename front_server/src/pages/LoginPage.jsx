import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import './AuthForm.css';

// URLs do servidor (Render) para autenticação
const RENDER_URL = 'https://makeastory-backend.onrender.com';
const LOGIN_URL = `${RENDER_URL}/auth/login`;
const GUEST_LOGIN_URL = `${RENDER_URL}/auth/guest_login`;

function LoginPage() {
    // Estados para guardar o que o usuário digita
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const navigate = useNavigate(); // Hook para redirecionar a página

    // Função para o login normal (com usuário e senha)
    const handleLogin = async (e) => {
        e.preventDefault(); // Impede o refresh da página
        setError('');

        try {
            // Chama a API de login
            const response = await axios.post(LOGIN_URL, {
                username: username,
                password: password
            });

            // Se der certo, pega o token...
            const token = response.data.access_token;
            localStorage.setItem('token', token);
            navigate('/rooms');

        } catch (err) {
            // Se der errado, mostra o erro
            if (err.response) {
                setError(err.response.data.msg);
            } else {
                setError('Não foi possível conectar ao servidor.');
            }
        }
    };

    // Função para o login de convidado (só com username)
    const handleGuestLogin = async () => {
        setError('');
        if (!username) {
            setError('O nome de usuário é obrigatório para entrar como convidado.');
            return;
        }

        try {
            // Chama a API de login de convidado
            const response = await axios.post(GUEST_LOGIN_URL, {
                username: username
            });

            // Se der certo, pega o token
            const token = response.data.access_token;
            localStorage.setItem('token', token);

            navigate('/rooms');

        } catch (err) {
            // Se der errado, mostra o erro
            if (err.response) {
                setError(err.response.data.msg);
            } else {
                setError('Não foi possível conectar ao servidor.');
            }
        }
    };

    // Estrutura visual da página (HTML/JSX)
    return (
        <div className="auth-container">
            <form className="auth-form" onSubmit={handleLogin}>
                <h2>Login</h2>
                {error && <p className="auth-error">{error}</p>}

                {/* Input de Usuário */}
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

                {/* Input de Senha */}
                <div className="auth-form-group">
                    <label htmlFor="password">Senha</label>
                    <input
                        type="password"
                        id="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                    />
                </div>

                {/* Botão de Login Normal */}
                <button type="submit">Entrar</button>

                <div className="auth-separator">OU</div>

                {/* Botão de Login Convidado */}
                <button
                    type="button"
                    className="guest-btn"
                    onClick={handleGuestLogin}
                >
                    Entrar como Convidado
                </button>

                {/* Link para a página de Registro */}
                <div className="auth-form-link">
                    <p>Não tem uma conta? <Link to="/register">Registre-se</Link></p>
                </div>
            </form>
        </div>
    );
}

export default LoginPage;
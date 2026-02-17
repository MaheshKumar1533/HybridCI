// Frontend API client
import axios from 'axios';

const API_BASE = '/api';

export async function fetchUsers() {
    return axios.get('/api/users');
}

export async function getUser(id) {
    return fetch(`/api/users/${id}`);
}

export async function createUser(data) {
    return axios.post('/api/users', data);
}

export async function login(username, password) {
    return axios.post('/api/auth/login', { username, password });
}

export async function getCalculation(a, b) {
    return fetch('/api/calculate');
}

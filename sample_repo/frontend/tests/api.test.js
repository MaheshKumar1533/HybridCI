// Frontend tests for API
import { fetchUsers, login, getCalculation } from '../api';

describe('API Client', () => {
    test('fetchUsers should call /api/users', async () => {
        const users = await fetchUsers();
        expect(users).toBeDefined();
    });

    test('login should call /api/auth/login', async () => {
        const result = await login('admin', 'password');
        expect(result).toBeDefined();
    });

    test('getCalculation should call /api/calculate', async () => {
        const result = await getCalculation(1, 2);
        expect(result).toBeDefined();
    });
});

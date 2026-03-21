import { Order, User } from '@/types/user.types';
import ordersData from '@/lib/mock-api/user-orders.json';

const delay = (ms: number = 500) => new Promise(resolve => setTimeout(resolve, ms));

export const userService = {
  async getOrders(): Promise<Order[]> {
    await delay();
    return ordersData as Order[];
  },

  async getCurrentUser(): Promise<User> {
    await delay();
    return {
      id: 'user-1',
      email: 'parent@example.com',
      name: 'Sarah Johnson',
      avatar: 'https://images.pexels.com/photos/774909/pexels-photo-774909.jpeg?auto=compress&cs=tinysrgb&w=200'
    };
  },
};

export interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
}

export interface Order {
  id: string;
  bookId: string;
  bookTitle: string;
  bookCover: string;
  orderDate: string;
  format: 'digital' | 'softcover' | 'hardcover';
  price: number;
  status: 'processing' | 'completed' | 'shipped';
  downloadUrl?: string;
}

export interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
}

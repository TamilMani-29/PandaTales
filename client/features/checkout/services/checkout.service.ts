import apiClient from '@/lib/api/axios';
import { ENDPOINTS } from '@/lib/api/endpoints';

export interface CheckoutRequest {
  bookId: string;
  format: 'digital' | 'softcover' | 'hardcover';
}

export interface RazorpayOrderResponse {
  order_id: string;          // our internal UUID
  razorpay_order_id: string; // e.g. "order_ABC123"
  amount: number;            // paise
  currency: string;
  key_id: string;
}

export interface VerifyPaymentRequest {
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
}

export interface OrderRecord {
  id: string;
  book_id: string;
  format: string;
  amount: number;
  currency: string;
  razorpay_order_id: string;
  razorpay_payment_id: string | null;
  status: 'created' | 'paid' | 'failed';
  paid_at: string | null;
  created_at: string;
}

export const checkoutService = {
  async createOrder(request: CheckoutRequest): Promise<RazorpayOrderResponse> {
    const { data } = await apiClient.post(ENDPOINTS.checkout.createOrder, {
      book_id: request.bookId,
      format: request.format,
    });
    return data.data as RazorpayOrderResponse;
  },

  async verifyPayment(payload: VerifyPaymentRequest): Promise<OrderRecord> {
    const { data } = await apiClient.post(ENDPOINTS.checkout.verifyPayment, payload);
    return data.data as OrderRecord;
  },

  async listOrders(): Promise<OrderRecord[]> {
    const { data } = await apiClient.get(ENDPOINTS.checkout.orders);
    return data.data as OrderRecord[];
  },
};

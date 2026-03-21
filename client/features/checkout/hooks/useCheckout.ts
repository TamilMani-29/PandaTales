import { useMutation, useQuery } from '@tanstack/react-query';
import {
  checkoutService,
  CheckoutRequest,
  VerifyPaymentRequest,
} from '../services/checkout.service';

export const useCreateOrder = () => {
  return useMutation({
    mutationFn: (request: CheckoutRequest) => checkoutService.createOrder(request),
  });
};

export const useVerifyPayment = () => {
  return useMutation({
    mutationFn: (payload: VerifyPaymentRequest) => checkoutService.verifyPayment(payload),
  });
};

export const useOrders = () => {
  return useQuery({
    queryKey: ['orders'],
    queryFn: () => checkoutService.listOrders(),
  });
};

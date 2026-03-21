import { useQuery } from '@tanstack/react-query';
import { userService } from '../services/user.service';

export const useOrders = () => {
  return useQuery({
    queryKey: ['orders'],
    queryFn: userService.getOrders,
  });
};

export const useCurrentUser = () => {
  return useQuery({
    queryKey: ['currentUser'],
    queryFn: userService.getCurrentUser,
  });
};

'use client';

import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useOrders } from '@/features/user/hooks/useUser';
// AUTH: import { useAuth } from '@/lib/providers/auth-provider';
import { Loader as Loader2, Download, Package, CircleCheck as CheckCircle, Clock } from 'lucide-react';
import Image from 'next/image';
import Link from 'next/link';
// AUTH: import { useRouter } from 'next/navigation';
// AUTH: import { useEffect } from 'react';
import { motion } from 'framer-motion';
import { format } from 'date-fns';

export default function DashboardPage() {
  // AUTH: const { isAuthenticated, isLoading: authLoading } = useAuth();
  const { data: orders, isLoading: ordersLoading } = useOrders();
  // AUTH: const router = useRouter();

  // AUTH: useEffect(() => {
  // AUTH:   if (!authLoading && !isAuthenticated) {
  // AUTH:     router.push('/login');
  // AUTH:   }
  // AUTH: }, [isAuthenticated, authLoading, router]);

  if (ordersLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'shipped':
        return <Package className="h-5 w-5 text-blue-500" />;
      case 'processing':
        return <Clock className="h-5 w-5 text-orange-500" />;
      default:
        return null;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'shipped':
        return 'bg-blue-100 text-blue-800';
      case 'processing':
        return 'bg-orange-100 text-orange-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="min-h-screen relative">
      <main className="relative z-10 container mx-auto px-4 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2 }}
        >
          <h1 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-[#6B21A8] to-[#C9A227] bg-clip-text text-transparent">
            My Books
          </h1>
          <p className="text-lg text-muted-foreground mb-8">
            View and manage your personalized book collection
          </p>

          {!orders || orders.length === 0 ? (
            <Card className="rounded-3xl shadow-lg p-12 text-center">
              <div className="max-w-md mx-auto">
                <Package className="h-16 w-16 mx-auto mb-4 text-muted-foreground" />
                <h2 className="text-2xl font-bold mb-2">No Books Yet</h2>
                <p className="text-muted-foreground mb-6">
                  You haven't created any personalized books yet. Start creating magical
                  stories today!
                </p>
                <Link href="/coloring-books">
                  <Button size="lg" className="rounded-2xl">
                    Browse Books
                  </Button>
                </Link>
              </div>
            </Card>
          ) : (
            <div className="space-y-6">
              {orders.map((order, index) => (
                <motion.div
                  key={order.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <Card className="rounded-3xl shadow-lg overflow-hidden hover:shadow-xl transition">
                    <CardContent className="p-6">
                      <div className="flex flex-col md:flex-row gap-6">
                        <div className="relative w-full md:w-48 aspect-[3/4] flex-shrink-0 rounded-2xl overflow-hidden">
                          <Image
                            src={order.bookCover}
                            alt={order.bookTitle}
                            fill
                            className="object-cover"
                          />
                        </div>

                        <div className="flex-1 flex flex-col justify-between">
                          <div>
                            <div className="flex items-start justify-between mb-2">
                              <h3 className="text-2xl font-bold">{order.bookTitle}</h3>
                              <Badge className={getStatusColor(order.status)}>
                                <span className="flex items-center gap-1">
                                  {getStatusIcon(order.status)}
                                  {order.status}
                                </span>
                              </Badge>
                            </div>
                            <p className="text-sm text-muted-foreground mb-4">
                              Ordered on {format(new Date(order.orderDate), 'MMMM d, yyyy')}
                            </p>
                            <div className="flex gap-4 text-sm">
                              <div>
                                <span className="text-muted-foreground">Format:</span>
                                <span className="ml-2 font-medium capitalize">
                                  {order.format}
                                </span>
                              </div>
                              <div>
                                <span className="text-muted-foreground">Price:</span>
                                <span className="ml-2 font-medium">
                                  ₹{order.price}
                                </span>
                              </div>
                            </div>
                          </div>

                          <div className="flex gap-3 mt-6">
                            {order.downloadUrl && order.status === 'completed' && (
                              <Button className="rounded-xl" asChild>
                                <a href={order.downloadUrl} download>
                                  <Download className="mr-2 h-4 w-4" />
                                  Download
                                </a>
                              </Button>
                            )}
                            {order.format !== 'digital' && (
                              <Button variant="outline" className="rounded-xl" asChild>
                                <Link href={`/checkout/${order.bookId}`}>
                                  Reorder Print
                                </Link>
                              </Button>
                            )}
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>
          )}
        </motion.div>
      </main>
    </div>
  );
}

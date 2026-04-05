import Link from 'next/link';
import { Footer } from '@/components/layout/footer';

export const metadata = {
  title: 'Privacy Policy — Pandora Pages',
  description: 'How Pandora Pages collects, uses and protects your personal information.',
};

export default function PrivacyPage() {
  return (
    <div className="min-h-screen flex flex-col">
      <main className="flex-1 container mx-auto px-4 py-12 max-w-3xl">
        <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-[#6B21A8] to-[#C9A227] bg-clip-text text-transparent">
          Privacy Policy
        </h1>
        <p className="text-sm text-muted-foreground mb-10">Last updated: March 21, 2026</p>

        <div className="prose prose-slate max-w-none space-y-8 text-foreground">

          <section>
            <h2 className="text-xl font-bold mb-3">1. Who We Are</h2>
            <p className="text-muted-foreground leading-relaxed">
              Pandora Pages (&ldquo;we&rdquo;, &ldquo;our&rdquo;, &ldquo;us&rdquo;) creates personalised story and
              coloring books for children. Our website is{' '}
              <span className="font-medium text-foreground">pandorapages.in</span>. This Privacy Policy explains what
              personal information we collect, how we use it, and the rights you have over your data.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold mb-3">2. Information We Collect</h2>
            <ul className="list-disc pl-5 space-y-2 text-muted-foreground">
              <li>
                <span className="font-medium text-foreground">Account information</span> — your name and email address
                when you create an account or sign in.
              </li>
              <li>
                <span className="font-medium text-foreground">Child details</span> — your child&apos;s first name, age
                and gender, provided by you solely to personalise the book. We do not collect any information directly
                from children.
              </li>
              <li>
                <span className="font-medium text-foreground">Photos</span> — images you upload to personalise your
                book. These are used only for generation and are not shared with third parties.
              </li>
              <li>
                <span className="font-medium text-foreground">Parent / guardian email</span> — used to deliver your
                digital PDF and send order-related communications.
              </li>
              <li>
                <span className="font-medium text-foreground">WhatsApp number</span> — optional; collected only when
                you choose a print copy so we can coordinate delivery.
              </li>
              <li>
                <span className="font-medium text-foreground">Payment information</span> — processed securely by
                Razorpay. We do not store card numbers or CVV details.
              </li>
              <li>
                <span className="font-medium text-foreground">Usage data</span> — pages visited, browser type and
                device, collected via server logs to improve our service.
              </li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-bold mb-3">3. How We Use Your Information</h2>
            <ul className="list-disc pl-5 space-y-2 text-muted-foreground">
              <li>To generate and deliver your personalised book (PDF or print).</li>
              <li>To process payments and issue receipts.</li>
              <li>To communicate order status, shipping updates and support responses.</li>
              <li>To improve and secure our platform.</li>
              <li>
                To send occasional product updates or offers — you can unsubscribe at any time via the link in our
                emails.
              </li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-bold mb-3">4. Photos and Children&apos;s Data</h2>
            <p className="text-muted-foreground leading-relaxed">
              Photos you upload are used exclusively to generate your book. They are stored on our secure servers
              (hosted in India) during the generation process and for a reasonable period thereafter so you can
              re-access your order. We will never share, sell, or use your child&apos;s photos or personal details for
              advertising or any purpose beyond fulfilling your order.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold mb-3">5. Sharing Your Information</h2>
            <p className="text-muted-foreground leading-relaxed">
              We do not sell your personal data. We share information only with:
            </p>
            <ul className="list-disc pl-5 space-y-2 text-muted-foreground mt-2">
              <li>
                <span className="font-medium text-foreground">Razorpay</span> — to process payments securely.
              </li>
              <li>
                <span className="font-medium text-foreground">Print and courier partners</span> — your name and
                shipping address if you order a physical copy.
              </li>
              <li>
                <span className="font-medium text-foreground">Cloud infrastructure providers</span> — who host our
                servers under strict data-processing agreements.
              </li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-bold mb-3">6. Data Retention</h2>
            <p className="text-muted-foreground leading-relaxed">
              We retain your account data and order records for as long as your account is active or as required by
              law. Uploaded photos are retained for 90 days after your order is completed, after which they are
              permanently deleted.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold mb-3">7. Your Rights</h2>
            <p className="text-muted-foreground leading-relaxed">
              Under applicable law (including India&apos;s Digital Personal Data Protection Act, 2023) you have the
              right to:
            </p>
            <ul className="list-disc pl-5 space-y-2 text-muted-foreground mt-2">
              <li>Access the personal data we hold about you.</li>
              <li>Request correction of inaccurate data.</li>
              <li>Request deletion of your data (subject to legal obligations).</li>
              <li>Withdraw consent at any time where processing is based on consent.</li>
            </ul>
            <p className="text-muted-foreground leading-relaxed mt-3">
              To exercise any of these rights, email us at{' '}
              <a href="mailto:info.pandorapages@gmail.com" className="text-[#6B21A8] underline">
                info.pandorapages@gmail.com
              </a>
              .
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold mb-3">8. Cookies</h2>
            <p className="text-muted-foreground leading-relaxed">
              We use only essential session cookies required to keep you logged in. We do not use advertising or
              tracking cookies.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold mb-3">9. Security</h2>
            <p className="text-muted-foreground leading-relaxed">
              All data is transmitted over HTTPS. We store passwords in hashed form and never in plain text. Our
              infrastructure is access-controlled and regularly reviewed for security.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold mb-3">10. Changes to This Policy</h2>
            <p className="text-muted-foreground leading-relaxed">
              We may update this policy from time to time. If we make significant changes we will notify you by email
              or with a prominent notice on the site. Continued use of the service after changes constitutes acceptance.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold mb-3">11. Contact Us</h2>
            <p className="text-muted-foreground leading-relaxed">
              If you have any questions about this Privacy Policy please contact us at{' '}
              <a href="mailto:info.pandorapages@gmail.com" className="text-[#6B21A8] underline">
                info.pandorapages@gmail.com
              </a>
              .
            </p>
          </section>

        </div>

        <div className="mt-12 pt-6 border-t">
          <Link href="/" className="text-sm text-[#6B21A8] hover:underline">
            ← Back to Home
          </Link>
        </div>
      </main>
      <Footer />
    </div>
  );
}
